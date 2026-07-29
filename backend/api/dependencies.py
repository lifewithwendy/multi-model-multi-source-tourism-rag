from backend.vector_db.embeddings import get_embedding_model

_embedder = None

def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = get_embedding_model()
    return _embedder
