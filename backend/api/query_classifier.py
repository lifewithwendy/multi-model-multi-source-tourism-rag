import os
import re
import json
from typing import Dict, Any, Optional
from groq import Groq

# Lists of known entities in Sri Lanka tourism data for rule-based matching
DISTRICTS = [
    "badulla", "nuwara eliya", "ratnapura", "kegalle", "kandy", "matale",
    "matara", "galle", "ampara", "trincomalee", "batticaloa", "hambantota",
    "gampaha", "puttalam"
]

CATEGORIES = ["waterfall", "mountain", "beach"]
DIFFICULTIES = ["easy", "moderate", "strenuous"]

def classify_query_rule_based(query: str) -> Dict[str, Any]:
    """
    Fallback deterministic rule-based query classifier.
    """
    query_lower = query.lower()
    
    # 1. Check for Structured parameters
    structured_filters = {}
    
    # Match category
    for cat in CATEGORIES:
        if cat in query_lower:
            structured_filters["category"] = cat.capitalize() if cat != "beach" else "beach" # DB matches "waterfall", "mountain", "beach"
            break
            
    # Match district
    for dist in DISTRICTS:
        if dist in query_lower:
            # Capitalize properly
            structured_filters["district"] = " ".join([w.capitalize() for w in dist.split()])
            break
            
    # Match difficulty
    for diff in DIFFICULTIES:
        if diff in query_lower:
            structured_filters["difficulty"] = diff.capitalize()
            break
            
    # Match max fee / price / free
    if "free" in query_lower or "no entrance fee" in query_lower or "no fee" in query_lower:
        structured_filters["max_fee"] = 0.0
    else:
        # Look for patterns like "under 500", "below 1000", "less than 2000"
        fee_match = re.search(r'(?:under|below|less than|max|maximum)\s*(?:lkr|rs\.?)?\s*(\d+)', query_lower)
        if fee_match:
            structured_filters["max_fee"] = float(fee_match.group(1))
            
    has_structured = len(structured_filters) > 0 or any(kw in query_lower for kw in ["fee", "price", "cost", "lkr", "rupees", "entrance", "difficulty", "trekking", "hike", "climb"])
    
    # 2. Check for Image keywords
    image_keywords = ["photo", "image", "picture", "visual", "look like", "view", "scenery", "show me", "snap", "camera"]
    has_image = any(kw in query_lower for kw in image_keywords)
    
    # 3. Semantic keyword checking
    # All natural queries are semantic by default unless they are purely structured filters.
    has_semantic = True
    
    # Determine reason
    reasons = []
    if has_structured:
        reasons.append("matches structured fields (category/district/price/difficulty)")
    if has_image:
        reasons.append("contains visual/image keywords")
    if has_semantic:
        reasons.append("contains natural language descriptive query")
        
    reason = "Query " + " and ".join(reasons) + "."
    
    return {
        "structured": bool(has_structured),
        "semantic": has_semantic,
        "image": has_image,
        "structured_filters": structured_filters,
        "reason": reason
    }

def classify_query_llm(query: str) -> Optional[Dict[str, Any]]:
    """
    Classifies query using a fast LLM call (llama-3.1-8b-instant) returning structured JSON.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
        
    try:
        client = Groq(api_key=api_key)
        
        system_prompt = """
You are a fast, accurate query classifier for a Sri Lanka tourism RAG system.
Your job is to classify the user's natural language search query and extract structured filters if present.
You MUST respond with a valid JSON object ONLY. Do not output any prose, markdown blocks, or extra text.

JSON Schema:
{
  "structured": boolean, // true if user query explicitly specifies filters like category, district, max entrance fee, or trekking difficulty
  "semantic": boolean, // true if the query is a descriptive natural language query suitable for semantic vector search
  "image": boolean, // true if the query asks for visual aspects, photos, images, views, or visual similarities (e.g. "what does it look like", "show a photo of...")
  "structured_filters": {
    "category": string or null, // "waterfall", "mountain", or "beach"
    "district": string or null, // e.g. "Kandy", "Galle", "Badulla", "Nuwara Eliya", "Matara", etc.
    "max_fee": number or null, // maximum entrance fee in LKR (e.g. if query says "under 1000 LKR", this is 1000)
    "difficulty": string or null // "Easy", "Moderate", or "Strenuous"
  },
  "reason": string // concise explanation of the classification decision
}
"""
        
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Query: {query}"}
            ],
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=256
        )
        
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            return json.loads(content)
    except Exception as e:
        print(f"LLM Classification failed, falling back to rule-based. Error: {e}")
        
    return None

def classify_query(query: str, has_image_file: bool = False) -> Dict[str, Any]:
    """
    Main query classifier entrypoint. Uses LLM-based classification as primary,
    and falls back to rule-based keyword matching if LLM fails or is unavailable.
    """
    if not query.strip():
        # If query is empty but an image is uploaded
        return {
            "structured": False,
            "semantic": False,
            "image": True,
            "structured_filters": {},
            "reason": "Only an image file was provided." if has_image_file else "Empty query."
        }
        
    # Attempt LLM classification
    decision = classify_query_llm(query)
    
    # Fallback to rule-based if LLM didn't return a valid dict
    if not decision:
        decision = classify_query_rule_based(query)
        
    # If a physical image file was uploaded, we MUST run image search regardless of query text
    if has_image_file:
        decision["image"] = True
        decision["reason"] += " (Forced image search due to uploaded file)"
        
    return decision
