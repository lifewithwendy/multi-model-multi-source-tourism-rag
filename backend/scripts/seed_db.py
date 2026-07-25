"""
Loads seed_data_full.csv into the Neon Postgres 'attractions' table.

Usage:
    python seed_db.py

Safe to re-run: it wipes and re-inserts every time, so edit the CSV and
re-run whenever your data changes (e.g. after Day 1 image sourcing fills
in more fields).
"""
import csv
from backend.database.connection import SessionLocal, engine, Base
from backend.models.attraction import Attraction

CSV_PATH = "data/seed_data_full.csv"


def parse_float(value):
    """CSV has blank cells for fields like height_m on beaches -- handle that."""
    if value is None or value.strip() == "":
        return None
    try:
        return float(value)
    except ValueError:
        return None


def main():
    Base.metadata.create_all(bind=engine)  # ensure table exists
    db = SessionLocal()

    try:
        # Wipe existing rows so this script is idempotent / re-runnable
        deleted = db.query(Attraction).delete()
        print(f"Cleared {deleted} existing rows.")

        with open(CSV_PATH, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                attraction = Attraction(
                    id=int(row["id"]),
                    name=row["name"],
                    category=row["category"],
                    district=row["district"],
                    province=row["province"],
                    latitude=parse_float(row["latitude"]),
                    longitude=parse_float(row["longitude"]),
                    height_m=parse_float(row["height_m"]),
                    trekking_difficulty=row["trekking_difficulty"] or None,
                    entrance_fee_lkr=parse_float(row["entrance_fee_lkr"]) or 0,
                    accessibility=row["accessibility"],
                    best_season=row["best_season"],
                    description=row["description"],
                    image_filenames=row["image_filenames"],
                    source_url=row["source_url"],
                    image_source_attribution=row["image_source_attribution"],
                )
                db.add(attraction)
                count += 1

        db.commit()
        print(f"Inserted {count} attractions into Neon.")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
