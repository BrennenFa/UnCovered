from langchain_qdrant import QdrantVectorStore
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
import os
from dotenv import load_dotenv

load_dotenv()


def chroma_connect(
    collection_name: str = "epstein_docs",
    remote: bool = False,
):
    """
    Get Qdrant vector store with HuggingFace embeddings.
    By default connects to a local persistent Qdrant. Pass remote=True
    to connect to the EC2 Qdrant server via QDRANT_URL.

    Args:
        collection_name: Name of the collection
        remote: If True, connect to remote Qdrant on EC2

    Returns:
        QdrantVectorStore instance
    """
    if remote:
        qdrant_url = os.getenv("QDRANT_URL")
        if not qdrant_url:
            raise ValueError("QDRANT_URL not found in environment variables")

        client = QdrantClient(url=qdrant_url)
        print(f"Connecting to remote Qdrant at {qdrant_url}, collection: {collection_name}")
    else:
        persist_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "qdrant_db")
        persist_dir = os.path.abspath(persist_dir)
        os.makedirs(persist_dir, exist_ok=True)
        client = QdrantClient(path=persist_dir)
        print(f"Using local Qdrant at {persist_dir}, collection: {collection_name}")

    model = "BAAI/bge-base-en-v1.5"
    embeddings = HuggingFaceEmbeddings(
            model_name=model,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True, 'batch_size': 32}
    )

    # Create collection if it doesn't exist
    from qdrant_client.models import Distance, VectorParams
    try:
        client.get_collection(collection_name=collection_name)
        count = client.count(collection_name=collection_name).count
        print(f"Vector store ready. Documents: {count}")
    except ValueError:
        # Collection doesn't exist, create it
        # BAAI/bge-base-en-v1.5 produces 768-dimensional vectors
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE),
        )
        print(f"Vector store ready. New collection: {collection_name}")

    database = QdrantVectorStore(
        client=client,
        collection_name=collection_name,
        embedding=embeddings,
    )

    return database


# if __name__ == "__main__":
#     vector_store = chroma_connect(persist_directory="./test_chroma_db")

#     test_docs = [
#         Document(
#             page_content="Sample document 1 about flight logs",
#             metadata={"document_id": "TEST-001", "source": "DOJ"}
#         ),
#         Document(
#             page_content="Sample document 2 about depositions",
#             metadata={"document_id": "TEST-002", "source": "HC"}
#         )
#     ]

#     vector_store.add_documents(test_docs)
#     print(f"\nAdded {len(test_docs)} documents")

#     results = vector_store.similarity_search("flight logs", k=2)
#     print(f"\nQuery results: {len(results)} documents")
#     for doc in results:
#         print(f"  - {doc.page_content[:50]}... | {doc.metadata}")
