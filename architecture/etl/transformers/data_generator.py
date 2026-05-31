"""
Synthetic Retail Data Generator
Generates realistic sample data for POS, ERP, and E-commerce source systems
"""

import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class RetailDataGenerator:
    """Generate synthetic retail data for testing"""
    
    def __init__(self, seed: int = 42):
        self.fake = Faker()
        Faker.seed(seed)
        np.random.seed(seed)
        random.seed(seed)
        
    def generate_customers(self, n: int = 1000) -> pd.DataFrame:
        """Generate customer dimension data"""
        logger.info(f"Generating {n} customers")
        
        customers = []
        for i in range(n):
            customers.append({
                'customer_id': f'CUST{str(i+1).zfill(6)}',
                'first_name': self.fake.first_name(),
                'last_name': self.fake.last_name(),
                'email': self.fake.email(),
                'phone': self.fake.phone_number(),
                'loyalty_tier': random.choices(
                    ['bronze', 'silver', 'gold', 'platinum'],
                    weights=[50, 30, 15, 5]
                )[0],
                'region': random.choice(['Northeast', 'Southeast', 'Midwest', 'West', 'Southwest']),
                'city': self.fake.city(),
                'country': 'USA',
                'age_group': random.choices(
                    ['18-24', '25-34', '35-44', '45-54', '55-64', '65+'],
                    weights=[15, 25, 25, 20, 10, 5]
                )[0],
                'registration_date': self.fake.date_between(start_date='-5y', end_date='today'),
                'is_active': random.choices([True, False], weights=[95, 5])[0]
            })
        
        return pd.DataFrame(customers)
    
    def generate_products(self, n: int = 500) -> pd.DataFrame:
        """Generate product dimension data"""
        logger.info(f"Generating {n} products")
        
        categories = ['Electronics', 'Clothing', 'Home & Garden', 'Sports', 'Books',
                     'Toys', 'Food & Beverage', 'Health & Beauty', 'Automotive', 'Jewelry']
        brands = ['TechPro', 'StyleCo', 'HomeMaster', 'SportMax', 'BookWorld',
                 'ToyKing', 'FreshMart', 'HealthPlus', 'AutoGear', 'LuxGems']
        
        products = []
        for i in range(n):
            category = random.choice(categories)
            brand = random.choice(brands)
            unit_cost = round(random.uniform(5.0, 200.0), 2)
            margin_pct = round(random.uniform(15.0, 50.0), 2)
            unit_price = round(unit_cost * (1 + margin_pct / 100), 2)
            
            products.append({
                'product_id': f'PROD{str(i+1).zfill(6)}',
                'product_name': f'{brand} {self.fake.word().title()} {category.split()[0]}',
                'category': category,
                'subcategory': f'{category} - {random.choice(["Premium", "Standard", "Budget"])}',
                'brand': brand,
                'unit_cost': unit_cost,
                'unit_price': unit_price,
                'margin_pct': margin_pct,
                'supplier_id': f'SUPP{str(random.randint(1, 50)).zfill(4)}',
                'supplier_name': f'{self.fake.company()} Supplier',
                'is_active': random.choices([True, False], weights=[98, 2])[0],
                'introduced_date': self.fake.date_between(start_date='-3y', end_date='today')
            })
        
        return pd.DataFrame(products)
    
    def generate_stores(self, n: int = 50) -> pd.DataFrame:
        """Generate store/channel dimension data"""
        logger.info(f"Generating {n} stores")
        
        stores = []
        cities = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix',
                 'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'San Jose']
        
        # Physical stores
        for i in range(n - 3):
            stores.append({
                'store_id': f'STORE{str(i+1).zfill(4)}',
                'store_name': f'{random.choice(cities)} {random.choice(["Main", "Central", "Downtown", "Mall"])} Store',
                'store_type': random.choices(['flagship', 'standard', 'outlet'], weights=[10, 70, 20])[0],
                'channel': random.choices(['POS', 'ERP'], weights=[80, 20])[0],
                'region': random.choice(['Northeast', 'Southeast', 'Midwest', 'West', 'Southwest']),
                'city': random.choice(cities),
                'address': self.fake.address().replace('\n', ', '),
                'country': 'USA',
                'opening_date': self.fake.date_between(start_date='-10y', end_date='today'),
                'square_footage': random.randint(5000, 50000),
                'is_active': random.choices([True, False], weights=[95, 5])[0]
            })
        
        # E-commerce stores
        for i in range(3):
            stores.append({
                'store_id': f'ECOM{str(i+1).zfill(4)}',
                'store_name': f'Online Store {i+1}',
                'store_type': 'online',
                'channel': 'E-commerce',
                'region': 'Online',
                'city': 'Online',
                'address': 'Online',
                'country': 'USA',
                'opening_date': self.fake.date_between(start_date='-5y', end_date='today'),
                'square_footage': 0,
                'is_active': True
            })
        
        return pd.DataFrame(stores)
    
    def generate_time_dimension(self, start_date: str = '2020-01-01', 
                               end_date: str = '2025-12-31') -> pd.DataFrame:
        """Generate time dimension data"""
        logger.info(f"Generating time dimension from {start_date} to {end_date}")
        
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        time_data = []
        current = start
        time_key = 1
        
        while current <= end:
            time_data.append({
                'time_key': time_key,
                'full_date': current.date(),
                'day_name': current.strftime('%A'),
                'month_name': current.strftime('%B'),
                'month_num': current.month,
                'quarter': (current.month - 1) // 3 + 1,
                'year': current.year,
                'is_weekend': current.weekday() >= 5,
                'is_holiday': False,  # Simplified
                'week_of_year': current.isocalendar()[1]
            })
            current += timedelta(days=1)
            time_key += 1
        
        return pd.DataFrame(time_data)
    
    def generate_sales_transactions(self, n: int = 50000, 
                                   customers_df: pd.DataFrame = None,
                                   products_df: pd.DataFrame = None,
                                   stores_df: pd.DataFrame = None,
                                   time_df: pd.DataFrame = None) -> pd.DataFrame:
        """Generate sales transaction fact data"""
        logger.info(f"Generating {n} sales transactions")
        
        if customers_df is None or products_df is None or stores_df is None or time_df is None:
            raise ValueError("Customer, product, store, and time DataFrames required")
        
        transactions = []
        start_date = datetime(2024, 1, 1)
        
        for i in range(n):
            # Select random foreign keys
            customer = customers_df.sample(1).iloc[0]
            product = products_df.sample(1).iloc[0]
            store = stores_df.sample(1).iloc[0]
            
            # Generate transaction date (weighted towards recent dates)
            days_ago = int(np.random.exponential(scale=30))
            transaction_date = max(start_date, datetime.now() - timedelta(days=days_ago))
            
            # Get time_key
            time_row = time_df[time_df['full_date'] == transaction_date.date()]
            if time_row.empty:
                time_key = 1
            else:
                time_key = time_row.iloc[0]['time_key']
            
            # Generate transaction details
            quantity = random.randint(1, 5)
            discount_pct = random.choices([0, 5, 10, 15, 20, 25], weights=[40, 20, 15, 12, 8, 5])[0]
            
            unit_price = product['unit_price']
            discount_amount = round(unit_price * quantity * discount_pct / 100, 2)
            net_revenue = round(unit_price * quantity - discount_amount, 2)
            gross_profit = round(net_revenue * product['margin_pct'] / 100, 2)
            
            transactions.append({
                'transaction_id': f'TXN{datetime.now().strftime("%Y%m%d")}{str(i+1).zfill(8)}',
                'transaction_date': transaction_date.date(),
                'time_key': time_key,
                'customer_id': customer['customer_id'],
                'product_id': product['product_id'],
                'store_id': store['store_id'],
                'quantity': quantity,
                'unit_price': unit_price,
                'net_revenue': net_revenue,
                'gross_profit': gross_profit,
                'discount_pct': discount_pct,
                'discount_amount': discount_amount,
                'return_quantity': random.choices([0, 1], weights=[95, 5])[0] if quantity > 1 else 0,
                'source_system': store['channel']
            })
        
        return pd.DataFrame(transactions)
