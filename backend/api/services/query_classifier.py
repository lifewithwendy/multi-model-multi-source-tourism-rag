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

from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

class StructuredFiltersSchema(BaseModel):
    category: Optional[str] = Field(default=None, description="Category filter: 'waterfall', 'mountain', or 'beach'")
    district: Optional[str] = Field(default=None, description="District filter: e.g. Kandy, Galle, Badulla, Nuwara Eliya, etc.")
    max_fee: Optional[float] = Field(default=None, description="maximum entrance fee in LKR")
    difficulty: Optional[str] = Field(default=None, description="trekking difficulty: 'Easy', 'Moderate', or 'Strenuous'")

class ClassificationSchema(BaseModel):
    structured: bool = Field(description="true if user query explicitly specifies filters like category, district, max entrance fee, or trekking difficulty")
    semantic: bool = Field(description="true if the query is a descriptive natural language query suitable for semantic vector search")
    image: bool = Field(description="true if the query asks for visual aspects, photos, images, views, or visual similarities")
    structured_filters: Optional[StructuredFiltersSchema] = Field(default=None, description="Structured filters extracted from query")
    reason: str = Field(description="concise explanation of the classification decision")

def classify_query_llm(query: str) -> Optional[Dict[str, Any]]:
    """
    Classifies query using a fast LLM call (llama-3.1-8b-instant) returning structured JSON via LangChain.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
        
    try:
        llm = ChatGroq(api_key=api_key, model="llama-3.1-8b-instant", temperature=0.0)
        structured_llm = llm.with_structured_output(ClassificationSchema)
        
        system_prompt = """
You are a fast, accurate query classifier for a Sri Lanka tourism RAG system.
Your job is to classify the user's natural language search query and extract structured filters if present.
"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("user", "Query: {query}")
        ])
        
        chain = prompt | structured_llm
        result = chain.invoke({"query": query})
        
        # Convert back to the expected dictionary format
        filters_dict = {}
        if result.structured_filters:
            if result.structured_filters.category:
                filters_dict["category"] = result.structured_filters.category
            if result.structured_filters.district:
                filters_dict["district"] = result.structured_filters.district
            if result.structured_filters.max_fee is not None:
                filters_dict["max_fee"] = result.structured_filters.max_fee
            if result.structured_filters.difficulty:
                filters_dict["difficulty"] = result.structured_filters.difficulty
                
        return {
            "structured": result.structured,
            "semantic": result.semantic,
            "image": result.image,
            "structured_filters": filters_dict,
            "reason": result.reason
        }
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
