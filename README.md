# 🏪 Retail Data Warehouse — MySQL NDB Cluster

> **Production-ready** retail analytics DWH with MySQL Cluster, multi-environment Docker Compose, Python ETL pipeline, and BI analytics.

---

## 📋 Table of Contents

- [Project Overview](#-project-overview)
- [Architecture](#-architecture)
- [Star Schema](#-star-schema)
- [Project Structure](#-project-structure)
- [Quick Start](#-quick-start)
- [Environment Guide](#-environment-guide)
- [ETL Pipeline](#-etl-pipeline)
- [Analytics Queries](#-analytics-queries)
- [CI/CD](#-cicd)
- [Troubleshooting](#-troubleshooting)

---

## 🎯 Project Overview

This project implements a **complete Retail Data Warehouse** that consolidates data from three source systems:

| Source System | Data Captured |
|---|---|
| **POS** (Point of Sale) | In-store transactions, cashier data |
| **ERP** (Enterprise Resource Planning) | Product catalog, supplier info, inventory |
| **E-commerce** | Online orders, web customer behavior |

**Key capabilities:**
- Unified `fact_sales` table — query across all channels in one SQL
- Star schema with 4 dimension tables (time, customers, products, stores)
- Multi-environment isolation: DEV → TEST → PROD → DAC (Data Analytics Center)
- Full ETL: synthetic data generation, cleaning, initial load, incremental load
- 7 production-grade analytics queries (revenue, trends, top products, promotions, RFM)
- All tables use MySQL NDB Cluster (ENGINE=NDBCLUSTER)
- CI/CD with GitHub Actions

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SOURCE SYSTEMS                                │
│   ┌──────────┐     ┌──────────┐     ┌──────────────────────┐   │
│   │   POS    │     │   ERP    │     │     E-Commerce       │   │
│   └────┬─────┘     └────┬─────┘     └──────────┬───────────┘   │
└────────┼────────────────┼──────────────────────┼───────────────┘
         │                │                      │
         └────────────────┴──────────────────────┘
                          │
              ┌───────────▼───────────┐
              │    ETL PIPELINE       │
              │  Python + Pandas      │
              │  • Extract & Generate │
              │  • Clean & Validate   │
              │  • Load (INITIAL/INCR)│
              └───────────┬───────────┘
                          │
         ┌────────────────▼──────────────────────┐
         │        MYSQL NDB CLUSTER               │
         │                                        │
         │  ┌─────────────┐                       │
         │  │  MGM NODE   │  ← Cluster controller │
         │  │  Port: 1186 │                       │
         │  └──────┬──────┘                       │
         │         │                              │
         │  ┌──────┴──────┐                       │
         │  │             │                       │
         │  ▼             ▼                       │
         │ ┌──────┐   ┌──────┐  ← 2× Data Nodes  │
         │ │ DN1  │   │ DN2  │    (NoOfReplicas=2) │
         │ └──────┘   └──────┘                   │
         │         │                              │
         │  ┌──────▼──────┐                       │
         │  │  SQL NODE   │  ← MySQL access point │
         │  │  Port: 3306 │                       │
         │  └─────────────┘                       │
         └────────────────────────────────────────┘
                          │
         ┌────────────────▼──────────────────────┐
         │        ANALYTICS LAYER                 │
         │  • SQL Queries (7 analytics)           │
         │  • Stored Procedures (RFM, etc.)       │
         │  • Metabase BI (DAC environment)       │
         │  • Prometheus + Grafana (Monitoring)   │
         └────────────────────────────────────────┘
```

### MySQL Cluster Node Roles

| Node | Role | Container |
|---|---|---|
| **Management Node** | Cluster configuration & arbitration | `retail-dwh_dev_mgm` |
| **Data Node 1** | Stores 50% of data, mirrors DN2 | `retail-dwh_dev_dn1` |
| **Data Node 2** | Stores 50% of data, mirrors DN1 | `retail-dwh_dev_dn2` |
| **SQL Node** | MySQL API — all queries go here | `retail-dwh_dev_sql` |

---

## ⭐ Star Schema

**Grain:** One row per transaction line item (one product in one sale).

```
                    ┌─────────────────┐
                    │   dim_time      │
                    │─────────────────│
                    │ time_key (PK)   │
                    │ full_date       │
                    │ day_name        │
                    │ month_name      │
                    │ quarter         │
                    │ year            │
                    │ is_weekend      │
                    │ is_holiday      │
                    └────────┬────────┘
                             │
┌─────────────────┐          │          ┌─────────────────┐
│  dim_customers  │          │          │  dim_products   │
│─────────────────│          │          │─────────────────│
│ customer_key(PK)│          │          │ product_key (PK)│
│ customer_id     │          │          │ product_id      │
│ first_name      ├──────────┤          │ product_name    │
│ loyalty_tier    │          │          │ category        │
│ region          │    ┌─────▼──────┐   │ brand           │
│ age_group       ├────┤ fact_sales ├───┤ unit_cost       │
└─────────────────┘    │────────────│   │ unit_price      │
                       │ sale_key   │   │ margin_pct      │
┌─────────────────┐    │ time_key   │   └─────────────────┘
│  dim_stores     │    │ customer_k │
│─────────────────│    │ product_k  │
│ store_key (PK)  │    │ store_key  │
│ store_id        ├────┤ quantity   │
│ store_name      │    │ unit_price │
│ store_type      │    │ net_revenue│
│ channel         │    │ gross_prof │
│ region          │    │ discount   │
└─────────────────┘    └────────────┘
```

---

## 📁 Project Structure

```
retail-dwh-project/
├── README.md                          # This file
├── LICENSE                            # MIT License
├── .gitignore                         # Git ignore rules
├── docker-compose.yml                 # Placeholder (see env directories)
│
├── architecture/                      # Architecture documentation
│   ├── overview.md                    # System architecture overview
│   ├── data_flow.md                   # Data flow documentation
│   └── deployment.md                   # Deployment guide
│
├── dev/                               # DEV environment
│   ├── .env                           # DEV environment variables
│   ├── docker-compose.yml             # DEV cluster (port 3306, Adminer 8080)
│   └── config/
│       ├── my.cnf.mgm                 # Management node config
│       └── my.cnf.sql                 # SQL node config
│
├── test/                              # TEST environment (port 3307)
│   ├── .env                           # TEST environment variables
│   ├── docker-compose.yml             # TEST cluster
│   └── config/
│       ├── my.cnf.mgm                 # Management node config
│       └── my.cnf.sql                 # SQL node config
│
├── prod/                              # PROD environment (port 3306 localhost only)
│   ├── .env                           # PROD environment variables
│   ├── docker-compose.yml             # PROD cluster
│   └── config/
│       ├── my.cnf.mgm                 # Management node config
│       └── my.cnf.sql                 # SQL node config
│
├── dac/                               # DAC: cluster + Metabase (port 3308 + 3000)
│   ├── .env                           # DAC environment variables
│   ├── docker-compose.yml             # DAC cluster + Metabase
│   └── config/
│       ├── my.cnf.mgm                 # Management node config
│       └── my.cnf.sql                 # SQL node config
│
├── sql/
│   ├── schema/
│   │   └── 01_schema.sql              # Full DDL (dimensions + fact + ETL control)
│   ├── analytics/
│   │   └── 01_analytics.sql           # 7 production analytics queries
│   └── procedures/
│       └── 01_procedures.sql          # Stored procedures (RFM, store revenue…)
│
├── etl/
│   ├── __init__.py
│   ├── run_etl.py                     # Main entrypoint: --mode initial|incremental
│   ├── requirements.txt               # Python dependencies
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── db_connection.py           # Connection pool manager with retry
│   │   └── logger.py                  # Rotating file + console logger
│   ├── transformers/
│   │   ├── __init__.py
│   │   ├── data_generator.py          # Synthetic retail data generator
│   │   └── data_cleaner.py            # Validation, dedup, null handling
│   └── loaders/
│       ├── __init__.py
│       └── dwh_loader.py              # Initial + incremental loader with audit
│
├── data/
│   ├── raw/                           # Source CSV exports (placeholder)
│   ├── processed/                     # Cleaned staging files (placeholder)
│   └── exports/                       # Analytics result exports (placeholder)
│
├── analysis/
│   └── README.md                      # Analysis documentation
│
├── ci/
│   ├── .github-workflows-ci.yml       # Copy to .github/workflows/ci.yml
│   └── tests/
│       └── unit/
│           └── test_data_cleaner.py   # Unit tests for ETL
│
└── scripts/
    ├── start_dev.sh / start_dev.ps1   # Start DEV cluster with health checks
    ├── stop_dev.sh / stop_dev.ps1     # Stop DEV cluster
    └── run_etl.sh / run_etl.ps1       # Run ETL pipeline
```

---

## 🚀 Quick Start

### Prerequisites

- Docker Engine ≥ 24.0
- Docker Compose ≥ 2.0
- Python ≥ 3.10
- Git

### 1. Clone the repository

```bash
git clone https://github.com/your-org/retail-dwh-project.git
cd retail-dwh-project
```

### 2. Start the DEV MySQL Cluster

```bash
cd dev
docker compose --env-file .env up -d
```

Or use the provided script:
```bash
# Linux/Mac
./scripts/start_dev.sh

# Windows
powershell -ExecutionPolicy Bypass -File scripts/start_dev.ps1
```

Wait ~90 seconds for the cluster to fully initialize, then verify:

```bash
# Check all containers are healthy
docker compose ps

# Check cluster topology via Management Node
docker exec retail-dwh_dev_mgm ndb_mgm -e "show" --ndb-connectstring=localhost:1186

# Test SQL connection
docker exec retail-dwh_dev_sql mysql -u dwh_user -pdwh_dev_pass_2024 -e "SHOW TABLES;" retail_dwh
```

### 3. Install Python dependencies

```bash
cd ..
python -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows
pip install -r etl/requirements.txt
```

### 4. Run the ETL pipeline

```bash
# Full initial load (50,000 transaction rows)
python -m etl.run_etl --mode initial --rows 50000

# Or use the provided script:
# Linux/Mac
./scripts/run_etl.sh initial 50000

# Windows
powershell -ExecutionPolicy Bypass -File scripts/run_etl.ps1 initial 50000

# Incremental load (adds ~2,000 new rows)
python -m etl.run_etl --mode incremental --rows 2000
```

### 5. Run analytics queries

```bash
docker exec retail-dwh_dev_sql mysql \
  -u dwh_analyst -panalyst_dev_2024 \
  retail_dwh < sql/analytics/01_analytics.sql
```

### 6. Open Adminer (web DB UI)

Navigate to **http://localhost:8080**
- Server: `sql_node`
- Username: `dwh_user`
- Password: `dwh_dev_pass_2024`
- Database: `retail_dwh`

---

## 🌍 Environment Guide

| Environment | Purpose | Port | Extra Services |
|---|---|---|---|
| **DEV** | Local development | 3306 | Adminer (8080) |
| **TEST** | Integration testing / CI | 3307 | — |
| **PROD** | Production (localhost bind) | 3306 | — |
| **DAC** | BI & analytics teams | 3308 | Metabase (3000) |

Switch environment:
```bash
cd dev   && docker compose --env-file .env up -d   # DEV
cd test  && docker compose --env-file .env up -d   # TEST
cd prod  && docker compose --env-file .env up -d   # PROD
cd dac   && docker compose --env-file .env up -d   # DAC + Metabase
```

---

## 🔄 ETL Pipeline

### Data Flow

```
[Data Generator] → [DataCleaner] → [DWH Loader] → [MySQL Cluster]
   (Synthetic)       (Validate)      (Bulk Insert)
```

### Initial Load

Loads all dimensions first, then resolves surrogate keys and loads fact_sales.

```bash
python -m etl.run_etl --mode initial --rows 50000
```

### Incremental Load

Upserts changed dimension records (`REPLACE INTO`) and appends new facts.

```bash
python -m etl.run_etl --mode incremental --rows 5000
```

### ETL Audit

Every run is recorded in the `etl_control` table:

```sql
SELECT * FROM retail_dwh.etl_control ORDER BY start_time DESC LIMIT 10;
```

---

##  Analytics Queries

| # | Query | Description |
|---|---|---|
| 1 | Revenue by Store | Net revenue, margin, avg basket per store |
| 2 | Monthly Sales Trends | MoM growth, units, discounts by month |
| 3 | Top 10 Products | Revenue, margin, return rate per SKU |
| 4 | Promotion Impact | Promoted vs. non-promoted comparison |
| 5 | Avg Basket per Customer | RFM segmentation, recency |
| 6 | Revenue by Category × Channel | Cross-tab category vs. POS/ERP/Ecommerce |
| 7 | Weekend vs. Weekday | Performance comparison by day type |

Run all:
```bash
docker exec retail-dwh_dev_sql mysql \
  -u dwh_analyst -panalyst_dev_2024 \
  retail_dwh < sql/analytics/01_analytics.sql
```

---

## CI/CD

The pipeline lives in `ci/.github-workflows-ci.yml`.  
Copy it to the right location before pushing:

```bash
mkdir -p .github/workflows
cp ci/.github-workflows-ci.yml .github/workflows/ci.yml
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions pipeline"
```

**Pipeline stages:**
1. **Lint** — Black, isort, Flake8
2. **Unit Tests** — pytest (no DB required)
3. **Integration Tests** — spins up DEV cluster, runs ETL
4. **Compose Validation** — validates all 4 environment files
5. **Deploy TEST** — on `develop` branch push
6. **Deploy PROD** — on `main` + version tag

---

## Troubleshooting

### Cluster won't start

```bash

docker logs retail-dwh_dev_mgm
docker logs retail-dwh_dev_dn1
docker logs retail-dwh_dev_sql

docker compose down -v
docker compose up -d
```

### ETL connection error

```bash
docker exec retail-dwh_dev_sql mysqladmin ping -u root -pdev_root_pass_2024


cat dev/.env | grep MYSQL
```

### NDB Cluster tables not visible

NDB tables require `ENGINE=NDBCLUSTER`. Verify:
```sql
SHOW CREATE TABLE fact_sales\G
```

### Reset everything

```bash
# Stop and remove all volumes
cd dev && docker compose down -v
cd ../test && docker compose down -v
```

---

##  Production Checklist

- [ ] Change all default passwords in `prod/.env`
- [ ] Use Docker Secrets or Vault instead of `.env` for credentials
- [ ] Configure `DataMemory` / `IndexMemory` based on actual data size
- [ ] Set up regular backups (`ndb_backup`)
- [ ] Enable TLS for MySQL connections
- [ ] Set `MGM_PORT` to not be publicly accessible
- [ ] Review and update security configurations

---

##  License

MIT License — free to use, modify, and distribute.

---

*Built with  using MySQL NDB Cluster 8.0, Docker Compose, and Python 3.10+*
