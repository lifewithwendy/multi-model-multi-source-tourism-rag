# start.ps1
# Sri Lanka Tourism RAG: Start both Backend and Frontend in separate windows

Write-Host "Launching Backend server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; `$env:PYTHONPATH='..'; uv run uvicorn backend.api.main:app --host 127.0.0.1 --port 8000 --reload"

Write-Host "Launching Frontend dev server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "Both servers have been launched in separate console windows." -ForegroundColor Green
