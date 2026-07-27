$env:PYTHONPATH = ".."
uv run uvicorn backend.api.main:app --reload
