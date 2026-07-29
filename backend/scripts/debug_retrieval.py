import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.database.connection import SessionLocal
from backend.models.attraction import Attraction
from backend.vector_db.embeddings import get_embedding_model
from backend.vector_db.chroma_client import get_text_collection, get_image_collection
from backend.api.services.retrieval import retrieve_semantic

db = SessionLocal()
embedder = get_embedding_model()

print("Attractions in DB:", db.query(Attraction).count())

text_col = get_text_collection()
print("Chroma text count:", text_col.count())

query = "Show me photos of beaches in Galle that are safe for swimming."
print(f"\nQuerying: {query}")

# Try direct query on text collection
query_embedding = embedder.embed_text([query])[0]
res = text_col.query(query_embeddings=[query_embedding], n_results=3)
print("Chroma results:")
print("IDs:", res["ids"])
print("Distances:", res.get("distances"))
if res["ids"] and res["ids"][0]:
    ids = res["ids"][0]
    db_attrs = db.query(Attraction).filter(Attraction.id.in_(ids)).all()
    print("Database matched attractions by ID:")
    for a in db_attrs:
        print(f" - {a.id}: {a.name} ({a.category})")
else:
    print("No Chroma IDs found.")

db.close()
