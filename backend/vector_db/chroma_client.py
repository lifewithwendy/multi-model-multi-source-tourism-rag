import os
import chromadb
from dotenv import load_dotenv

load_dotenv()

CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")

# Initialize Chroma persistent client
client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

def get_text_collection():
    """
    Returns the Chroma collection for text embeddings (descriptions).
    Creates it if it doesn't exist.
    """
    return client.get_or_create_collection(
        name="text_kb",
        metadata={"hnsw:space": "cosine"} # Use cosine similarity
    )

def get_image_collection():
    """
    Returns the Chroma collection for image embeddings (CLIP).
    Creates it if it doesn't exist.
    """
    return client.get_or_create_collection(
        name="image_kb",
        metadata={"hnsw:space": "cosine"} # Use cosine similarity
    )
