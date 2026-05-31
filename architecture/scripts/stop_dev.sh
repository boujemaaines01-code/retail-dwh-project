#!/bin/bash
# Stop DEV MySQL Cluster

echo "Stopping DEV MySQL Cluster..."
cd dev

docker compose down

echo "DEV Cluster stopped."
echo "To remove volumes (WARNING: deletes all data):"
echo "docker compose down -v"
