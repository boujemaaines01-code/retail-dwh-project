"""
Main ETL Pipeline Entry Point
Run with: python -m etl.run_etl --mode initial|incremental --rows 50000
"""

import argparse
import pandas as pd
import sys
import os
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from etl.utils.logger import setup_logger
from etl.utils.db_connection import DBConnection
from etl.transformers.data_generator import RetailDataGenerator
from etl.transformers.data_cleaner import DataCleaner
from etl.loaders.dwh_loader import DWHLoader

logger = setup_logger('etl_pipeline')


def run_initial_load(num_rows: int, host: str = 'localhost', port: int = 3306):
    """Run initial load of all dimensions and facts"""
    logger.info("=" * 60)
    logger.info("STARTING INITIAL LOAD")
    logger.info("=" * 60)
    
    try:
        # Initialize components
        generator = RetailDataGenerator(seed=42)
        cleaner = DataCleaner()
        loader = DWHLoader(host=host, port=port)
        
        # Start ETL run record
        run_id = loader.start_etl_run('initial', 'ALL')
        total_processed = 0
        total_inserted = 0
        
        # Generate and load dimensions
        logger.info("Step 1: Generate and load time dimension")
        time_df = generator.generate_time_dimension('2020-01-01', '2025-12-31')
        time_df, time_stats = cleaner.clean_time(time_df)
        loader.load_time_dimension(time_df)
        total_processed += time_stats['original_count']
        total_inserted += time_stats['cleaned_count']
        
        logger.info("Step 2: Generate and load customer dimension")
        customers_df = generator.generate_customers(1000)
        customers_df, cust_stats = cleaner.clean_customers(customers_df)
        loader.load_customers(customers_df)
        total_processed += cust_stats['original_count']
        total_inserted += cust_stats['cleaned_count']
        
        logger.info("Step 3: Generate and load product dimension")
        products_df = generator.generate_products(500)
        products_df, prod_stats = cleaner.clean_products(products_df)
        loader.load_products(products_df)
        total_processed += prod_stats['original_count']
        total_inserted += prod_stats['cleaned_count']
        
        logger.info("Step 4: Generate and load store dimension")
        stores_df = generator.generate_stores(50)
        stores_df, store_stats = cleaner.clean_stores(stores_df)
        loader.load_stores(stores_df)
        total_processed += store_stats['original_count']
        total_inserted += store_stats['cleaned_count']
        
        logger.info("Step 5: Generate and load sales facts")
        sales_df = generator.generate_sales_transactions(
            n=num_rows,
            customers_df=customers_df,
            products_df=products_df,
            stores_df=stores_df,
            time_df=time_df
        )
        sales_df, sales_stats = cleaner.clean_sales(
            sales_df, customers_df, products_df, stores_df, time_df
        )
        facts_inserted = loader.load_sales_facts(sales_df)
        total_processed += sales_stats['original_count']
        total_inserted += facts_inserted
        
        # Complete ETL run
        loader.complete_etl_run(run_id, 'completed', total_processed, total_inserted, 0)
        
        logger.info("=" * 60)
        logger.info("INITIAL LOAD COMPLETED SUCCESSFULLY")
        logger.info(f"Total rows processed: {total_processed}")
        logger.info(f"Total rows inserted: {total_inserted}")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Initial load failed: {e}", exc_info=True)
        if 'run_id' in locals():
            loader.complete_etl_run(run_id, 'failed', total_processed, total_inserted, 0, str(e))
        return False
    finally:
        if 'loader' in locals():
            loader.db.disconnect()


def run_incremental_load(num_rows: int, host: str = 'localhost', port: int = 3306):
    """Run incremental load of new transactions"""
    logger.info("=" * 60)
    logger.info("STARTING INCREMENTAL LOAD")
    logger.info("=" * 60)
    
    try:
        # Initialize components
        generator = RetailDataGenerator(seed=int(datetime.now().timestamp()))
        cleaner = DataCleaner()
        loader = DWHLoader(host=host, port=port)
        
        # Start ETL run record
        run_id = loader.start_etl_run('incremental', 'ALL')
        total_processed = 0
        total_inserted = 0
        total_updated = 0
        
        # Load existing dimensions for key resolution
        logger.info("Loading existing dimensions for key resolution")
        
        with loader.db:
            customers_df = pd.DataFrame(loader.db.execute_query("SELECT * FROM dim_customers"))
            products_df = pd.DataFrame(loader.db.execute_query("SELECT * FROM dim_products"))
            stores_df = pd.DataFrame(loader.db.execute_query("SELECT * FROM dim_stores"))
            time_df = pd.DataFrame(loader.db.execute_query("SELECT * FROM dim_time"))
        
        # Generate new sales transactions
        logger.info(f"Generating {num_rows} new sales transactions")
        sales_df = generator.generate_sales_transactions(
            n=num_rows,
            customers_df=customers_df,
            products_df=products_df,
            stores_df=stores_df,
            time_df=time_df
        )
        
        # Clean sales data
        sales_df, sales_stats = cleaner.clean_sales(
            sales_df, customers_df, products_df, stores_df, time_df
        )
        total_processed += sales_stats['original_count']
        
        # Load sales facts
        facts_inserted = loader.load_sales_facts(sales_df)
        total_inserted += facts_inserted
        
        # Complete ETL run
        loader.complete_etl_run(run_id, 'completed', total_processed, total_inserted, total_updated)
        
        logger.info("=" * 60)
        logger.info("INCREMENTAL LOAD COMPLETED SUCCESSFULLY")
        logger.info(f"Total rows processed: {total_processed}")
        logger.info(f"Total rows inserted: {total_inserted}")
        logger.info("=" * 60)
        
        return True
        
    except Exception as e:
        logger.error(f"Incremental load failed: {e}", exc_info=True)
        if 'run_id' in locals():
            loader.complete_etl_run(run_id, 'failed', total_processed, total_inserted, total_updated, str(e))
        return False
    finally:
        if 'loader' in locals():
            loader.db.disconnect()


def main():
    parser = argparse.ArgumentParser(description='Retail Data Warehouse ETL Pipeline')
    parser.add_argument('--mode', type=str, required=True, choices=['initial', 'incremental'],
                        help='ETL mode: initial or incremental')
    parser.add_argument('--rows', type=int, default=50000,
                        help='Number of sales transactions to generate (default: 50000)')
    parser.add_argument('--host', type=str, default='localhost',
                        help='MySQL host (default: localhost)')
    parser.add_argument('--port', type=int, default=3306,
                        help='MySQL port (default: 3306)')
    
    args = parser.parse_args()
    
    if args.mode == 'initial':
        success = run_initial_load(args.rows, args.host, args.port)
    else:
        success = run_incremental_load(args.rows, args.host, args.port)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
