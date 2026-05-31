-- ============================================================================
-- Retail Data Warehouse Analytics Queries
-- All queries use MySQL NDB Cluster tables
-- ============================================================================

USE retail_dwh;

-- ============================================================================
-- ANALYTICS 1: Revenue by Store
-- ============================================================================
SELECT 
    'Revenue by Store' AS report_name,
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
GROUP BY s.store_id, s.store_name, s.store_type, s.channel, s.region
ORDER BY total_net_revenue DESC;

-- ============================================================================
-- ANALYTICS 2: Monthly Sales Trends
-- ============================================================================
SELECT 
    'Monthly Sales Trends' AS report_name,
    t.year,
    t.month_name,
    t.month_num,
    COUNT(DISTINCT f.transaction_id) AS total_transactions,
    SUM(f.quantity) AS total_units_sold,
    SUM(f.net_revenue) AS total_net_revenue,
    SUM(f.gross_profit) AS total_gross_profit,
    ROUND(AVG(f.discount_pct), 2) AS avg_discount_pct,
    ROUND(SUM(f.net_revenue) / LAG(SUM(f.net_revenue)) OVER (ORDER BY t.year, t.month_num) * 100 - 100, 2) AS mom_growth_pct
FROM fact_sales f
JOIN dim_time t ON f.time_key = t.time_key
GROUP BY t.year, t.month_name, t.month_num
ORDER BY t.year DESC, t.month_num DESC;

-- ============================================================================
-- ANALYTICS 3: Top 10 Products by Revenue
-- ============================================================================
SELECT 
    'Top 10 Products' AS report_name,
    p.product_id,
    p.product_name,
    p.category,
    p.brand,
    COUNT(DISTINCT f.transaction_id) AS transaction_count,
    SUM(f.quantity) AS total_units_sold,
    SUM(f.net_revenue) AS total_net_revenue,
    SUM(f.gross_profit) AS total_gross_profit,
    ROUND(SUM(f.gross_profit) / SUM(f.net_revenue) * 100, 2) AS profit_margin_pct,
    ROUND(SUM(f.return_quantity) / SUM(f.quantity) * 100, 2) AS return_rate_pct
FROM fact_sales f
JOIN dim_products p ON f.product_key = p.product_key
GROUP BY p.product_id, p.product_name, p.category, p.brand
ORDER BY total_net_revenue DESC
LIMIT 10;

-- ============================================================================
-- ANALYTICS 4: Promotion Impact Analysis
-- ============================================================================
SELECT 
    'Promotion Impact' AS report_name,
    CASE 
        WHEN f.discount_pct > 0 THEN 'Promoted'
        ELSE 'Non-Promoted'
    END AS promotion_status,
    COUNT(DISTINCT f.transaction_id) AS total_transactions,
    SUM(f.quantity) AS total_units_sold,
    SUM(f.net_revenue) AS total_net_revenue,
    SUM(f.gross_profit) AS total_gross_profit,
    ROUND(AVG(f.discount_pct), 2) AS avg_discount_pct,
    ROUND(SUM(f.net_revenue) / COUNT(DISTINCT f.transaction_id), 2) AS avg_basket_value,
    ROUND(SUM(f.gross_profit) / SUM(f.net_revenue) * 100, 2) AS profit_margin_pct
FROM fact_sales f
GROUP BY 
    CASE 
        WHEN f.discount_pct > 0 THEN 'Promoted'
        ELSE 'Non-Promoted'
    END
ORDER BY total_net_revenue DESC;

-- ============================================================================
-- ANALYTICS 5: Customer RFM Analysis (Recency, Frequency, Monetary)
-- ============================================================================
SELECT 
    'Customer RFM Analysis' AS report_name,
    c.customer_id,
    CONCAT(c.first_name, ' ', c.last_name) AS customer_name,
    c.loyalty_tier,
    c.region,
    c.age_group,
    COUNT(DISTINCT f.transaction_id) AS frequency,
    SUM(f.net_revenue) AS monetary_value,
    ROUND(SUM(f.net_revenue) / COUNT(DISTINCT f.transaction_id), 2) AS avg_basket_value,
    MAX(f.transaction_date) AS last_purchase_date,
    DATEDIFF(CURDATE(), MAX(f.transaction_date)) AS days_since_last_purchase,
    CASE 
        WHEN DATEDIFF(CURDATE(), MAX(f.transaction_date)) <= 30 THEN 'Active'
        WHEN DATEDIFF(CURDATE(), MAX(f.transaction_date)) <= 90 THEN 'At Risk'
        WHEN DATEDIFF(CURDATE(), MAX(f.transaction_date)) <= 180 THEN 'Lapsing'
        ELSE 'Churned'
    END AS customer_status
FROM fact_sales f
JOIN dim_customers c ON f.customer_key = c.customer_key
GROUP BY c.customer_id, c.first_name, c.last_name, c.loyalty_tier, c.region, c.age_group
ORDER BY monetary_value DESC
LIMIT 20;

-- ============================================================================
-- ANALYTICS 6: Revenue by Category × Channel
-- ============================================================================
SELECT 
    'Revenue by Category × Channel' AS report_name,
    p.category,
    s.channel,
    COUNT(DISTINCT f.transaction_id) AS total_transactions,
    SUM(f.quantity) AS total_units_sold,
    SUM(f.net_revenue) AS total_net_revenue,
    SUM(f.gross_profit) AS total_gross_profit,
    ROUND(SUM(f.net_revenue) / SUM(SUM(f.net_revenue)) OVER (PARTITION BY p.category) * 100, 2) AS category_share_pct,
    ROUND(SUM(f.net_revenue) / SUM(SUM(f.net_revenue)) OVER (PARTITION BY s.channel) * 100, 2) AS channel_share_pct
FROM fact_sales f
JOIN dim_products p ON f.product_key = p.product_key
JOIN dim_stores s ON f.store_key = s.store_key
GROUP BY p.category, s.channel
ORDER BY p.category, s.channel;

-- ============================================================================
-- ANALYTICS 7: Weekend vs Weekday Performance
-- ============================================================================
SELECT 
    'Weekend vs Weekday' AS report_name,
    CASE 
        WHEN t.is_weekend = TRUE THEN 'Weekend'
        ELSE 'Weekday'
    END AS day_type,
    t.day_name,
    COUNT(DISTINCT f.transaction_id) AS total_transactions,
    SUM(f.quantity) AS total_units_sold,
    SUM(f.net_revenue) AS total_net_revenue,
    SUM(f.gross_profit) AS total_gross_profit,
    ROUND(SUM(f.net_revenue) / COUNT(DISTINCT f.transaction_id), 2) AS avg_basket_value,
    ROUND(AVG(f.discount_pct), 2) AS avg_discount_pct
FROM fact_sales f
JOIN dim_time t ON f.time_key = t.time_key
GROUP BY 
    CASE 
        WHEN t.is_weekend = TRUE THEN 'Weekend'
        ELSE 'Weekday'
    END,
    t.day_name
ORDER BY day_type, t.day_name;
