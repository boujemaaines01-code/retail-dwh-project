"""
Data Warehouse Loader
Loads cleaned data into MySQL NDB Cluster with surrogate key resolution
"""

import pandas as pd
import logging
from typing import Dict, Optional
from ..utils.db_connection import DBConnection
from ..utils.logger import setup_logger

logger = setup_logger('dwh_loader')


class DWHLoader:
    """Load data into the data warehouse"""
    
    def __init__(self, host: str = 'localhost', port: int = 3306,
                 user: str = None, password: str = None):
        self.db = DBConnection(host=host, port=port, user=user, password=password)
        self.key_mappings = {
            'customers': {},
            'products': {},
            'stores': {},
            'time': {}
        }
        
    def load_time_dimension(self, df: pd.DataFrame) -> int:
        """Load time dimension data"""
        logger.info(f"Loading time dimension: {len(df)} rows")
        
        # Check if table is empty
        query = "SELECT COUNT(*) as count FROM dim_time"
        result = self.db.execute_query(query)
        if result[0]['count'] > 0:
            logger.info("Time dimension already loaded, skipping")
            return result[0]['count']
        
        # Load data
        insert_query = """
        INSERT INTO dim_time 
        (time_key, full_date, day_name, month_name, month_num, quarter, year, 
         is_weekend, is_holiday, week_of_year)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        data = [tuple(row) for row in df[['time_key', 'full_date', 'day_name', 'month_name',
                                          'month_num', 'quarter', 'year', 'is_weekend',
                                          'is_holiday', 'week_of_year']].values]
        
        rows_inserted = self.db.execute_batch(insert_query, data, batch_size=500)
        
        # Build key mapping
        for _, row in df.iterrows():
            self.key_mappings['time'][row['full_date']] = row['time_key']
        
        logger.info(f"Time dimension loaded: {rows_inserted} rows")
        return rows_inserted
    
    def load_customers(self, df: pd.DataFrame) -> int:
        """Load customer dimension data"""
        logger.info(f"Loading customer dimension: {len(df)} rows")
        
        # Load data using REPLACE INTO for idempotency
        insert_query = """
        REPLACE INTO dim_customers 
        (customer_key, customer_id, first_name, last_name, email, phone, loyalty_tier,
         region, city, country, age_group, registration_date, is_active)
        VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        data = [tuple(row) for row in df[['customer_id', 'first_name', 'last_name', 'email',
                                          'phone', 'loyalty_tier', 'region', 'city', 'country',
                                          'age_group', 'registration_date', 'is_active']].values]
        
        rows_inserted = self.db.execute_batch(insert_query, data, batch_size=500)
        
        # Refresh key mapping
        query = "SELECT customer_key, customer_id FROM dim_customers"
        result = self.db.execute_query(query)
        for row in result:
            self.key_mappings['customers'][row['customer_id']] = row['customer_key']
        
        logger.info(f"Customer dimension loaded: {rows_inserted} rows")
        return rows_inserted
    
    def load_products(self, df: pd.DataFrame) -> int:
        """Load product dimension data"""
        logger.info(f"Loading product dimension: {len(df)} rows")
        
        insert_query = """
        REPLACE INTO dim_products 
        (product_key, product_id, product_name, category, subcategory, brand, unit_cost,
         unit_price, margin_pct, supplier_id, supplier_name, is_active, introduced_date)
        VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        data = [tuple(row) for row in df[['product_id', 'product_name', 'category', 'subcategory',
                                          'brand', 'unit_cost', 'unit_price', 'margin_pct',
                                          'supplier_id', 'supplier_name', 'is_active',
                                          'introduced_date']].values]
        
        rows_inserted = self.db.execute_batch(insert_query, data, batch_size=500)
        
        # Refresh key mapping
        query = "SELECT product_key, product_id FROM dim_products"
        result = self.db.execute_query(query)
        for row in result:
            self.key_mappings['products'][row['product_id']] = row['product_key']
        
        logger.info(f"Product dimension loaded: {rows_inserted} rows")
        return rows_inserted
    
    def load_stores(self, df: pd.DataFrame) -> int:
        """Load store dimension data"""
        logger.info(f"Loading store dimension: {len(df)} rows")
        
        insert_query = """
        REPLACE INTO dim_stores 
        (store_key, store_id, store_name, store_type, channel, region, city, address,
         country, opening_date, square_footage, is_active)
        VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        data = [tuple(row) for row in df[['store_id', 'store_name', 'store_type', 'channel',
                                          'region', 'city', 'address', 'country', 'opening_date',
                                          'square_footage', 'is_active']].values]
        
        rows_inserted = self.db.execute_batch(insert_query, data, batch_size=500)
        
        # Refresh key mapping
        query = "SELECT store_key, store_id FROM dim_stores"
        result = self.db.execute_query(query)
        for row in result:
            self.key_mappings['stores'][row['store_id']] = row['store_key']
        
        logger.info(f"Store dimension loaded: {rows_inserted} rows")
        return rows_inserted
    
    def load_sales_facts(self, df: pd.DataFrame) -> int:
        """Load sales fact data with surrogate key resolution"""
        logger.info(f"Loading sales facts: {len(df)} rows")
        
        # Ensure key mappings are loaded
        if not self.key_mappings['customers']:
            query = "SELECT customer_key, customer_id FROM dim_customers"
            result = self.db.execute_query(query)
            for row in result:
                self.key_mappings['customers'][row['customer_id']] = row['customer_key']
        
        if not self.key_mappings['products']:
            query = "SELECT product_key, product_id FROM dim_products"
            result = self.db.execute_query(query)
            for row in result:
                self.key_mappings['products'][row['product_id']] = row['product_key']
        
        if not self.key_mappings['stores']:
            query = "SELECT store_key, store_id FROM dim_stores"
            result = self.db.execute_query(query)
            for row in result:
                self.key_mappings['stores'][row['store_id']] = row['store_key']
        
        # Resolve surrogate keys
        df['customer_key'] = df['customer_id'].map(self.key_mappings['customers'])
        df['product_key'] = df['product_id'].map(self.key_mappings['products'])
        df['store_key'] = df['store_id'].map(self.key_mappings['stores'])
        
        # Remove rows with unresolved keys
        original_count = len(df)
        df = df.dropna(subset=['customer_key', 'product_key', 'store_key'])
        if len(df) < original_count:
            logger.warning(f"Removed {original_count - len(df)} rows with unresolved foreign keys")
        
        # Convert keys to integers
        df['customer_key'] = df['customer_key'].astype(int)
        df['product_key'] = df['product_key'].astype(int)
        df['store_key'] = df['store_key'].astype(int)
        df['time_key'] = df['time_key'].astype(int)
        
        # Load data using INSERT IGNORE to handle duplicates
        insert_query = """
        INSERT IGNORE INTO fact_sales 
        (transaction_id, transaction_date, time_key, customer_key, product_key, store_key,
         quantity, unit_price, net_revenue, gross_profit, discount_pct, discount_amount,
         return_quantity, source_system)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        data = [tuple(row) for row in df[['transaction_id', 'transaction_date', 'time_key',
                                          'customer_key', 'product_key', 'store_key', 'quantity',
                                          'unit_price', 'net_revenue', 'gross_profit', 'discount_pct',
                                          'discount_amount', 'return_quantity', 'source_system']].values]
        
        rows_inserted = self.db.execute_batch(insert_query, data, batch_size=1000)
        
        logger.info(f"Sales facts loaded: {rows_inserted} rows")
        return rows_inserted
    
    def start_etl_run(self, mode: str, source_system: str = None) -> int:
        """Start a new ETL run record"""
        query = """
        INSERT INTO etl_control (run_mode, status, rows_processed, rows_inserted, rows_updated, source_system)
        VALUES (%s, 'running', 0, 0, 0, %s)
        """
        self.db.execute_update(query, (mode, source_system))
        
        query = "SELECT LAST_INSERT_ID() as run_id"
        result = self.db.execute_query(query)
        return result[0]['run_id']
    
    def complete_etl_run(self, run_id: int, status: str, rows_processed: int,
                         rows_inserted: int, rows_updated: int, error_message: str = None):
        """Complete an ETL run record"""
        query = """
        UPDATE etl_control
        SET end_time = NOW(), status = %s, rows_processed = %s, 
            rows_inserted = %s, rows_updated = %s, error_message = %s
        WHERE run_id = %s
        """
        self.db.execute_update(query, (status, rows_processed, rows_inserted, rows_updated, error_message, run_id))
