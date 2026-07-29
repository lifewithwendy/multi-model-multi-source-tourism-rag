from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def health_check():
    """Simple health-check endpoint to verify the server is running."""
    return {"status": "healthy"}
