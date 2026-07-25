"""
SQLAlchemy models -- structured data schema.

This is the relational side of the RAG system: the fields here are what
get queried directly for "structured queries" (e.g. "waterfalls under 50m",
"beaches with kitesurfing", "free entry mountains").

The `id` here is the same id used as the Chroma document id, so retrieval
results can be joined back to full structured rows.
"""
from sqlalchemy import Column, Integer, String, Float, Text
from backend.database.connection import Base


class Attraction(Base):
    __tablename__ = "attractions"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # waterfall | mountain | beach
    district = Column(String(100))
    province = Column(String(100))
    latitude = Column(Float)
    longitude = Column(Float)
    height_m = Column(Float, nullable=True)                 # waterfalls/mountains only
    trekking_difficulty = Column(String(100), nullable=True)
    entrance_fee_lkr = Column(Float, default=0)
    accessibility = Column(Text)
    best_season = Column(String(100))
    description = Column(Text)          # also embedded into Chroma's text_kb collection
    image_filenames = Column(Text)       # pipe-separated, e.g. "diyaluma_1.jpg|diyaluma_2.jpg"
    source_url = Column(Text)
    image_source_attribution = Column(Text)

    def image_list(self):
        """Helper: split image_filenames into a list."""
        return self.image_filenames.split("|") if self.image_filenames else []

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "district": self.district,
            "province": self.province,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "height_m": self.height_m,
            "trekking_difficulty": self.trekking_difficulty,
            "entrance_fee_lkr": self.entrance_fee_lkr,
            "accessibility": self.accessibility,
            "best_season": self.best_season,
            "description": self.description,
            "images": self.image_list(),
            "source_url": self.source_url,
        }
