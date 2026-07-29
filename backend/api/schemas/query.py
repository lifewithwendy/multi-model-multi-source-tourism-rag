from pydantic import BaseModel
from typing import List, Dict, Optional

class AttractionResponse(BaseModel):
    id: str
    name: str
    category: str
    district: Optional[str] = None
    province: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    height_m: Optional[float] = None
    trekking_difficulty: Optional[str] = None
    entrance_fee_lkr: float
    accessibility: Optional[str] = None
    best_season: Optional[str] = None
    description: Optional[str] = None
    images: List[str] = []
    source_url: Optional[str] = None

    class Config:
        from_attributes = True
        # Allow population from database models or dicts directly
        populate_by_name = True

class QueryResponse(BaseModel):
    results: List[AttractionResponse]
    answer: Optional[str] = None

class SourcesUsed(BaseModel):
    structured: bool
    semantic: bool
    image: bool
    reason: str

class ImageRawResults(BaseModel):
    attractions: List[AttractionResponse]
    image_ids: List[str]
    distances: List[float]

class RawResults(BaseModel):
    structured: List[AttractionResponse]
    semantic: List[AttractionResponse]
    image: Optional[ImageRawResults] = None

class HybridQueryResponse(BaseModel):
    answer: str
    sources_used: SourcesUsed
    attraction_sources: Dict[str, List[str]]
    raw_results: RawResults
