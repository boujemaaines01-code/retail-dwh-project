# Data Flow Documentation

## Source Systems Integration

### POS (Point of Sale)
- **Data Captured**: In-store transactions, cashier data
- **Channel**: Physical retail locations
- **Frequency**: Real-time transaction capture
- **Integration**: ETL extracts transaction records, resolves customer/product keys

### ERP (Enterprise Resource Planning)
- **Data Captured**: Product catalog, supplier info, inventory levels
- **Channel**: Enterprise system
- **Frequency**: Daily batch updates
- **Integration**: ETL extracts product master data, inventory changes

### E-commerce
- **Data Captured**: Online orders, web customer behavior
- **Channel**: Web platform
- **Frequency**: Real-time order capture
- **Integration**: ETL extracts web orders, customer web profiles

## ETL Data Flow

### Phase 1: Data Generation/Extraction
```
Source Systems → Raw CSV Files → Pandas DataFrame
```

For this project, synthetic data is generated using the Faker library:
- **Customers**: 1,000 records with demographics and loyalty tiers
- **Products**: 500 records with pricing and supplier information
- **Stores**: 50 records (47 physical + 3 online)
- **Time Dimension**: 6 years of daily records (2020-2025)
- **Sales Transactions**: Configurable (default 50,000 rows)

### Phase 2: Data Cleaning & Validation
```
Raw Data → DataCleaner → Validated Data
```

Cleaning operations per table:
- **Customers**: Remove duplicates, validate email/phone, validate enum values
- **Products**: Remove duplicates, validate pricing, validate margins
- **Stores**: Remove duplicates, validate store types and channels
- **Time**: Remove duplicates, sort chronologically, reset sequence
- **Sales**: Validate foreign keys, validate numeric values, validate business rules

### Phase 3: Surrogate Key Resolution
```
Business Keys → Lookup Tables → Surrogate Keys
```

Key resolution process:
1. Load dimension tables with business keys (customer_id, product_id, store_id)
2. Auto-generate surrogate keys (customer_key, product_key, store_key)
3. Build in-memory mapping: business_key → surrogate_key
4. Apply mapping to fact table before loading

### Phase 4: Data Loading
```
Validated Data → Batch Insert → MySQL NDB Cluster
```

Loading strategy:
- **Dimensions**: REPLACE INTO for idempotency (upsert semantics)
- **Facts**: INSERT IGNORE to handle duplicates gracefully
- **Batch Size**: 500 rows for dimensions, 1000 rows for facts
- **Transaction**: Each batch is committed independently

## Data Warehouse Loading Sequence

### Initial Load Sequence
1. **dim_time** (no dependencies)
2. **dim_customers** (no dependencies)
3. **dim_products** (no dependencies)
4. **dim_stores** (no dependencies)
5. **fact_sales** (depends on all dimensions)

### Incremental Load Sequence
1. Load existing dimensions for key resolution
2. Generate new transaction data
3. Clean and validate sales data
4. Resolve surrogate keys using existing dimension mappings
5. Load new fact records (INSERT IGNORE)

## ETL Control & Auditing

### etl_control Table
Tracks every ETL run for audit and monitoring:
- **run_id**: Unique identifier
- **run_mode**: initial or incremental
- **start_time / end_time**: Run duration
- **status**: running, completed, failed
- **rows_processed**: Total rows handled
- **rows_inserted**: New rows added
- **rows_updated**: Existing rows modified
- **error_message**: Failure details (if any)
- **source_system**: Source of data (POS, ERP, E-commerce, or ALL)

### Audit Queries
```sql
-- View recent ETL runs
SELECT * FROM etl_control 
ORDER BY start_time DESC 
LIMIT 10;

-- Check for failed runs
SELECT * FROM etl_control 
WHERE status = 'failed'
ORDER BY start_time DESC;

-- Calculate ETL performance
SELECT 
    run_mode,
    AVG(rows_processed) as avg_rows,
    AVG(TIMESTAMPDIFF(SECOND, start_time, end_time)) as avg_duration_sec
FROM etl_control
WHERE status = 'completed'
GROUP BY run_mode;
```

## Data Quality Checks

### Pre-Load Validation
- **Null Checks**: Ensure no NULL values in required fields
- **Data Type Validation**: Verify correct data types
- **Enum Validation**: Ensure valid enum values
- **Foreign Key Validation**: Ensure references exist in dimension tables
- **Business Rule Validation**: Quantity > 0, Price > 0, Return ≤ Quantity

### Post-Load Validation
- **Row Count Verification**: Compare source vs. target counts
- **Referential Integrity**: Verify all foreign keys resolve
- **Aggregate Validation**: Sum of facts matches expectations
- **Duplicate Detection**: Check for unexpected duplicates

## Error Handling

### Connection Errors
- Automatic retry with exponential backoff
- Maximum 3 retry attempts
- Logs connection failures with details

### Data Loading Errors
- Transaction rollback on failure
- Detailed error logging
- ETL control record marked as 'failed'
- Error message captured for troubleshooting

### Key Resolution Errors
- Rows with unresolved foreign keys are filtered out
- Warning logged for filtered rows
- Statistics tracked in cleaning phase

## Performance Optimization

### Batch Processing
- Dimensions: 500 rows per batch
- Facts: 1000 rows per batch
- Reduces network round-trips
- Improves throughput

### Connection Pooling
- Single connection per ETL run
- Reused across all operations
- Reduces connection overhead

### Indexing Strategy
- Primary keys on all tables
- Foreign key indexes on fact table
- Composite indexes on frequently queried columns
- Time-based indexes for date range queries

### Memory Configuration
- DataMemory: Configured per environment
- IndexMemory: 25% of DataMemory
- MaxNoOfConcurrentOperations: Scaled for expected load
