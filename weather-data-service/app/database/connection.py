"""
Database connection and initialization
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages SQLite database connection and initialization"""
    
    def __init__(self, db_path: str = "data/weather_pool.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection: Optional[sqlite3.Connection] = None
    
    def get_connection(self) -> sqlite3.Connection:
        """Get database connection, creating if necessary"""
        if self._connection is None:
            self._connection = sqlite3.connect(str(self.db_path))
            self._connection.row_factory = sqlite3.Row  # Enable dict-like access
            # Enable foreign key constraints
            self._connection.execute("PRAGMA foreign_keys = ON")
        return self._connection
    
    def initialize_database(self) -> bool:
        """Initialize database with schema"""
        try:
            conn = self.get_connection()
            
            # Read and execute schema
            schema_file = Path(__file__).parent / "schema.sql"
            with open(schema_file, 'r') as f:
                schema_sql = f.read()
            
            conn.executescript(schema_sql)
            conn.commit()
            
            logger.info("Database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            return False
    
    def close(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def __enter__(self):
        return self.get_connection()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.get_connection().rollback()
        else:
            self.get_connection().commit()

# Global database manager instance
db_manager = DatabaseManager()
