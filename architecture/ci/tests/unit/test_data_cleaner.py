"""
Unit tests for Data Cleaner
"""

import pytest
import pandas as pd
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..')))

from etl.transformers.data_cleaner import DataCleaner


class TestDataCleaner:
    """Test data cleaning functionality"""
    
    def test_clean_customers(self):
        """Test customer data cleaning"""
        cleaner = DataCleaner()
        
        # Create test data
        df = pd.DataFrame({
            'customer_id': ['CUST001', 'CUST002', 'CUST001', 'CUST003'],
            'first_name': ['John', 'Jane', None, 'Bob'],
            'last_name': ['Doe', 'Smith', 'Doe', 'Johnson'],
            'email': ['john@test.com', None, 'john@test.com', 'bob@test.com'],
            'loyalty_tier': ['bronze', 'gold', 'invalid', 'silver'],
            'region': ['Northeast', 'Southeast', 'Northeast', 'Midwest'],
            'city': ['NYC', 'LA', 'NYC', 'Chicago'],
            'country': ['USA', 'USA', 'USA', 'USA'],
            'age_group': ['25-34', '35-44', 'invalid', '45-54'],
            'registration_date': ['2020-01-01', '2020-02-01', '2020-01-01', '2020-03-01'],
            'is_active': [True, True, True, False]
        })
        
        cleaned_df, stats = cleaner.clean_customers(df)
        
        # Verify duplicates removed
        assert len(cleaned_df) < len(df)
        
        # Verify invalid enum values removed
        assert 'invalid' not in cleaned_df['loyalty_tier'].values
        assert 'invalid' not in cleaned_df['age_group'].values
        
        # Verify nulls handled
        assert cleaned_df['email'].isna().sum() == 0
        
        # Verify stats
        assert stats['original_count'] == 4
        assert stats['removed_count'] > 0
        
    def test_clean_products(self):
        """Test product data cleaning"""
        cleaner = DataCleaner()
        
        df = pd.DataFrame({
            'product_id': ['PROD001', 'PROD002', 'PROD001', 'PROD003'],
            'product_name': ['Widget', 'Gadget', 'Widget', 'Thing'],
            'category': ['Electronics', 'Clothing', 'Electronics', 'Home'],
            'subcategory': ['Premium', None, 'Premium', 'Standard'],
            'brand': ['TechPro', 'StyleCo', 'TechPro', 'HomeMaster'],
            'unit_cost': [10.0, 15.0, 10.0, -5.0],
            'unit_price': [20.0, 30.0, 20.0, 0.0],
            'margin_pct': [50.0, 50.0, 50.0, 50.0],
            'supplier_id': ['SUPP001', 'SUPP002', 'SUPP001', None],
            'supplier_name': ['Supplier A', 'Supplier B', 'Supplier A', None],
            'is_active': [True, True, True, True],
            'introduced_date': ['2020-01-01', '2020-02-01', '2020-01-01', '2020-03-01']
        })
        
        cleaned_df, stats = cleaner.clean_products(df)
        
        # Verify invalid pricing removed
        assert all(cleaned_df['unit_cost'] > 0)
        assert all(cleaned_df['unit_price'] > 0)
        
        # Verify nulls handled
        assert cleaned_df['subcategory'].isna().sum() == 0
        assert cleaned_df['supplier_id'].isna().sum() == 0
        
    def test_clean_stores(self):
        """Test store data cleaning"""
        cleaner = DataCleaner()
        
        df = pd.DataFrame({
            'store_id': ['STORE001', 'STORE002', 'STORE001', 'STORE003'],
            'store_name': ['Main Store', 'Downtown', 'Main Store', 'Mall'],
            'store_type': ['flagship', 'standard', 'flagship', 'invalid'],
            'channel': ['POS', 'ERP', 'POS', 'invalid'],
            'region': ['Northeast', 'Southeast', 'Northeast', 'Midwest'],
            'city': ['NYC', 'LA', 'NYC', 'Chicago'],
            'address': ['123 Main', '456 Oak', '123 Main', None],
            'country': ['USA', 'USA', 'USA', 'USA'],
            'opening_date': ['2020-01-01', '2020-02-01', '2020-01-01', '2020-03-01'],
            'square_footage': [10000, 5000, 10000, None],
            'is_active': [True, True, True, True]
        })
        
        cleaned_df, stats = cleaner.clean_stores(df)
        
        # Verify invalid enum values removed
        assert 'invalid' not in cleaned_df['store_type'].values
        assert 'invalid' not in cleaned_df['channel'].values
        
        # Verify nulls handled
        assert cleaned_df['address'].isna().sum() == 0
        assert cleaned_df['square_footage'].isna().sum() == 0
        
    def test_clean_time(self):
        """Test time dimension cleaning"""
        cleaner = DataCleaner()
        
        df = pd.DataFrame({
            'time_key': [1, 2, 3, 4],
            'full_date': ['2020-01-01', '2020-01-02', '2020-01-01', '2020-01-03'],
            'day_name': ['Monday', 'Tuesday', 'Monday', 'Wednesday'],
            'month_name': ['January', 'January', 'January', 'January'],
            'month_num': [1, 1, 1, 1],
            'quarter': [1, 1, 1, 1],
            'year': [2020, 2020, 2020, 2020],
            'is_weekend': [False, False, False, False],
            'is_holiday': [False, False, False, False],
            'week_of_year': [1, 1, 1, 1]
        })
        
        cleaned_df, stats = cleaner.clean_time(df)
        
        # Verify duplicates removed
        assert len(cleaned_df) < len(df)
        
        # Verify time_key reset sequentially
        assert list(cleaned_df['time_key']) == list(range(1, len(cleaned_df) + 1))
