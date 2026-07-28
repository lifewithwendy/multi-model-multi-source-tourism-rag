from fastapi import FastAPI, Depends, Query, File, UploadFile, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import Optional, List
import os
import tempfile
import shutil

from backend.database.connection import get_db
from backend.models.attraction import Attraction
from backend.vector_db.chroma_client import get_text_collection, get_image_collection
from backend.vector_db.embeddings import get_embedding_model
from backend.llm.groq_client import generate_rag_response
from backend.api.query_classifier import classify_query
from backend.api.retrieval import retrieve_structured, retrieve_semantic, retrieve_image

app = FastAPI(title="Sri Lanka Tourism RAG API")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/images",
    StaticFiles(directory=os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/images"))),
    name="images"
)

# Initialize embedding model lazily to avoid loading it when importing the module (e.g. during tests)
_embedder = None
def get_embedder():
    global _embedder
    if _embedder is None:
        _embedder = get_embedding_model()
    return _embedder

@app.get("/health")
def health_check():
    """Simple health-check endpoint to verify the server is running."""
    return {"status": "healthy"}

def format_context(attractions: List[Attraction]) -> str:
    """Helper to convert structured Postgres data into a text context for the LLM."""
    context_parts = []
    for attr in attractions:
        part = f"- {attr.name} (Category: {attr.category}): Located in {attr.district}, {attr.province} Province."
        if attr.description:
            part += f" Description: {attr.description}"
        if attr.entrance_fee_lkr is not None:
            part += f" Entrance fee: {attr.entrance_fee_lkr} LKR."
        if attr.trekking_difficulty:
            part += f" Trekking Difficulty: {attr.trekking_difficulty}."
        if attr.best_season:
            part += f" Best Season: {attr.best_season}."
        context_parts.append(part)
    return "\n\n".join(context_parts)

@app.get("/query/structured")
def query_structured(
    category: Optional[str] = None,
    district: Optional[str] = None,
    max_fee: Optional[float] = None,
    difficulty: Optional[str] = None,
    generate_answer: bool = False,
    question: Optional[str] = Query(None, description="Natural language question to ask the LLM if generate_answer is true"),
    db: Session = Depends(get_db)
):
    """
    Query the Postgres database directly using structured filters. No vector search involved.
    """
    query = db.query(Attraction)
    if category: 
        query = query.filter(Attraction.category.ilike(category))
    if district: 
        query = query.filter(Attraction.district.ilike(district))
    if max_fee is not None: 
        query = query.filter(Attraction.entrance_fee_lkr <= max_fee)
    if difficulty: 
        query = query.filter(Attraction.trekking_difficulty.ilike(difficulty))
    
    results = query.all()
    
    response = {
        "results": [r.to_dict() for r in results]
    }
    
    if generate_answer:
        if not question:
            raise HTTPException(status_code=400, detail="Must provide a 'question' if generate_answer is true")
        if not results:
            response["answer"] = "No matching attractions found to answer your question."
        else:
            context = format_context(results)
            response["answer"] = generate_rag_response(context, question)
            
    return response

