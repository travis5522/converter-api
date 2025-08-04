Write-Host "Enhanced PDF Converter API Server" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green
Write-Host ""

# Change to converter-api directory
Set-Location $PSScriptRoot

# Check if virtual environment exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating Python virtual environment..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
} else {
    Write-Host "Virtual environment not found, using system Python..." -ForegroundColor Yellow
}

# Try to start the server
Write-Host "Starting API server..." -ForegroundColor Cyan

try {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        python app.py
    } elseif (Get-Command py -ErrorAction SilentlyContinue) {
        py app.py
    } else {
        Write-Host "Python not found. Please install Python or add it to PATH." -ForegroundColor Red
        Write-Host "You can download Python from: https://www.python.org/downloads/" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Error starting server: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host ""
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 