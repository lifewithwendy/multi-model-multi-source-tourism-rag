from fastapi import APIRouter, Depends, Query, File, UploadFile, Form, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from backend.database.connection import get_db
from backend.api.dependencies import get_embedder
from backend.api.services.query_service import QueryService
from backend.api.schemas.query import QueryResponse, HybridQueryResponse

router = APIRouter()

@router.get("/structured", response_model=QueryResponse)
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
    try:
        return QueryService.query_structured(
            db=db,
            category=category,
            district=district,
            max_fee=max_fee,
            difficulty=difficulty,
            generate_answer=generate_answer,
            question=question
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/semantic", response_model=QueryResponse)
def query_semantic(
    query: str,
    top_k: int = 3,
    generate_answer: bool = False,
    db: Session = Depends(get_db),
    embedder = Depends(get_embedder)
):
    """
    Semantic search over attraction text descriptions.
    """
    try:
        return QueryService.query_semantic(
            db=db,
            query=query,
            top_k=top_k,
            generate_answer=generate_answer,
            embedder=embedder
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/image", response_model=QueryResponse)
def query_image(
    file: Optional[UploadFile] = File(None, description="Image file to search for visually similar attractions"),
    text_query: Optional[str] = Form(None, description="Text describing the visual features you want"),
    top_k: int = Form(3, description="Number of results to retrieve"),
    generate_answer: bool = Form(False, description="Generate LLM RAG answer if true"),
    question: Optional[str] = Form(None, description="Question for the LLM based on the visual matches"),
    db: Session = Depends(get_db),
    embedder = Depends(get_embedder)
):
    """
    Search the image vector collection using either an uploaded image OR a descriptive text string.
    """
    try:
        return QueryService.query_image(
            db=db,
            file=file,
            text_query=text_query,
            top_k=top_k,
            generate_answer=generate_answer,
            question=question,
            embedder=embedder
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hybrid", response_model=HybridQueryResponse)
async def query_hybrid(
    query: Optional[str] = Form(None, description="Natural language query string"),
    file: Optional[UploadFile] = File(None, description="Optional uploaded image file"),
    top_k: int = Form(3, description="Number of results to retrieve per active vector search"),
    category: Optional[str] = Form(None, description="Explicit category filter"),
    district: Optional[str] = Form(None, description="Explicit district filter"),
    max_fee: Optional[float] = Form(None, description="Explicit maximum entry fee filter"),
    difficulty: Optional[str] = Form(None, description="Explicit difficulty filter"),
    db: Session = Depends(get_db),
    embedder = Depends(get_embedder)
):
    """
    Hybrid query endpoint. Classifies the query, performs the required retrievals,
    merges contexts, and generates a unified RAG response.
    """
    try:
        return QueryService.query_hybrid(
            db=db,
            query=query,
            file=file,
            top_k=top_k,
            category=category,
            district=district,
            max_fee=max_fee,
            difficulty=difficulty,
            embedder=embedder
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
