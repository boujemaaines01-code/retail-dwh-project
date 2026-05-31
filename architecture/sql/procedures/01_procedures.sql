-- ============================================================================
-- Retail Data Warehouse Stored Procedures
-- MySQL NDB Cluster
-- ============================================================================

USE retail_dwh;

DELIMITER //

-- ============================================================================
-- PROCEDURE: Calculate Store Revenue Summary
-- ============================================================================
CREATE PROCEDURE IF NOT EXISTS sp_store_revenue_summary(
    IN p_start_date DATE,
    IN p_end_date DATE
)
BEGIN
    SELECT 
        s.store_id,
        s.store_name,
        s.store_type,
        s.channel,
        s.region,
        COUNT(DISTINCT f.transaction_id) AS total_transactions,
        SUM(f.quantity) AS total_units_sold,
        SUM(f.net_revenue) AS total_net_revenue,
        SUM(f.gross_profit) AS total_gross_profit,
        ROUND(SUM(f.gross_profit) / SUM(f.net_revenue) * 100, 2) AS profit_margin_pct,
        ROUND(SUM(f.net_revenue) / COUNT(DISTINCT f.transaction_id), 2) AS avg_basket_value
    FROM fact_sales f
    JOIN dim_stores s ON f.store_key = s.store_key
    JOIN dim_time t ON f.time_key = t.time_key
    WHERE t.full_date BETWEEN p_start_date AND p_end_date
    GROUP BY s.store_id, s.store_name, s.store_type, s.channel, s.region
    ORDER BY total_net_revenue DESC;
END //

-- ============================================================================
-- PROCEDURE: RFM Customer Segmentation
-- ============================================================================
CREATE PROCEDURE IF NOT EXISTS sp_rfm_segmentation()
BEGIN
    DROP TEMPORARY TABLE IF EXISTS temp_rfm;
    
    CREATE TEMPORARY TABLE temp_rfm AS
    SELECT 
        c.customer_key,
        c.customer_id,
        CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
        c.loyalty_tier,
        COUNT(DISTINCT f.transaction_id) AS frequency,
        SUM(f.net_revenue) AS monetary,
        MAX(f.transaction_date) AS last_purchase_date,
        DATEDIFF(CURDATE(), MAX(f.transaction_date)) AS recency_days
    FROM fact_sales f
    JOIN dim_customers c ON f.customer_key = c.customer_key
    GROUP BY c.customer_key, c.customer_id, c.first_name, c.last_name, c.loyalty_tier;
    
    -- Calculate RFM scores and segments
    SELECT 
        customer_id,
        customer_name,
        loyalty_tier,
        frequency,
        monetary,
        recency_days,
        last_purchase_date,
        CASE 
            WHEN recency_days <= 30 AND frequency >= 10 AND monetary >= 1000 THEN 'Champions'
            WHEN recency_days <= 60 AND frequency >= 5 AND monetary >= 500 THEN 'Loyal Customers'
            WHEN recency_days <= 90 AND frequency >= 3 THEN 'Potential Loyalists'
            WHEN recency_days <= 30 AND frequency < 3 THEN 'New Customers'
            WHEN recency_days BETWEEN 91 AND 180 THEN 'At Risk'
            WHEN recency_days > 180 THEN 'Churned'
            ELSE 'Others'
        END AS rfm_segment
    FROM temp_rfm
    ORDER BY monetary DESC;
END //

-- ============================================================================
-- PROCEDURE: Daily Sales Summary
-- ============================================================================
CREATE PROCEDURE IF NOT EXISTS sp_daily_sales_summary(
    IN p_date DATE
)
BEGIN
    SELECT 
        t.full_date,
        t.day_name,
        t.is_weekend,
    COUNT(DISTINCT f.transaction_id) AS total_transactions,
        SUM(f.quantity) AS total_units_sold,
        SUM(f.net_revenue) AS total_net_revenue,
        SUM(f.gross_profit) AS total_gross_profit,
        ROUND(AVG(f.discount_pct), 2) AS avg_discount_pct,
        COUNT(DISTINCT f.customer_key) AS unique_customers,
        COUNT(DISTINCT f.store_key) AS active_stores
    FROM fact_sales f
    JOIN dim_time t ON f.time_key = t.time_key
    WHERE t.full_date = p_date
    GROUP BY t.full_date, t.day_name, t.is_weekend;
END //

-- ============================================================================
-- PROCEDURE: Product Performance by Category
-- ============================================================================
CREATE PROCEDURE IF NOT EXISTS sp_product_category_performance()
BEGIN
    SELECT 
        p.category,
        p.subcategory,
        COUNT(DISTINCT p.product_id) AS total_products,
        COUNT(DISTINCT f.transaction_id) AS total_transactions,
        SUM(f.quantity) AS total_units_sold,
        SUM(f.net_revenue) AS total_net_revenue,
        SUM(f.gross_profit) AS total_gross_profit,
        ROUND(SUM(f.gross_profit) / SUM(f.net_revenue) * 100, 2) AS profit_margin_pct,
        ROUND(SUM(f.return_quantity) / SUM(f.quantity) * 100, 2) AS return_rate_pct
    FROM dim_products p
    LEFT JOIN fact_sales f ON p.product_key = f.product_key
    GROUP BY p.category, p.subcategory
    ORDER BY total_net_revenue DESC;
END //

-- ============================================================================
-- PROCEDURE: Channel Comparison
-- ============================================================================
CREATE PROCEDURE IF NOT EXISTS sp_channel_comparison(
    IN p_start_date DATE,
    IN p_end_date DATE
)
BEGIN
    SELECT 
        s.channel,
        COUNT(DISTINCT s.store_id) AS total_stores,
        COUNT(DISTINCT f.transaction_id) AS total_transactions,
        SUM(f.quantity) AS total_units_sold,
        SUM(f.net_revenue) AS total_net_revenue,
        SUM(f.gross_profit) AS total_gross_profit,
        ROUND(SUM(f.net_revenue) / COUNT(DISTINCT f.transaction_id), 2) AS avg_basket_value,
        ROUND(AVG(f.discount_pct), 2) AS avg_discount_pct,
        COUNT(DISTINCT f.customer_key) AS unique_customers
    FROM fact_sales f
    JOIN dim_stores s ON f.store_key = s.store_key
    JOIN dim_time t ON f.time_key = t.time_key
    WHERE t.full_date BETWEEN p_start_date AND p_end_date
    GROUP BY s.channel
    ORDER BY total_net_revenue DESC;
END //

-- ============================================================================
-- PROCEDURE: Update ETL Control
-- ============================================================================
CREATE PROCEDURE IF NOT EXISTS sp_update_etl_control(
    IN p_run_id BIGINT,
    IN p_status VARCHAR(20),
    IN p_rows_processed INT,
    IN p_rows_inserted INT,
    IN p_rows_updated INT,
    IN p_error_message TEXT
)
BEGIN
    UPDATE etl_control
    SET 
        end_time = NOW(),
        status = p_status,
        rows_processed = p_rows_processed,
        rows_inserted = p_rows_inserted,
        rows_updated = p_rows_updated,
        error_message = p_error_message
    WHERE run_id = p_run_id;
END //

DELIMITER ;
