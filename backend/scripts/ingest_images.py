import sys
import os
from collections import defaultdict

# Add the project root to sys.path so we can import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.database.connection import SessionLocal
from backend.models.attraction import Attraction
from backend.vector_db.embeddings import get_embedding_model
from backend.vector_db.chroma_client import get_image_collection

def main():
    print("Initializing embedding model...")
    embedder = get_embedding_model()
    
    print("Connecting to ChromaDB...")
    collection = get_image_collection()
    
    print("Fetching attractions from Postgres...")
    db = SessionLocal()
    
    missing_images = defaultdict(list)
    
    try:
        attractions = db.query(Attraction).all()
        
        ids = []
        image_paths = []
        metadatas = []
        
        # Path to data/images/
        base_image_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/images"))
        
        category_to_folder = {
            "waterfall": "waterfalls",
            "mountain": "mountains",
            "beach": "beaches"
        }
        
        for attr in attractions:
            images = attr.image_list()
            folder_name = category_to_folder.get(attr.category, attr.category)
            for idx, img_filename in enumerate(images):
                img_path = os.path.join(base_image_dir, folder_name, img_filename)
                
                if os.path.exists(img_path):
                    doc_id = f"{attr.id}_{idx}"
                    ids.append(doc_id)
                    image_paths.append(img_path)
                    base_meta = {
                        "attraction_id": attr.id,
                        "name": attr.name,
                        "category": attr.category,
                        "image_filename": img_filename
                    }
                    
                    # Add filterable fields (ChromaDB does not accept None values in metadata)
                    if attr.district: base_meta["district"] = attr.district
                    if attr.province: base_meta["province"] = attr.province
                    if attr.height_m is not None: base_meta["height_m"] = float(attr.height_m)
                    if attr.trekking_difficulty: base_meta["trekking_difficulty"] = attr.trekking_difficulty
                    if attr.entrance_fee_lkr is not None: base_meta["entrance_fee_lkr"] = float(attr.entrance_fee_lkr)
                    if attr.best_season: base_meta["best_season"] = attr.best_season
                    
                    metadatas.append(base_meta)
                else:
                    missing_images[attr.category].append(img_filename)
                    
        total_referenced = len(image_paths) + sum(len(l) for l in missing_images.values())
        print(f"Found {len(image_paths)} images on disk out of {total_referenced} total referenced.")
        
        if missing_images:
            print("\n=== MISSING IMAGES CHECKLIST ===")
            for category, filenames in missing_images.items():
                print(f"[{category}]")
                for fn in filenames:
                    print(f"  - {fn}")
            print("================================\n")
            
        if not image_paths:
            print("No images found on disk to ingest. Please download them first!")
            return
            
        print("Generating image embeddings (this might take a while depending on the provider...)")
        embeddings = embedder.embed_images(image_paths)
        
        print(f"Upserting into ChromaDB {collection.name}...")
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            # Chroma allows None for documents if embeddings are provided
        )
        
        print(f"Successfully ingested {len(ids)} image documents into ChromaDB.")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
