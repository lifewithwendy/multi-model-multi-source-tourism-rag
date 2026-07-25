import sys
import os

# Add the project root to sys.path so we can import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.database.connection import SessionLocal
from backend.models.attraction import Attraction
from backend.vector_db.embeddings import get_embedding_model
from backend.vector_db.chroma_client import get_text_collection

def main():
    print("Initializing embedding model...")
    embedder = get_embedding_model()
    
    print("Connecting to ChromaDB...")
    collection = get_text_collection()
    
    print("Fetching attractions from Postgres...")
    db = SessionLocal()
    try:
        attractions = db.query(Attraction).all()
        
        if not attractions:
            print("No attractions found in the database. Run seed_db.py first.")
            return
            
        print(f"Found {len(attractions)} attractions. Embedding descriptions...")
        
        ids = []
        documents = []
        metadatas = []
        
        for attr in attractions:
            if attr.description:
                ids.append(attr.id)
                # We prepend the name for richer context
                text = f"{attr.name}\n{attr.description}"
                documents.append(text)
                metadatas.append({
                    "name": attr.name,
                    "category": attr.category
                })
        
        print(f"Computed texts for {len(documents)} attractions. Generating embeddings...")
        embeddings = embedder.embed_text(documents)
        
        print("Upserting into ChromaDB text_kb...")
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"Successfully ingested {len(ids)} text documents into ChromaDB.")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
