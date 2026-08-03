import os
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from backend.models.attraction import Attraction
from backend.vector_db.client import get_text_collection, get_image_collection

logger = logging.getLogger(__name__)


def retrieve_structured(db: Session, filters: Dict[str, Any]) -> List[Attraction]:
    """
    Retrieves attractions matching structural constraints.
    """
    query = db.query(Attraction)
    if filters.get("category"):
        query = query.filter(Attraction.category.ilike(filters["category"]))
    if filters.get("district"):
        query = query.filter(Attraction.district.ilike(filters["district"]))
    if filters.get("max_fee") is not None:
        try:
            val = float(filters["max_fee"])
            query = query.filter(Attraction.entrance_fee_lkr <= val)
        except ValueError:
            pass
    if filters.get("difficulty"):
        query = query.filter(Attraction.trekking_difficulty.ilike(filters["difficulty"]))
    return query.all()

def retrieve_semantic(db: Session, query: str, top_k: int, embedder) -> List[Attraction]:
    """
    Retrieves attractions via semantic text search on descriptions.
    """
    try:
        query_embedding = embedder.embed_text([query])[0]
    except Exception as e:
        raise RuntimeError(f"Embedding error: {str(e)}")
        
    text_col = get_text_collection()
    search_res = text_col.query(query_embeddings=[query_embedding], n_results=top_k)
    
    if not search_res["ids"] or not search_res["ids"][0]:
        return []
        
    ids = search_res["ids"][0]
    results = db.query(Attraction).filter(Attraction.id.in_(ids)).all()
    
    id_to_attr = {str(attr.id): attr for attr in results}
    sorted_results = [id_to_attr[i] for i in ids if i in id_to_attr]
    return sorted_results

def retrieve_image(db: Session, query_embedding: List[float], top_k: int) -> Dict[str, Any]:
    """
    Retrieves attractions visually similar to the query embedding.
    """
    img_col = get_image_collection()
    search_res = img_col.query(query_embeddings=[query_embedding], n_results=top_k)
    
    if not search_res["ids"] or not search_res["ids"][0]:
        return {"attractions": [], "image_ids": [], "distances": []}
        
    image_ids = search_res["ids"][0]
    distances = search_res["distances"][0] if "distances" in search_res else []
    
    logger.info(f"Visual retrieval raw matches and cosine distances: {list(zip(image_ids, distances))}")
    
    # Filter based on visual threshold to ignore irrelevant images
    visual_threshold = float(os.getenv("VISUAL_THRESHOLD", "0.65"))
    filtered_pairs = [
        (img_id, dist) for img_id, dist in zip(image_ids, distances)
        if dist <= visual_threshold
    ]
    
    if not filtered_pairs:
        logger.info(f"Visual retrieval found no matching attractions below the distance threshold of {visual_threshold}.")
        return {"attractions": [], "image_ids": [], "distances": []}
        
    filtered_image_ids = [pair[0] for pair in filtered_pairs]
    filtered_distances = [pair[1] for pair in filtered_pairs]
    
    logger.info(f"Visual retrieval matched attractions after threshold filtering (kept IDs: {filtered_image_ids})")
    
    # Extract unique attraction IDs
    attr_ids = list(set([str(i).split('_')[0] for i in filtered_image_ids]))
    results = db.query(Attraction).filter(Attraction.id.in_(attr_ids)).all()
    
    return {
        "attractions": results,
        "image_ids": filtered_image_ids,
        "distances": filtered_distances
    }


