"""
Database Connection Manager for MySQL NDB Cluster
Handles connection pooling and retry logic
"""

import mysql.connector
from mysql.connector import Error
import time
import logging
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)


class DBConnection:
    """MySQL NDB Cluster connection manager with retry logic"""
    
    def __init__(self, host: str = 'localhost', port: int = 3306,
                 user: str = None, password: str = None,
                 database: str = 'retail_dwh', max_retries: int = 3):
        self.host = host
        self.port = port
        self.user = user or os.getenv('MYSQL_USER', 'dwh_user')
        self.password = password or os.getenv('MYSQL_PASSWORD', 'dwh_dev_pass_2024')
        self.database = database
        self.max_retries = max_retries
        self.connection = None
        
    def connect(self) -> mysql.connector.MySQLConnection:
        """Establish connection with retry logic"""
        for attempt in range(self.max_retries):
            try:
                self.connection = mysql.connector.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    charset='utf8mb4',
                    use_pure=True
                )
                logger.info(f"Successfully connected to MySQL NDB Cluster at {self.host}:{self.port}")
                return self.connection
            except Error as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to connect after {self.max_retries} attempts")
                    raise
                    
    def disconnect(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Database connection closed")
            
    def execute_query(self, query: str, params: tuple = None) -> Optional[list]:
        """Execute a SELECT query and return results"""
        if not self.connection or not self.connection.is_connected():
            self.connect()
            
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            return result
        except Error as e:
            logger.error(f"Query execution failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
                
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows"""
        if not self.connection or not self.connection.is_connected():
            self.connect()
            
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, params or ())
            self.connection.commit()
            affected = cursor.rowcount
            logger.debug(f"Query executed, {affected} rows affected")
            return affected
        except Error as e:
            self.connection.rollback()
            logger.error(f"Update query failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
                
    def execute_batch(self, query: str, data: list, batch_size: int = 1000) -> int:
        """Execute batch insert with multiple rows"""
        if not self.connection or not self.connection.is_connected():
            self.connect()
            
        cursor = None
        total_affected = 0
        try:
            cursor = self.connection.cursor()
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                cursor.executemany(query, batch)
                self.connection.commit()
                total_affected += cursor.rowcount
                logger.debug(f"Batch {i//batch_size + 1}: {cursor.rowcount} rows inserted")
            return total_affected
        except Error as e:
            self.connection.rollback()
            logger.error(f"Batch insert failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
                
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
