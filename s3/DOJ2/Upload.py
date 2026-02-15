import os
import time
import glob
import boto3
import threading
import signal
import atexit
import psutil
from queue import Queue
from urllib.parse import urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv

# config variables
NUM_WORKERS = 1
DATASETS = [9, 10, 11, 12]
BASE_URL = "https://www.justice.gov/epstein/doj-disclosures/data-set-{}-files?page={}"
VALID_EXTS = (".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".doc", ".docx", ".xls", ".xlsx", ".zip")
CHECKPOINT_FILE = "doj2_checkpoint.txt"
DOWNLOAD_BASE = os.path.abspath("doj_downloads")

load_dotenv()
BUCKET = os.getenv("AWS_BUCKET_NAME")
REGION = os.getenv("AWS_REGION")

s3 = boto3.client("s3", region_name=REGION)

os.makedirs(DOWNLOAD_BASE, exist_ok=True)

# Thread-safe stats
stats_lock = threading.Lock()
stats = {"uploaded": 0, "skipped": 0, "html": 0, "failed": 0}

# Process cleanup tracking (save RAM)
_cleanup_done = False
_cleanup_lock = threading.Lock()

def kill_chrome_processes():
    """Force kill any lingering Chrome processes"""
    try:
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if 'chrome' in proc.name().lower():
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception:
        pass

def cleanup_all():
    """Comprehensive cleanup on exit"""
    global _cleanup_done
    with _cleanup_lock:
        if _cleanup_done:
            return
        _cleanup_done = True

    print("\n[CLEANUP] Starting resource cleanup...")
    try:
        # Close upload queue
        try:
            while not upload_queue.empty():
                upload_queue.get_nowait()
        except:
            pass

        # Close task queue
        try:
            while not task_queue.empty():
                task_queue.get_nowait()
        except:
            pass

        # Kill Chrome processes
        kill_chrome_processes()

        # Clean temp directories
        import shutil
        if os.path.exists(DOWNLOAD_BASE):
            try:
                shutil.rmtree(DOWNLOAD_BASE)
            except:
                pass

        print("[CLEANUP] Done")
    except Exception as e:
        print(f"[CLEANUP] Error: {e}")

def handle_interrupt(signum, frame):
    """Handle Ctrl+C gracefully"""
    print("\n[INTERRUPT] Received interrupt signal, cleaning up...")
    cleanup_all()
    exit(0)

# Register cleanup handlers
signal.signal(signal.SIGINT, handle_interrupt)
signal.signal(signal.SIGTERM, handle_interrupt)
atexit.register(cleanup_all)




checkpoint_lock = threading.Lock()

def load_checkpoint():
    """Load completed dataset:page entries from checkpoint file."""
    if not os.path.exists(CHECKPOINT_FILE):
        return set()
    with open(CHECKPOINT_FILE, 'r') as f:
        return set(line.strip() for line in f if line.strip())

def save_to_checkpoint(dataset, page):
    """Append completed dataset:page entry to checkpoint file."""
    with checkpoint_lock:
        with open(CHECKPOINT_FILE, 'a') as f:
            f.write(f"{dataset}:{page}\n")

# ---------------- HELPERS ----------------
def s3_key_for(dataset, file_url):
    """Generate S3 object key from dataset number and file URL."""
    filename = os.path.basename(urlparse(file_url).path)
    return f"epstein_files/DataSet_{dataset}/{filename}"

def is_valid_file(filepath):
    """Check if downloaded file is valid (not HTML/age-verification page)."""
    with open(filepath, "rb") as f:
        head = f.read(500).lstrip()
    if head.startswith(b"<!DOCTYPE") or head.startswith(b"<html") or b"age-verify" in head:
        return False
    return True

# ---------------- S3 uploaders ----------------
upload_queue = Queue()

def upload_worker():
    """Background thread that handles all S3 uploads."""
    while True:
        item = upload_queue.get()
        if item is None:
            break
        file_path, s3_key, tag, filename = item
        try:
            # Stream file directly to S3 without loading entire file into memory
            with open(file_path, "rb") as f:
                s3.put_object(Bucket=BUCKET, Key=s3_key, Body=f)
            with stats_lock:
                stats["uploaded"] += 1
                if stats["uploaded"] % 10 == 0:
                    print(f"[S3] {stats['uploaded']} uploaded, "
                          f"{stats['skipped']} skipped, {stats['failed']} failed")
            print(f"{tag} Uploaded: {filename}")
        except Exception as e:
            print(f"{tag} S3 error for {filename}: {e}")
            with stats_lock:
                stats["failed"] += 1
        finally:
            # Clean up file immediately
            try:
                os.remove(file_path)
            except:
                pass
            upload_queue.task_done()

upload_threads = [threading.Thread(target=upload_worker, daemon=True) for _ in range(4)]
for t in upload_threads:
    t.start()

# Selenium Methods
def create_driver(download_dir, driver_path):
    os.makedirs(download_dir, exist_ok=True)
    opts = Options()
    opts.add_argument("--start-maximized") # Fixed typo
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
    }
    opts.add_experimental_option("prefs", prefs)
   
    # Use the pre-installed driver path here
    return webdriver.Chrome(
        service=Service(executable_path=driver_path),
        options=opts,
    )
