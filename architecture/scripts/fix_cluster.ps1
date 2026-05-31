# MySQL NDB Cluster Fix Script
# This script fixes the cluster configuration and restarts it

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "MySQL NDB Cluster Fix Script" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Fix .env file
Write-Host "[1/5] Fixing .env file..." -ForegroundColor Yellow
$envPath = "dev\.env"
$envContent = @"
MYSQL_ROOT_PASSWORD=dev_root_pass_2024
MYSQL_USER=dwh_user
MYSQL_PASSWORD=dwh_dev_pass_2024
MYSQL_DATABASE=retail_dwh
"@
Set-Content -Path $envPath -Value $envContent -Force
Write-Host "✓ .env file fixed" -ForegroundColor Green

# Step 2: Stop and remove all containers
Write-Host "[2/5] Stopping and removing containers..." -ForegroundColor Yellow
Set-Location dev
docker compose down -v
Write-Host "✓ Containers stopped and removed" -ForegroundColor Green

# Step 3: Clean Docker system
Write-Host "[3/5] Cleaning Docker system..." -ForegroundColor Yellow
docker system prune -f
Write-Host "✓ Docker system cleaned" -ForegroundColor Green

# Step 4: Start the cluster
Write-Host "[4/5] Starting MySQL Cluster..." -ForegroundColor Yellow
docker compose --env-file .env up -d
Write-Host "✓ Cluster started" -ForegroundColor Green

# Step 5: Wait for cluster to initialize
Write-Host "[5/5] Waiting for cluster to initialize (90 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 90

# Verify cluster status
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Cluster Status Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Container Status:" -ForegroundColor Yellow
docker compose ps

Write-Host ""
Write-Host "Cluster Topology:" -ForegroundColor Yellow
docker exec retail_dwh_mgm ndb_mgm -e "show"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Fix script completed!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
