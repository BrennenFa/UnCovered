"""
Migrate local Qdrant data to remote Qdrant server (no re-embedding).
Resumes from where it left off if interrupted.

Usage:
    python migrate_to_remote.py http://<IP>:6333
"""

import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

COLLECTION_NAME = "epstein_docs"
VECTOR_DIM = 768
BATCH_SIZE = 50
MAX_WORKERS = 8


def upload_batch(remote, points):
    for attempt in range(5):
        try:
            remote.upsert(COLLECTION_NAME, points=points)
            return len(points)
        except Exception as e:
            wait = 3 * (attempt + 1)
            print(f"  Retry {attempt + 1}/5 in {wait}s... ({type(e).__name__})")
            time.sleep(wait)
    raise RuntimeError("Batch failed after 5 retries")


def migrate(remote_url):
    local_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "qdrant_db"))
    local = QdrantClient(path=local_path)
    local_count = local.count(collection_name=COLLECTION_NAME).count
    print(f"Local: {local_count} points")

    remote = QdrantClient(url=remote_url, prefer_grpc=False, timeout=120)

    try:
        remote_count = remote.count(COLLECTION_NAME).count
        print(f"Remote has {remote_count} points, resuming...")
    except Exception:
        remote.create_collection(COLLECTION_NAME, vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE))
        remote_count = 0

    # Build set of IDs already on remote so we can skip them
    remote_ids = set()
    if remote_count > 0:
        print("Collecting remote IDs to skip...")
        r_offset = None
        while True:
            r_results, r_offset = remote.scroll(COLLECTION_NAME, limit=500, offset=r_offset, with_payload=False, with_vectors=False)
            for r in r_results:
                remote_ids.add(r.id)
            if r_offset is None:
                break
        print(f"Skipping {len(remote_ids)} points already on remote")

    total = 0
    skipped = 0
    offset = None
    pending = []

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        while True:
            # Scroll a batch from local
            results, offset = local.scroll(COLLECTION_NAME, limit=BATCH_SIZE, offset=offset, with_payload=True, with_vectors=True)
            if not results:
                break

            # Filter out points already on remote
            new_points = [PointStruct(id=r.id, vector=r.vector, payload=r.payload) for r in results if r.id not in remote_ids]
            skipped += len(results) - len(new_points)

            if not new_points:
                if offset is None:
                    break
                continue

            future = executor.submit(upload_batch, remote, new_points)
            pending.append(future)

            # Drain completed futures to print progress
            done = [f for f in pending if f.done()]
            for f in done:
                try:
                    total += f.result()
                    print(f"Uploaded {total}/{local_count}")
                except RuntimeError as e:
                    print(f"{e}. Run again to resume.")
                    local.close()
                    sys.exit(1)
                pending.remove(f)

            if offset is None:
                break

        # Wait for remaining uploads
        for f in as_completed(pending):
            try:
                total += f.result()
                print(f"Uploaded {total}/{local_count}")
            except RuntimeError as e:
                print(f"{e}. Run again to resume.")
                local.close()
                sys.exit(1)

    print(f"Skipped {skipped} already-uploaded points")
    print(f"Done. Remote: {remote.count(COLLECTION_NAME).count} points")
    local.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python migrate_to_remote.py http://<IP>:6333")
        sys.exit(1)
    migrate(sys.argv[1])