def wait_for_page_load(drv, timeout=10):
    """Wait until the page is fully loaded (document.readyState == 'complete')."""
    WebDriverWait(drv, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )

def pass_robot_check(drv):
    """Attempt to click 'I am not a robot' button if present."""
    try:
        btn = drv.find_element(By.XPATH, "//input[@value='I am not a robot']")
        drv.execute_script("arguments[0].click();", btn)
        # Wait for page to reload after clicking
        WebDriverWait(drv, 10).until(
            lambda d: "Homepage" not in d.title
        )
        return True
    except:
        return False

def pass_age_verify(drv):
    """Click age verification 'Yes' button if present on page."""
    try:
        yes_btn = WebDriverWait(drv, 2).until(
            EC.element_to_be_clickable((By.ID, "age-button-yes"))
        )
        yes_btn.click()
        return True
    except:
        return False

def init_worker_session(drv):
    """Pass robot check + age-verify to set cookies for this browser."""
    drv.get(BASE_URL.format(9, 0))
    wait_for_page_load(drv)
    pass_robot_check(drv)

    links = drv.find_elements(By.TAG_NAME, "a")
    for link in links:
        href = link.get_attribute("href")
        if href and href.lower().endswith(VALID_EXTS):
            drv.get(href)
            wait_for_page_load(drv)
            pass_age_verify(drv)
            return

def clear_dir(d):
    """Delete all files in a directory (cleanup before download)."""
    for f in glob.glob(os.path.join(d, "*")):
        try:
            os.remove(f)
        except:
            pass

