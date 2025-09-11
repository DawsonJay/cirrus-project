import os
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse

def get_database_connection():
    """Get database connection for both SQLite (local) and PostgreSQL (Railway)"""
    
    # Check if we're running on Railway (PostgreSQL)
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        # Parse the DATABASE_URL for PostgreSQL
        parsed_url = urlparse(database_url)
        
        conn = psycopg2.connect(
            host=parsed_url.hostname,
            port=parsed_url.port,
            database=parsed_url.path[1:],  # Remove leading slash
            user=parsed_url.username,
            password=parsed_url.password,
            sslmode='require'
        )
        return conn
    
    # Fallback to SQLite for local development
    import sqlite3
    db_path = os.getenv('DATABASE_PATH', 'data/weather_pool.db')
    return sqlite3.connect(db_path)

def get_cursor():
    """Get database cursor with appropriate configuration"""
    conn = get_database_connection()
    
    # Check if it's PostgreSQL
    if hasattr(conn, 'cursor'):
        # PostgreSQL
        return conn.cursor(cursor_factory=RealDictCursor)
    else:
        # SQLite
        conn.row_factory = sqlite3.Row
        return conn.cursor()
