# Deployment Guide

## Prerequisites

- Docker Engine ≥ 24.0
- Docker Compose ≥ 2.0
- Python ≥ 3.10
- Git
- Minimum 8GB RAM (16GB recommended for production)
- Minimum 20GB disk space

## Environment Setup

### 1. Clone Repository
```bash
git clone https://github.com/your-org/retail-dwh-project.git
cd retail-dwh-project
```

### 2. Environment Configuration

Each environment has its own `.env` file with specific configurations:

#### DEV Environment
```bash
cd dev
# Edit .env if needed (default passwords are for development only)
docker compose --env-file .env up -d
```

#### TEST Environment
```bash
cd test
# Edit .env if needed
docker compose --env-file .env up -d
```

#### PROD Environment
```bash
cd prod
# IMPORTANT: Change all passwords in .env before deployment
docker compose --env-file .env up -d
```

#### DAC Environment
```bash
cd dac
# Edit .env if needed
docker compose --env-file .env up -d
```

## Cluster Startup Process

### 1. Management Node Starts
- Reads configuration from `my.cnf.mgm`
- Listens on port 1186
- Waits for data nodes to connect

### 2. Data Nodes Start
- Connect to management node
- Initialize data partitions
- Establish replication (NoOfReplicas=2)
- Become ready for SQL connections

### 3. SQL Node Starts
- Connects to management node
- Connects to data nodes
- Initializes MySQL server
- Executes initialization scripts from `/docker-entrypoint-initdb.d`

### 4. Health Checks
- Each service has health checks defined
- Services wait for dependencies to be healthy
- Full cluster startup takes ~90 seconds

## Verification Steps

### Check Container Status
```bash
docker compose ps
```

Expected output: All services should show "healthy" status.

### Check Cluster Topology
```bash
docker exec retail-dwh_dev_mgm ndb_mgm -e "show" --ndb-connectstring=localhost:1186
```

Expected output:
```
Connected to Management Server at: localhost:1186
Cluster Configuration
---------------------
[ndbd(NDB)]     2 node(s)
id=2    @10.0.0.2  (mysql-8.0 ndb-8.0)
id=3    @10.0.0.3  (mysql-8.0 ndb-8.0)

[ndb_mgmd(MGM)] 1 node(s)
id=1    @10.0.0.1  (mysql-8.0 ndb-8.0)

[mysqld(API)]   1 node(s)
id=4    @10.0.0.4  (mysql-8.0 ndb-8.0)
```

### Test SQL Connection
```bash
docker exec retail-dwh_dev_sql mysql -u dwh_user -pdwh_dev_pass_2024 -e "SHOW TABLES;" retail_dwh
```

Expected output: List of all dimension and fact tables.

### Verify NDB Engine
```bash
docker exec retail-dwh_dev_sql mysql -u dwh_user -pdwh_dev_pass_2024 -e "SHOW CREATE TABLE fact_sales\G" retail_dwh
```

Expected output: `ENGINE=NDBCLUSTER` in the table definition.

## ETL Pipeline Setup

### Install Python Dependencies
```bash
cd ..
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows
pip install -r etl/requirements.txt
```

### Run Initial Load
```bash
python -m etl.run_etl --mode initial --rows 50000
```

### Run Incremental Load
```bash
python -m etl.run_etl --mode incremental --rows 2000
```

## Service Access

### DEV Environment
- **MySQL**: localhost:3306
- **Adminer**: http://localhost:8080
  - Server: `sql_node`
  - Username: `dwh_user`
  - Password: `dwh_dev_pass_2024`
  - Database: `retail_dwh`

### TEST Environment
- **MySQL**: localhost:3307

### PROD Environment
- **MySQL**: localhost:3306 (bind to localhost only)

### DAC Environment
- **MySQL**: localhost:3308
- **Metabase**: http://localhost:3000
  - Initial setup required on first access

## Monitoring

### View Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f sql
```

### Check Resource Usage
```bash
docker stats
```

### Cluster Status
```bash
docker exec retail-dwh_dev_mgm ndb_mgm -e "status"
```

## Backup & Recovery

### Backup
```bash
# Backup data volumes
docker run --rm -v retail_dwh_dev_dn1_data:/data -v $(pwd)/backups:/backup \
  alpine tar czf /backup/dn1_backup_$(date +%Y%m%d).tar.gz -C /data .

# Repeat for dn2 and sql volumes
```

### Recovery
```bash
# Stop cluster
docker compose down

# Restore volumes
docker run --rm -v retail_dwh_dev_dn1_data:/data -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/dn1_backup_20240101.tar.gz -C /data

# Restart cluster
docker compose up -d
```

## Scaling Considerations

### Vertical Scaling
- Increase DataMemory/IndexMemory in `my.cnf.mgm`
- Increase max_connections in `my.cnf.sql`
- Add more RAM to host machine

### Horizontal Scaling
- Add additional data nodes (modify `my.cnf.mgm`)
- Add additional SQL nodes for read scaling
- Use MySQL Router for connection routing

### Environment-Specific Tuning

| Environment | DataMemory | Max Connections | Use Case |
|---|---|---|---|
| DEV | 512MB | 500 | Development & testing |
| TEST | 256MB | 200 | Integration testing |
| PROD | 2GB | 1000 | Production workload |
| DAC | 1GB | 300 | Analytics & BI |

## Troubleshooting

### Cluster Won't Start
```bash
# Check logs
docker compose logs mgm
docker compose logs dn1
docker compose logs sql

# Reset cluster (WARNING: deletes all data)
docker compose down -v
docker compose up -d
```

### Connection Refused
```bash
# Verify SQL node is healthy
docker compose ps

# Check if port is available
netstat -an | grep 3306

# Verify .env variables
cat .env | grep MYSQL
```

### NDB Tables Not Visible
```sql
-- Verify engine type
SHOW CREATE TABLE fact_sales;

-- Should show: ENGINE=NDBCLUSTER
```

### Slow Performance
```bash
# Check slow query log
docker exec retail-dwh_dev_sql tail -f /var/log/mysql/slow-query.log

-- Check cluster status
docker exec retail-dwh_dev_mgm ndb_mgm -e "status"
```

## Security Hardening for Production

1. **Change all default passwords** in `prod/.env`
2. **Use Docker Secrets** instead of `.env` files
3. **Bind MySQL to localhost** (already configured in prod)
4. **Restrict Management Node port** (1186) to internal network
5. **Enable TLS** for MySQL connections
6. **Configure firewall rules** to restrict access
7. **Regular security updates** for Docker images
8. **Audit logs** for access monitoring
9. **Implement backup encryption**
10. **Use secrets management** (Vault, AWS Secrets Manager)

## CI/CD Integration

See `ci/.github-workflows-ci.yml` for GitHub Actions pipeline configuration.

Pipeline stages:
1. Lint (Black, isort, Flake8)
2. Unit Tests (pytest)
3. Integration Tests (spin up TEST cluster, run ETL)
4. Compose Validation (validate all environment files)
5. Deploy TEST (on develop branch)
6. Deploy PROD (on main + version tag)