def wait_for_download(download_dir, timeout=30):
    """Wait for file to complete downloading; return path or None if timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        crdownloads = glob.glob(os.path.join(download_dir, "*.crdownload"))
        files = [f for f in glob.glob(os.path.join(download_dir, "*"))
                 if not f.endswith(".crdownload")]
        if files and not crdownloads:
            return files[0]
        time.sleep(0.2)
    return None

# ---------------- DOWNLOAD WORKER ----------------
def download_worker(worker_id, task_queue, driver_path):
    download_dir = os.path.join(DOWNLOAD_BASE, f"worker_{worker_id}")
    drv = create_driver(download_dir, driver_path)
    tag = f"[W{worker_id}]"

    try:
        print(f"{tag} Initializing session...")
        init_worker_session(drv)
        clear_dir(download_dir)
        print(f"{tag} Ready")

        while True:
            item = task_queue.get()
            if item is None:
                break

            dataset, file_url = item
            s3_key = s3_key_for(dataset, file_url)
            filename = os.path.basename(urlparse(file_url).path)

            clear_dir(download_dir)
            drv.get(file_url)

            # Either age-verify page loads (click Yes) or PDF auto-downloads
            pass_age_verify(drv)

            downloaded = wait_for_download(download_dir, timeout=30)

            if downloaded:
                if is_valid_file(downloaded):
                    try:
                        upload_queue.put((downloaded, s3_key, tag, filename))
                    except Exception as e:
                        print(f"{tag} Error queueing file: {e}")
                        with stats_lock:
                            stats["failed"] += 1
                        try:
                            os.remove(downloaded)
                        except:
                            pass
                else:
                    with stats_lock:
                        stats["html"] += 1
                    print(f"{tag} SKIPPED (HTML): {filename}")
                    try:
                        os.remove(downloaded)
                    except:
                        pass
            else:
                with stats_lock:
                    stats["failed"] += 1
                print(f"{tag} TIMEOUT: {filename}")

            task_queue.task_done()
    finally:
        drv.quit()
        print(f"{tag} Shut down")

# ---------------- MAIN ----------------
print(f"Starting {NUM_WORKERS} download workers...")
task_queue = Queue()

stable_path = ChromeDriverManager().install()

threads = []
for i in range(NUM_WORKERS):
    t = threading.Thread(target=download_worker, args=(i, task_queue, stable_path), daemon=True)
    t.start()
    threads.append(t)

# Crawler browser for listing pages
crawler_dir = os.path.join(DOWNLOAD_BASE, "crawler")
os.makedirs(crawler_dir, exist_ok=True)
time.sleep(2)
crawler = create_driver(crawler_dir, stable_path)


print("\nCrawler: passing robot check...")
crawler.get(BASE_URL.format(9, 0))
wait_for_page_load(crawler)
pass_robot_check(crawler)
print("Crawler ready.\n")

checkpoint_set = load_checkpoint()
print(f"Loaded {len(checkpoint_set)} completed pages from checkpoint")

for dataset in DATASETS:
    print(f"\n===== DATASET {dataset} =====")
    page = 0

    while True:
        page_key = f"{dataset}:{page}"
        if page_key in checkpoint_set:
            page += 1
            continue

        url = BASE_URL.format(dataset, page)
        print(f"Page {page}: {url}")
        crawler.get(url)
        wait_for_page_load(crawler)
        pass_robot_check(crawler)

        links = crawler.find_elements(By.TAG_NAME, "a")
        file_links = []
        for link in links:
            href = link.get_attribute("href")
            if href and href.lower().endswith(VALID_EXTS):
                file_links.append(href)
        del links

        if not file_links:
            print(f"  No files on page {page}. Dataset {dataset} complete.")
            break

        unique_links = list(set(file_links))
        print(f"  Queued {len(unique_links)} files")

        for file_url in unique_links:
            task_queue.put((dataset, file_url))

        task_queue.join()

        print(f"  Page {page} done: {stats['uploaded']} total uploaded, "
              f"{stats['skipped']} skipped, {stats['html']} HTML, {stats['failed']} failed")

        save_to_checkpoint(dataset, page)
        checkpoint_set.add(page_key)

        page += 1

# Shut down workers
try:
    for _ in range(NUM_WORKERS):
        task_queue.put(None)
    for t in threads:
        t.join(timeout=5)
except Exception as e:
    print(f"Error shutting down workers: {e}")

# Drain upload queue
try:
    upload_queue.join()
    for _ in range(4):
        upload_queue.put(None)
    for t in upload_threads:
        t.join(timeout=5)
except Exception as e:
    print(f"Error draining upload queue: {e}")

# Close crawler
try:
    crawler.quit()
except:
    pass

print(f"\nALL DATASETS 9-12 COMPLETE")
print(f"Uploaded: {stats['uploaded']}, Skipped: {stats['skipped']}, "
      f"HTML: {stats['html']}, Failed: {stats['failed']}")

# Final cleanup
cleanup_all()
