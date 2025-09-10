#!/usr/bin/env python3
"""
Create a fresh database with schema v2
No migration needed - start clean with the new structure
"""

import sqlite3
import os

def create_fresh_database():
    """Create a fresh database with schema v2"""
    
    # Remove old database if it exists
    db_path = "data/weather_pool.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print("🗑️  Removed old database")
    
    # Ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    # Create new database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Read and execute schema
        with open('app/database/schema_v2.sql', 'r') as f:
            schema_sql = f.read()
        
        statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
        for statement in statements:
            if statement:
                cursor.execute(statement)
        
        conn.commit()
        print("✅ Fresh database created with schema v2")
        
        # Verify tables were created
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📊 Tables created: {', '.join(tables)}")
        
    except Exception as e:
        print(f"❌ Failed to create database: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    create_fresh_database()