@app.get("/query/semantic")
def query_semantic(
    query: str,
    top_k: int = 3,
    generate_answer: bool = False,
    db: Session = Depends(get_db)
):
    """
    Semantic search over attraction text descriptions.
    """
    embedder = get_embedder()
    try:
        query_embedding = embedder.embed_text([query])[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding error: {str(e)}")
        
    text_col = get_text_collection()
    search_res = text_col.query(query_embeddings=[query_embedding], n_results=top_k)
    
    if not search_res["ids"] or not search_res["ids"][0]:
        return {"results": [], "answer": "No semantic matches found." if generate_answer else None}
        
    ids = search_res["ids"][0]
    results = db.query(Attraction).filter(Attraction.id.in_(ids)).all()
    
    # Sort results to match Chroma's distance order
    id_to_attr = {str(attr.id): attr for attr in results}
    sorted_results = [id_to_attr[i] for i in ids if i in id_to_attr]
    
    response = {
        "results": [r.to_dict() for r in sorted_results]
    }
    
    if generate_answer:
        context = format_context(sorted_results)
        response["answer"] = generate_rag_response(context, query)
        
    return response

@app.post("/query/image")
def query_image(
    file: Optional[UploadFile] = File(None, description="Image file to search for visually similar attractions"),
    text_query: Optional[str] = Form(None, description="Text describing the visual features you want"),
    top_k: int = 3,
    generate_answer: bool = False,
    question: Optional[str] = Form(None, description="Question for the LLM based on the visual matches"),
    db: Session = Depends(get_db)
):
    """
    Search the image vector collection using either an uploaded image OR a descriptive text string.
    """
    if not file and not text_query:
        raise HTTPException(status_code=400, detail="Must provide either an uploaded 'file' or a 'text_query'")
        
    embedder = get_embedder()
    query_embedding = None
    
    if file:
        temp_path = ""
        try:
            fd, temp_path = tempfile.mkstemp(suffix=f"_{file.filename}")
            with os.fdopen(fd, "wb") as f:
                shutil.copyfileobj(file.file, f)
            query_embedding = embedder.embed_images([temp_path])[0]
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to process image: {str(e)}")
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
    else:
        try:
            query_embedding = embedder.embed_text([text_query])[0]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Embedding error: {str(e)}")
            
    img_col = get_image_collection()
    search_res = img_col.query(query_embeddings=[query_embedding], n_results=top_k)
    
    if not search_res["ids"] or not search_res["ids"][0]:
        return {"results": [], "answer": "No visual matches found." if generate_answer else None}
        
    # Extract unique attraction IDs (image ids are stored as {attraction_id}_{idx})
    attr_ids = list(set([str(i).split('_')[0] for i in search_res["ids"][0]]))
    
    results = db.query(Attraction).filter(Attraction.id.in_(attr_ids)).all()
    
    response = {
        "results": [r.to_dict() for r in results]
    }
    
    if generate_answer:
        # Fallback question if none provided
        llm_question = question if question else "Please describe these matching attractions based on the context."
        context = format_context(results)
        response["answer"] = generate_rag_response(context, llm_question)
        
    return response


@app.post("/query/hybrid")
async def query_hybrid(
    query: Optional[str] = Form(None, description="Natural language query string"),
    file: Optional[UploadFile] = File(None, description="Optional uploaded image file"),
    top_k: int = Form(3, description="Number of results to retrieve per active vector search"),
    category: Optional[str] = Form(None, description="Explicit category filter"),
    district: Optional[str] = Form(None, description="Explicit district filter"),
    max_fee: Optional[float] = Form(None, description="Explicit maximum entry fee filter"),
    difficulty: Optional[str] = Form(None, description="Explicit difficulty filter"),
    db: Session = Depends(get_db)
):
    """
    Hybrid query endpoint. Classifies the query, performs the required retrievals,
    merges contexts, and generates a unified RAG response.
    """
    if not query and not file and not category and not district and not max_fee and not difficulty:
        raise HTTPException(status_code=400, detail="Must provide either a 'query' string, an uploaded 'file', or structured filters")
        
    # 1. Classify the query
    decision = classify_query(query or "", has_image_file=(file is not None))
    
    # 1b. Merge explicit frontend filters
    explicit_filters = {}
    if category:
        explicit_filters["category"] = category
    if district:
        explicit_filters["district"] = district
    if max_fee is not None:
        explicit_filters["max_fee"] = max_fee
    if difficulty:
        explicit_filters["difficulty"] = difficulty

    if explicit_filters:
        decision["structured"] = True
        if "structured_filters" not in decision or not isinstance(decision["structured_filters"], dict):
            decision["structured_filters"] = {}
        decision["structured_filters"].update(explicit_filters)
        if decision.get("reason"):
            decision["reason"] += " (With explicit frontend filters applied)"
        else:
            decision["reason"] = "Explicit frontend filters applied."
            
    sources_used = {
        "structured": decision.get("structured", False),
        "semantic": decision.get("semantic", False),
        "image": decision.get("image", False),
        "reason": decision.get("reason", "")
    }
    
    raw_results_objects = {
        "structured": [],
        "semantic": [],
        "image": None
    }
    
    embedder = get_embedder()
    
    # 2. Perform retrievals as decided by classifier
    if sources_used["structured"]:
        filters = decision.get("structured_filters", {})
        raw_results_objects["structured"] = retrieve_structured(db, filters)
        
    if sources_used["semantic"] and query:
        raw_results_objects["semantic"] = retrieve_semantic(db, query, top_k, embedder)
        
    if sources_used["image"]:
        query_embedding = None
        if file:
            temp_path = ""
            try:
                fd, temp_path = tempfile.mkstemp(suffix=f"_{file.filename}")
                with os.fdopen(fd, "wb") as f:
                    shutil.copyfileobj(file.file, f)
                query_embedding = embedder.embed_images([temp_path])[0]
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Failed to process image: {str(e)}")
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
        elif query:
            try:
                query_embedding = embedder.embed_text([query])[0]
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Embedding error: {str(e)}")
                
        if query_embedding is not None:
            raw_results_objects["image"] = retrieve_image(db, query_embedding, top_k)
            
    # 3. Merge contexts and eliminate duplicates
    unique_attractions = {}
    attraction_sources = {}
    for attr in raw_results_objects["structured"]:
        unique_attractions[attr.id] = attr
        attraction_sources.setdefault(attr.id, []).append("structured")
    for attr in raw_results_objects["semantic"]:
        unique_attractions[attr.id] = attr
        attraction_sources.setdefault(attr.id, []).append("semantic")
    if raw_results_objects["image"]:
        for attr in raw_results_objects["image"]["attractions"]:
            unique_attractions[attr.id] = attr
            attraction_sources.setdefault(attr.id, []).append("image")
            
    attractions_list = list(unique_attractions.values())
    
    # 4. Generate answer or return fallback
    if not attractions_list:
        answer = "No matching attractions found to answer your query."
    else:
        context = format_context(attractions_list)
        # Use query if provided, else fall back to a generic prompt
        llm_question = query if query else "Describe the matching attractions visually similar to the uploaded image."
        answer = generate_rag_response(context, llm_question)
        
    # 5. Format response payload
    response = {
        "answer": answer,
        "sources_used": sources_used,
        "attraction_sources": attraction_sources,
        "raw_results": {
            "structured": [r.to_dict() for r in raw_results_objects["structured"]],
            "semantic": [r.to_dict() for r in raw_results_objects["semantic"]],
            "image": {
                "attractions": [r.to_dict() for r in raw_results_objects["image"]["attractions"]],
                "image_ids": raw_results_objects["image"]["image_ids"],
                "distances": raw_results_objects["image"]["distances"]
            } if raw_results_objects["image"] else None
        }
    }
    
    return response
