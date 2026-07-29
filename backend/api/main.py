import os
import logging
from fastapi import FastAPI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)
logger = logging.getLogger("backend.api")
logger.info("Initializing Sri Lanka Tourism RAG API...")
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes import health, query

app = FastAPI(title="Sri Lanka Tourism RAG API")

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

# Register routers
app.include_router(health.router)
app.include_router(query.router, prefix="/query", tags=["Query"])
