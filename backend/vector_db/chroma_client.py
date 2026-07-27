import os
import chromadb
from dotenv import load_dotenv

load_dotenv()

_env_path = os.getenv("CHROMA_PERSIST_DIR", "./chroma_data")
if not os.path.isabs(_env_path):
    # Resolve relative paths against the backend directory, not the current working directory
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    CHROMA_PERSIST_DIR = os.path.normpath(os.path.join(backend_dir, _env_path))
else:
    CHROMA_PERSIST_DIR = _env_path

from chromadb.config import Settings

# Initialize Chroma persistent client
client = chromadb.PersistentClient(
    path=CHROMA_PERSIST_DIR,
    settings=Settings(anonymized_telemetry=False)
)

def get_text_collection():
    """
    Returns the Chroma collection for text embeddings (descriptions).
    Creates it if it doesn't exist.
    """
    provider = os.getenv("EMBEDDING_PROVIDER", "local").lower()
    return client.get_or_create_collection(
        name=f"text_kb_{provider}",
        metadata={"hnsw:space": "cosine"} # Use cosine similarity
    )

def get_image_collection():
    """
    Returns the Chroma collection for image embeddings (CLIP).
    Creates it if it doesn't exist.
    """
    provider = os.getenv("EMBEDDING_PROVIDER", "local").lower()
    return client.get_or_create_collection(
        name=f"image_kb_{provider}",
        metadata={"hnsw:space": "cosine"} # Use cosine similarity
    )
