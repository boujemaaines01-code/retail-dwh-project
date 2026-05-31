# Stop DEV MySQL Cluster (PowerShell)

Write-Host "Stopping DEV MySQL Cluster..." -ForegroundColor Yellow
Set-Location dev

docker compose down

Write-Host "DEV Cluster stopped." -ForegroundColor Green
Write-Host "To remove volumes (WARNING: deletes all data):"
Write-Host "docker compose down -v"
