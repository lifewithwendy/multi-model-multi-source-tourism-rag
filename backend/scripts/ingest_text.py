import sys
import os

# Add the project root to sys.path so we can import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.database.connection import SessionLocal
from backend.models.attraction import Attraction
from backend.vector_db.embeddings import get_embedding_model
from backend.vector_db.client import get_text_collection

def main():
    print("Initializing embedding model...")
    embedder = get_embedding_model()
    
    print("Connecting to VectorDB...")
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
                # We prepend all available metadata for richer semantic context
                text_parts = [
                    f"Attraction Name: {attr.name}",
                    f"Category: {attr.category}",
                    f"Location: {attr.district}, {attr.province} Province, Sri Lanka"
                ]
                
                if attr.best_season:
                    text_parts.append(f"Best Season to Visit: {attr.best_season}")
                if attr.trekking_difficulty:
                    text_parts.append(f"Trekking Difficulty: {attr.trekking_difficulty}")
                if attr.accessibility:
                    text_parts.append(f"Accessibility: {attr.accessibility}")
                if attr.entrance_fee_lkr is not None:
                    text_parts.append(f"Entrance Fee: {attr.entrance_fee_lkr} LKR")
                
                text_parts.append(f"Description: {attr.description}")
                text_parts.append(f"Keywords: tourism, travel, Sri Lanka, {attr.category}, {attr.district}")
                
                text = "\n".join(text_parts)
                documents.append(text)
                base_meta = {
                    "name": attr.name,
                    "category": attr.category
                }
                
                # Add filterable fields (ChromaDB does not accept None values in metadata)
                if attr.district: base_meta["district"] = attr.district
                if attr.province: base_meta["province"] = attr.province
                if attr.height_m is not None: base_meta["height_m"] = float(attr.height_m)
                if attr.trekking_difficulty: base_meta["trekking_difficulty"] = attr.trekking_difficulty
                if attr.entrance_fee_lkr is not None: base_meta["entrance_fee_lkr"] = float(attr.entrance_fee_lkr)
                if attr.best_season: base_meta["best_season"] = attr.best_season
                
                metadatas.append(base_meta)
        
        print(f"Computed texts for {len(documents)} attractions. Generating embeddings...")
        embeddings = embedder.embed_text(documents)
        
        print(f"Upserting into VectorDB {collection.name}...")
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        print(f"Successfully ingested {len(ids)} text documents into VectorDB.")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
