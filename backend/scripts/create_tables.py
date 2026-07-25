"""
Run once to create the attractions table in your Neon database.

Usage:
    python create_tables.py
"""
from backend.database.connection import engine, Base
from backend.models import attraction  # noqa: F401 -- import so Base knows about the model

if __name__ == "__main__":
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Done. 'attractions' table is ready in Neon.")
