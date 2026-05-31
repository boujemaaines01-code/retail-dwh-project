#!/bin/bash
# Start DEV MySQL Cluster with health checks

echo "Starting DEV MySQL Cluster..."
cd dev

# Start the cluster
docker compose --env-file .env up -d

echo "Waiting for cluster to initialize (this may take 60-90 seconds)..."
sleep 30

# Check if management node is running
echo "Checking Management Node status..."
docker exec retail-dwh_dev_mgm ndb_mgm -e "show" --ndb-connectstring=localhost:1186

# Check if SQL node is ready
echo "Checking SQL Node status..."
for i in {1..12}; do
    if docker exec retail-dwh_dev_sql mysqladmin ping -h localhost -u root -pdev_root_pass_2024 --silent; then
        echo "SQL Node is ready!"
        break
    fi
    echo "Waiting for SQL Node... ($i/12)"
    sleep 5
done

# Show final status
echo ""
echo "Cluster Status:"
docker compose ps

echo ""
echo "DEV Cluster started successfully!"
echo "MySQL: localhost:3306"
echo "Adminer: http://localhost:8080"
echo ""
echo "To connect to MySQL:"
echo "docker exec -it retail-dwh_dev_sql mysql -u dwh_user -pdwh_dev_pass_2024 retail_dwh"
