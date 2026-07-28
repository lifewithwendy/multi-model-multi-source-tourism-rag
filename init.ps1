# init.ps1
# Sri Lanka Tourism RAG: Initialization Script

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "Sri Lanka Tourism RAG Initialization Script" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host ""

# Check Python installation
$pythonCheck = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCheck) {
    Write-Host "[ERROR] Python was not found in your system path. Please install Python and try again." -ForegroundColor Red
    Exit 1
} else {
    Write-Host "[OK] Python is installed." -ForegroundColor Green
}

# Check Node.js / NPM installation
$npmCheck = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npmCheck) {
    Write-Host "[ERROR] Node.js / NPM was not found in your system path. Please install Node.js and try again." -ForegroundColor Red
    Exit 1
} else {
    Write-Host "[OK] Node.js and NPM are installed." -ForegroundColor Green
}

# Check for uv (extremely fast python package installer)
$uvCheck = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvCheck) {
    Write-Host "[INFO] 'uv' was not found. Attempting to install 'uv' via pip for faster installation..." -ForegroundColor Yellow
    python -m pip install uv
    $uvCheck = Get-Command uv -ErrorAction SilentlyContinue
}

# Initialize Backend
Write-Host ""
Write-Host "---------------------------------------------" -ForegroundColor Cyan
Write-Host "Setting up Backend..." -ForegroundColor Cyan
Write-Host "---------------------------------------------" -ForegroundColor Cyan

if (Test-Path "backend") {
    Push-Location backend
    
    if ($uvCheck) {
        Write-Host "Creating Python virtual environment using uv..." -ForegroundColor Blue
        if (-not (Test-Path ".venv")) {
            uv venv
        }
        Write-Host "Installing Python dependencies using uv..." -ForegroundColor Blue
        uv pip install -r requirements.txt
    } else {
        Write-Host "[WARNING] 'uv' could not be installed. Falling back to standard pip..." -ForegroundColor Yellow
        Write-Host "Creating Python virtual environment..." -ForegroundColor Blue
        if (-not (Test-Path ".venv")) {
            python -m venv .venv
        }
        Write-Host "Activating environment and installing dependencies..." -ForegroundColor Blue
        & .venv\Scripts\activate.ps1
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    }
    
    # Check .env file in backend
    if (-not (Test-Path ".env")) {
        if (Test-Path "../.env") {
            Write-Host "Copying .env from root directory to backend/.env..." -ForegroundColor Yellow
            Copy-Item "../.env" ".env"
        } else {
            Write-Host "[WARNING] No .env file found in backend or root folder." -ForegroundColor Yellow
        }
    }
    
    Pop-Location
} else {
    Write-Host "[ERROR] 'backend' directory not found!" -ForegroundColor Red
    Exit 1
}

# Initialize Frontend
Write-Host ""
Write-Host "---------------------------------------------" -ForegroundColor Cyan
Write-Host "Setting up Frontend..." -ForegroundColor Cyan
Write-Host "---------------------------------------------" -ForegroundColor Cyan

if (Test-Path "frontend") {
    Push-Location frontend
    Write-Host "Installing frontend dependencies using npm..." -ForegroundColor Blue
    npm install
    Pop-Location
} else {
    Write-Host "[ERROR] 'frontend' directory not found!" -ForegroundColor Red
    Exit 1
}

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host "Initialization completed successfully!" -ForegroundColor Green
Write-Host "You can now run '.\start.ps1' to start the application." -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
