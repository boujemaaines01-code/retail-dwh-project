# Retail Data Warehouse Architecture

## System Overview

This Retail Data Warehouse implements a star schema design using MySQL NDB Cluster for high availability and scalability. The system consolidates data from three source systems: POS (Point of Sale), ERP (Enterprise Resource Planning), and E-commerce.

## Architecture Diagram

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
         │  │  SQL NODE   │  ← MySQL API point   │
         │  │  Port: 3306 │                       │
         │  └─────────────┘                       │
         └────────────────────────────────────────┘
                          │
         ┌────────────────▼──────────────────────┐
         │        ANALYTICS LAYER                 │
         │  • SQL Queries (7 analytics)           │
         │  • Stored Procedures (RFM, etc.)       │
         │  • Metabase BI (DAC environment)       │
         └────────────────────────────────────────┘
```

## MySQL Cluster Node Roles

| Node | Role | Container | Purpose |
|---|---|---|---|
| **Management Node** | Cluster configuration & arbitration | `retail-dwh_*_mgm` | Controls cluster startup, configuration, and node arbitration |
| **Data Node 1** | Stores 50% of data, mirrors DN2 | `retail-dwh_*_dn1` | Stores partitioned data with automatic replication |
| **Data Node 2** | Stores 50% of data, mirrors DN1 | `retail-dwh_*_dn2` | Stores partitioned data with automatic replication |
| **SQL Node** | MySQL API — all queries go here | `retail-dwh_*_sql` | Provides standard MySQL interface to NDB storage |

## Star Schema Design

### Grain
One row per transaction line item (one product in one sale).

### Fact Table: fact_sales

| Column | Type | Description |
|---|---|---|
| sale_key | BIGINT UNSIGNED PK | Surrogate key |
| transaction_id | VARCHAR(100) | Business key from source |
| transaction_date | DATE | Date of transaction |
| time_key | INT UNSIGNED FK | Foreign key to dim_time |
| customer_key | INT UNSIGNED FK | Foreign key to dim_customers |
| product_key | INT UNSIGNED FK | Foreign key to dim_products |
| store_key | INT UNSIGNED FK | Foreign key to dim_stores |
| quantity | INT UNSIGNED | Units sold |
| unit_price | DECIMAL(10,2) | Price per unit |
| net_revenue | DECIMAL(12,2) | Revenue after discounts |
| gross_profit | DECIMAL(12,2) | Profit from sale |
| discount_pct | DECIMAL(5,2) | Discount percentage |
| discount_amount | DECIMAL(10,2) | Discount amount |
| return_quantity | INT UNSIGNED | Units returned |
| source_system | ENUM | POS, ERP, or E-commerce |

### Dimension Tables

#### dim_time
- Time dimension for date-based analytics
- Attributes: full_date, day_name, month_name, quarter, year, is_weekend, is_holiday

#### dim_customers
- Customer dimension with loyalty and demographic data
- Attributes: customer_id, name, contact info, loyalty_tier, region, age_group

#### dim_products
- Product dimension with catalog and supplier information
- Attributes: product_id, name, category, brand, pricing, supplier

#### dim_stores
- Store/channel dimension for physical and online locations
- Attributes: store_id, name, type, channel (POS/ERP/E-commerce), region

## Multi-Environment Strategy

| Environment | Purpose | MySQL Port | Additional Services |
|---|---|---|---|
| **DEV** | Local development | 3306 | Adminer (8080) |
| **TEST** | Integration testing / CI | 3307 | — |
| **PROD** | Production (localhost bind) | 3306 | — |
| **DAC** | BI & analytics teams | 3308 | Metabase (3000) |

Each environment has:
- Isolated Docker network (no cross-environment communication)
- Persistent Docker volumes
- Separate .env configuration
- Independent MySQL Cluster instance

## ETL Pipeline Architecture

### Data Flow
```
[Data Generator] → [DataCleaner] → [DWH Loader] → [MySQL Cluster]
   (Synthetic)       (Validate)      (Bulk Insert)
```

### ETL Modes

#### Initial Load
1. Load all dimension tables first
2. Resolve surrogate keys
3. Load fact_sales with resolved keys
4. Record run in etl_control table

#### Incremental Load
1. Load existing dimensions for key resolution
2. Generate new transaction data
3. Clean and validate
4. Append new facts (INSERT IGNORE for idempotency)
5. Record run in etl_control table

### ETL Components

| Component | File | Purpose |
|---|---|---|
| Data Generator | `etl/transformers/data_generator.py` | Generates synthetic retail data |
| Data Cleaner | `etl/transformers/data_cleaner.py` | Validates, cleans, transforms data |
| DWH Loader | `etl/loaders/dwh_loader.py` | Loads data with surrogate key resolution |
| DB Connection | `etl/utils/db_connection.py` | Connection pool with retry logic |
| Logger | `etl/utils/logger.py` | Structured logging with rotation |
| Main Script | `etl/run_etl.py` | CLI entry point for ETL pipeline |

## Technology Stack

- **Database**: MySQL Cluster 8.0 (NDB)
- **Orchestration**: Docker Compose
- **ETL**: Python 3.10+, Pandas, MySQL Connector
- **BI Tool**: Metabase (DAC environment)
- **Data Generation**: Faker library

## Key Design Decisions

1. **MySQL NDB Cluster**: Chosen for high availability, automatic partitioning, and in-memory performance
2. **Star Schema**: Simplifies queries and improves performance for analytics workloads
3. **Surrogate Keys**: Enables slowly changing dimensions and maintains history
4. **Multi-Environment**: Isolates development, testing, and production workloads
5. **Docker Compose**: Provides reproducible, containerized deployment
6. **Python ETL**: Flexible, maintainable, with excellent data processing libraries

## Performance Considerations

- **NDB Memory**: Configured per environment (DEV: 512MB, TEST: 256MB, PROD: 2GB, DAC: 1GB)
- **Batch Loading**: ETL uses batch inserts (1000 rows per batch)
- **Connection Pooling**: DB connection manager with retry logic
- **Indexing**: Strategic indexes on foreign keys and frequently queried columns
- **NoOfReplicas=2**: Provides automatic failover and data redundancy
