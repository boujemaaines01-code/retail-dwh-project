# Run ETL Pipeline (PowerShell)

# Activate virtual environment if it exists
if (Test-Path "venv") {
    & .\venv\Scripts\Activate.ps1
}

# Check if dependencies are installed
python -c "import pandas" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r etl/requirements.txt
}

# Parse arguments
$MODE = if ($args[0]) { $args[0] } else { "initial" }
$ROWS = if ($args[1]) { $args[1] } else { 50000 }
$HOST = if ($args[2]) { $args[2] } else { "localhost" }
$PORT = if ($args[3]) { $args[3] } else { 3306 }

Write-Host "Running ETL Pipeline..." -ForegroundColor Green
Write-Host "Mode: $MODE"
Write-Host "Rows: $ROWS"
Write-Host "Host: $HOST:$PORT"

# Run ETL
python -m etl.run_etl --mode $MODE --rows $ROWS --host $HOST --port $PORT

if ($LASTEXITCODE -eq 0) {
    Write-Host "ETL Pipeline completed successfully!" -ForegroundColor Green
} else {
    Write-Host "ETL Pipeline failed!" -ForegroundColor Red
    exit 1
}
