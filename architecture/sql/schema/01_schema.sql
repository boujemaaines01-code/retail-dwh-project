-- ============================================================================
-- Retail Data Warehouse Schema
-- MySQL NDB Cluster - All tables use ENGINE=NDBCLUSTER
-- ============================================================================

-- Create database
CREATE DATABASE IF NOT EXISTS retail_dwh;
USE retail_dwh;

-- ============================================================================
-- DIMENSION TABLES
-- ============================================================================

-- dim_time: Time dimension for date-based analytics
CREATE TABLE IF NOT EXISTS dim_time (
    time_key INT UNSIGNED NOT NULL AUTO_INCREMENT,
    full_date DATE NOT NULL,
    day_name VARCHAR(20) NOT NULL,
    month_name VARCHAR(20) NOT NULL,
    month_num TINYINT UNSIGNED NOT NULL,
    quarter TINYINT UNSIGNED NOT NULL,
    year SMALLINT UNSIGNED NOT NULL,
    is_weekend BOOLEAN NOT NULL DEFAULT FALSE,
    is_holiday BOOLEAN NOT NULL DEFAULT FALSE,
    week_of_year TINYINT UNSIGNED NOT NULL,
    PRIMARY KEY (time_key),
    UNIQUE KEY uk_full_date (full_date),
    KEY idx_year_month (year, month_num),
    KEY idx_quarter (quarter)
) ENGINE=NDBCLUSTER DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Time dimension - one row per date';

-- dim_customers: Customer dimension
CREATE TABLE IF NOT EXISTS dim_customers (
    customer_key INT UNSIGNED NOT NULL AUTO_INCREMENT,
    customer_id VARCHAR(50) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    loyalty_tier ENUM('bronze', 'silver', 'gold', 'platinum') NOT NULL DEFAULT 'bronze',
    region VARCHAR(50) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(50) NOT NULL DEFAULT 'USA',
    age_group ENUM('18-24', '25-34', '35-44', '45-54', '55-64', '65+') NOT NULL,
    registration_date DATE NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (customer_key),
    UNIQUE KEY uk_customer_id (customer_id),
    KEY idx_loyalty_tier (loyalty_tier),
    KEY idx_region (region),
    KEY idx_age_group (age_group)
) ENGINE=NDBCLUSTER DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Customer dimension';

-- dim_products: Product dimension
CREATE TABLE IF NOT EXISTS dim_products (
    product_key INT UNSIGNED NOT NULL AUTO_INCREMENT,
    product_id VARCHAR(50) NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    brand VARCHAR(100) NOT NULL,
    unit_cost DECIMAL(10, 2) NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    margin_pct DECIMAL(5, 2) NOT NULL,
    supplier_id VARCHAR(50),
    supplier_name VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    introduced_date DATE NOT NULL,
    PRIMARY KEY (product_key),
    UNIQUE KEY uk_product_id (product_id),
    KEY idx_category (category),
    KEY idx_brand (brand),
    KEY idx_supplier (supplier_id)
) ENGINE=NDBCLUSTER DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Product dimension';

-- dim_stores: Store/channel dimension
CREATE TABLE IF NOT EXISTS dim_stores (
    store_key INT UNSIGNED NOT NULL AUTO_INCREMENT,
    store_id VARCHAR(50) NOT NULL,
    store_name VARCHAR(255) NOT NULL,
    store_type ENUM('flagship', 'standard', 'outlet', 'online') NOT NULL,
    channel ENUM('POS', 'ERP', 'E-commerce') NOT NULL,
    region VARCHAR(50) NOT NULL,
    city VARCHAR(100) NOT NULL,
    address VARCHAR(500),
    country VARCHAR(50) NOT NULL DEFAULT 'USA',
    opening_date DATE NOT NULL,
    square_footage INT UNSIGNED,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (store_key),
    UNIQUE KEY uk_store_id (store_id),
    KEY idx_channel (channel),
    KEY idx_region (region),
    KEY idx_store_type (store_type)
) ENGINE=NDBCLUSTER DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Store/Channel dimension';

-- ============================================================================
-- FACT TABLE
-- ============================================================================

-- fact_sales: Sales fact table
-- Grain: One row per product line in a transaction
CREATE TABLE IF NOT EXISTS fact_sales (
    sale_key BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    transaction_id VARCHAR(100) NOT NULL,
    transaction_date DATE NOT NULL,
    time_key INT UNSIGNED NOT NULL,
    customer_key INT UNSIGNED NOT NULL,
    product_key INT UNSIGNED NOT NULL,
    store_key INT UNSIGNED NOT NULL,
    quantity INT UNSIGNED NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    net_revenue DECIMAL(12, 2) NOT NULL,
    gross_profit DECIMAL(12, 2) NOT NULL,
    discount_pct DECIMAL(5, 2) NOT NULL DEFAULT 0.00,
    discount_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    return_quantity INT UNSIGNED NOT NULL DEFAULT 0,
    source_system ENUM('POS', 'ERP', 'E-commerce') NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (sale_key),
    UNIQUE KEY uk_transaction_product (transaction_id, product_key),
    KEY idx_time_key (time_key),
    KEY idx_customer_key (customer_key),
    KEY idx_product_key (product_key),
    KEY idx_store_key (store_key),
    KEY idx_transaction_date (transaction_date),
    KEY idx_source_system (source_system),
    CONSTRAINT fk_fact_sales_time FOREIGN KEY (time_key) REFERENCES dim_time(time_key),
    CONSTRAINT fk_fact_sales_customer FOREIGN KEY (customer_key) REFERENCES dim_customers(customer_key),
    CONSTRAINT fk_fact_sales_product FOREIGN KEY (product_key) REFERENCES dim_products(product_key),
    CONSTRAINT fk_fact_sales_store FOREIGN KEY (store_key) REFERENCES dim_stores(store_key)
) ENGINE=NDBCLUSTER DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Sales fact table - grain: one row per product line item';

-- ============================================================================
-- ETL CONTROL TABLE
-- ============================================================================

-- etl_control: Track ETL runs
CREATE TABLE IF NOT EXISTS etl_control (
    run_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    run_mode ENUM('initial', 'incremental') NOT NULL,
    start_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    status ENUM('running', 'completed', 'failed') NOT NULL DEFAULT 'running',
    rows_processed INT UNSIGNED NOT NULL DEFAULT 0,
    rows_inserted INT UNSIGNED NOT NULL DEFAULT 0,
    rows_updated INT UNSIGNED NOT NULL DEFAULT 0,
    error_message TEXT,
    source_system VARCHAR(50),
    PRIMARY KEY (run_id),
    KEY idx_start_time (start_time),
    KEY idx_status (status)
) ENGINE=NDBCLUSTER DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='ETL run control table';

-- ============================================================================
-- USERS AND PERMISSIONS
-- ============================================================================

-- Create application users
CREATE USER IF NOT EXISTS 'dwh_user'@'%' IDENTIFIED BY 'dwh_dev_pass_2024';
CREATE USER IF NOT EXISTS 'dwh_analyst'@'%' IDENTIFIED BY 'analyst_dev_2024';

-- Grant permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON retail_dwh.* TO 'dwh_user'@'%';
GRANT SELECT ON retail_dwh.* TO 'dwh_analyst'@'%';

FLUSH PRIVILEGES;
