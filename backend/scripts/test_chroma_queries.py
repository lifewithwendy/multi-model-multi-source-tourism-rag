import sys
import os

# Add the project root to sys.path so we can import from backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.vector_db.embeddings import get_embedding_model
from backend.vector_db.chroma_client import get_text_collection, get_image_collection

def extract_category(query: str) -> str:
    import os
    import requests
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
        
    prompt = f"""
    You are a travel assistant for Sri Lanka. Extract the attraction category from the following user query.
    Possible categories include: beach, mountain, waterfall, historical, temple, wildlife, city, etc.
    Return ONLY the category word in lowercase. If no category is mentioned or implied, return the exact word "none".
    Query: "{query}"
    """
    
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": "llama-3.1-8b-instant",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0,
                "max_tokens": 10
            }
        )
        if response.ok:
            category = response.json()["choices"][0]["message"]["content"].strip().lower()
            if category == "none" or category == "":
                return None
            return category
    except Exception as e:
        print(f"Error extracting category: {e}")
    return None

def main():
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "beautiful waterfall for swimming and having a cup of tea"
        
    print(f"Query: '{query}'")
    
    extracted_category = extract_category(query)
    where_filter = None
    if extracted_category:
        print(f"Extracted Category (LLM Filter): '{extracted_category}'")
        where_filter = {"category": extracted_category}
    else:
        print("Extracted Category: None (Searching all categories)")
        
    print("Initializing embedding model...")
    embedder = get_embedding_model()
    
    print("Embedding query...")
    query_embedding = embedder.embed_text([query])[0]
    
    print("\n=== TEXT KB RESULTS ===")
    text_col = get_text_collection()
    text_results = text_col.query(
        query_embeddings=[query_embedding],
        n_results=3,
        where=where_filter
    )
    
    if text_results["ids"] and text_results["ids"][0]:
        for i in range(len(text_results["ids"][0])):
            meta = text_results["metadatas"][0][i]
            dist = text_results["distances"][0][i]
            print(f"{i+1}. [{meta['category']}] {meta['name']} (Distance: {dist:.4f})")
    else:
        print("No results found. Did you run ingest_text.py?")
        
    print("\n=== IMAGE KB RESULTS ===")
    img_col = get_image_collection()
    img_results = img_col.query(
        query_embeddings=[query_embedding],
        n_results=3,
        where=where_filter
    )
    
    if img_results["ids"] and img_results["ids"][0]:
        for i in range(len(img_results["ids"][0])):
            meta = img_results["metadatas"][0][i]
            dist = img_results["distances"][0][i]
            print(f"{i+1}. [{meta['category']}] {meta['name']} - {meta['image_filename']} (Distance: {dist:.4f})")
    else:
        print("No results found. Did you run ingest_images.py?")
        
if __name__ == "__main__":
    main()
