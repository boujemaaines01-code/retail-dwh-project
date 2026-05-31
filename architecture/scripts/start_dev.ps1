# Start DEV MySQL Cluster with health checks (PowerShell)

Write-Host "Starting DEV MySQL Cluster..." -ForegroundColor Green
Set-Location dev

# Start the cluster
docker compose --env-file .env up -d

Write-Host "Waiting for cluster to initialize (this may take 60-90 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check if management node is running
Write-Host "Checking Management Node status..." -ForegroundColor Yellow
docker exec retail-dwh_dev_mgm ndb_mgm -e "show" --ndb-connectstring=localhost:1186

# Check if SQL node is ready
Write-Host "Checking SQL Node status..." -ForegroundColor Yellow
for ($i = 1; $i -le 12; $i++) {
    $result = docker exec retail-dwh_dev_sql mysqladmin ping -h localhost -u root -pdev_root_pass_2024 --silent 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SQL Node is ready!" -ForegroundColor Green
        break
    }
    Write-Host "Waiting for SQL Node... ($i/12)" -ForegroundColor Yellow
    Start-Sleep -Seconds 5
}

# Show final status
Write-Host ""
Write-Host "Cluster Status:" -ForegroundColor Yellow
docker compose ps

Write-Host ""
Write-Host "DEV Cluster started successfully!" -ForegroundColor Green
Write-Host "MySQL: localhost:3306"
Write-Host "Adminer: http://localhost:8080"
Write-Host ""
Write-Host "To connect to MySQL:"
Write-Host "docker exec -it retail-dwh_dev_sql mysql -u dwh_user -pdwh_dev_pass_2024 retail_dwh"
