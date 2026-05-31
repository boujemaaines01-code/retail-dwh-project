"""
Data Cleaner and Validator
Validates, cleans, and transforms data before loading into the warehouse
"""

import pandas as pd
import numpy as np
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class DataCleaner:
    """Clean and validate data before loading"""
    
    @staticmethod
    def clean_customers(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
        """Clean customer data"""
        logger.info("Cleaning customer data")
        
        original_count = len(df)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['customer_id'], keep='first')
        
        # Handle null values
        df['email'] = df['email'].fillna('unknown@example.com')
        df['phone'] = df['phone'].fillna('000-000-0000')
        
        # Validate data types
        df['registration_date'] = pd.to_datetime(df['registration_date']).dt.date
        
        # Validate enum values
        valid_tiers = ['bronze', 'silver', 'gold', 'platinum']
        df = df[df['loyalty_tier'].isin(valid_tiers)]
        
        valid_age_groups = ['18-24', '25-34', '35-44', '45-54', '55-64', '65+']
        df = df[df['age_group'].isin(valid_age_groups)]
        
        stats = {
            'original_count': original_count,
            'cleaned_count': len(df),
            'removed_count': original_count - len(df)
        }
        
        logger.info(f"Customer cleaning complete: {stats}")
        return df, stats
    
    @staticmethod
    def clean_products(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
        """Clean product data"""
        logger.info("Cleaning product data")
        
        original_count = len(df)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['product_id'], keep='first')
        
        # Handle null values
        df['subcategory'] = df['subcategory'].fillna(df['category'])
        df['supplier_id'] = df['supplier_id'].fillna('SUPP0000')
        df['supplier_name'] = df['supplier_name'].fillna('Unknown Supplier')
        
        # Validate numeric values
        df = df[df['unit_cost'] > 0]
        df = df[df['unit_price'] > 0]
        df = df[df['margin_pct'] >= 0]
        
        # Validate dates
        df['introduced_date'] = pd.to_datetime(df['introduced_date']).dt.date
        
        stats = {
            'original_count': original_count,
            'cleaned_count': len(df),
            'removed_count': original_count - len(df)
        }
        
        logger.info(f"Product cleaning complete: {stats}")
        return df, stats
    
    @staticmethod
    def clean_stores(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
        """Clean store data"""
        logger.info("Cleaning store data")
        
        original_count = len(df)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['store_id'], keep='first')
        
        # Handle null values
        df['address'] = df['address'].fillna('Unknown Address')
        df['square_footage'] = df['square_footage'].fillna(0)
        
        # Validate store types
        valid_types = ['flagship', 'standard', 'outlet', 'online']
        df = df[df['store_type'].isin(valid_types)]
        
        # Validate channels
        valid_channels = ['POS', 'ERP', 'E-commerce']
        df = df[df['channel'].isin(valid_channels)]
        
        # Validate dates
        df['opening_date'] = pd.to_datetime(df['opening_date']).dt.date
        
        stats = {
            'original_count': original_count,
            'cleaned_count': len(df),
            'removed_count': original_count - len(df)
        }
        
        logger.info(f"Store cleaning complete: {stats}")
        return df, stats
    
    @staticmethod
    def clean_time(df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
        """Clean time dimension data"""
        logger.info("Cleaning time dimension data")
        
        original_count = len(df)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['full_date'], keep='first')
        
        # Validate dates
        df['full_date'] = pd.to_datetime(df['full_date']).dt.date
        
        # Sort by date
        df = df.sort_values('full_date')
        
        # Reset time_key sequentially
        df['time_key'] = range(1, len(df) + 1)
        
        stats = {
            'original_count': original_count,
            'cleaned_count': len(df),
            'removed_count': original_count - len(df)
        }
        
        logger.info(f"Time dimension cleaning complete: {stats}")
        return df, stats
    
    @staticmethod
    def clean_sales(df: pd.DataFrame, customers_df: pd.DataFrame,
                   products_df: pd.DataFrame, stores_df: pd.DataFrame,
                   time_df: pd.DataFrame) -> Tuple[pd.DataFrame, dict]:
        """Clean sales transaction data"""
        logger.info("Cleaning sales transaction data")
        
        original_count = len(df)
        
        # Remove duplicates
        df = df.drop_duplicates(subset=['transaction_id', 'product_id'], keep='first')
        
        # Validate foreign keys exist in dimension tables
        valid_customers = set(customers_df['customer_id'])
        valid_products = set(products_df['product_id'])
        valid_stores = set(stores_df['store_id'])
        valid_time_keys = set(time_df['time_key'])
        
        df = df[df['customer_id'].isin(valid_customers)]
        df = df[df['product_id'].isin(valid_products)]
        df = df[df['store_id'].isin(valid_stores)]
        df = df[df['time_key'].isin(valid_time_keys)]
        
        # Validate numeric values
        df = df[df['quantity'] > 0]
        df = df[df['unit_price'] > 0]
        df = df[df['net_revenue'] >= 0]
        df = df[df['gross_profit'] >= 0]
        df = df[df['discount_pct'] >= 0]
        df = df[df['return_quantity'] >= 0]
        
        # Validate return quantity doesn't exceed quantity
        df = df[df['return_quantity'] <= df['quantity']]
        
        # Validate source system
        valid_sources = ['POS', 'ERP', 'E-commerce']
        df = df[df['source_system'].isin(valid_sources)]
        
        # Validate dates
        df['transaction_date'] = pd.to_datetime(df['transaction_date']).dt.date
        
        stats = {
            'original_count': original_count,
            'cleaned_count': len(df),
            'removed_count': original_count - len(df)
        }
        
        logger.info(f"Sales cleaning complete: {stats}")
        return df, stats
