import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_query(query, file_path=None):
    url = f"{BASE_URL}/query/hybrid"
    print("\n" + "="*60)
    print(f"QUERY: \"{query}\"")
    if file_path:
        print(f"WITH IMAGE FILE: {file_path}")
    print("="*60)
    
    data = {"query": query} if query else {}
    files = {}
    
    if file_path:
        files = {"file": open(file_path, "rb")}
        
    try:
        response = requests.post(url, data=data, files=files if files else None)
        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text}")
            return
            
        res_json = response.json()
        
        # Print decision
        decision = res_json.get("sources_used", {})
        print("CLASSIFICATION DECISION:")
        print(f"  - Structured: {decision.get('structured')}")
        print(f"  - Semantic:   {decision.get('semantic')}")
        print(f"  - Image:      {decision.get('image')}")
        print(f"  - Reason:     {decision.get('reason')}")
        print()
        
        # Print results summary
        raw_res = res_json.get("raw_results", {})
        struct_count = len(raw_res.get("structured", []))
        semantic_count = len(raw_res.get("semantic", []))
        
        img_data = raw_res.get("image")
        if img_data:
            img_count = len(img_data.get("attractions", []))
        else:
            img_count = 0
            
        print("RETRIEVAL COUNTS:")
        print(f"  - Structured: {struct_count} attractions")
        print(f"  - Semantic:   {semantic_count} attractions")
        print(f"  - Image:      {img_count} attractions")
        print()
        
        # Print answer
        print("GENERATED ANSWER:")
        print(res_json.get("answer"))
        print()
        
    except Exception as e:
        print(f"Request failed: {e}")
    finally:
        if files:
            files["file"].close()

if __name__ == "__main__":
    # Test cases
    
    # 1. Semantic + Structured
    # Matches category 'waterfall', district 'Kandy', and does semantic search for swimming.
    test_query("What are the entry fees for waterfalls in Kandy?")
    
    # 2. All Three (Structured + Semantic + Image keyword)
    # Matches category 'beach', district 'Galle', visual keyword 'photo/visual', semantic 'safe for swimming'
    test_query("Show me photos of beaches in Galle that are safe for swimming.")
    
    # 3. Semantic Only
    # No category, district, trekking, or price filter keyword; no visual/photo keywords.
    test_query("Where is a good place to see turtles and enjoy a quiet sunset?")
