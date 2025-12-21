#!/usr/bin/env python3
"""
Migration: Add analytics_log table for tracking system events
"""

import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

load_dotenv()

def migrate():
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME', 'face_recognition'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres'),
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432')
    )
    
    try:
        cur = conn.cursor()
        
        print("Creating analytics_log table...")
        
        # Create analytics_log table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS analytics_log (
                id SERIAL PRIMARY KEY,
                event_type VARCHAR(50) NOT NULL,
                person_id INTEGER REFERENCES persons(id) ON DELETE CASCADE,
                emp_id VARCHAR(100),
                name VARCHAR(255),
                region VARCHAR(50),
                timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
                date DATE NOT NULL,
                metadata JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
        
        # Create indexes for fast queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_analytics_log_event_type 
            ON analytics_log(event_type);
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_analytics_log_date 
            ON analytics_log(date);
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_analytics_log_emp_id 
            ON analytics_log(emp_id);
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_analytics_log_region 
            ON analytics_log(region);
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_analytics_log_timestamp 
            ON analytics_log(timestamp);
        """)
        
        # Create composite index for common queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_analytics_log_date_event 
            ON analytics_log(date, event_type);
        """)
        
        conn.commit()
        print("✅ Successfully created analytics_log table with indexes")
        
        # Show table structure
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'analytics_log'
            ORDER BY ordinal_position;
        """)
        
        print("\nTable structure:")
        for row in cur.fetchall():
            print(f"  {row[0]}: {row[1]} (nullable: {row[2]})")
        
        cur.close()
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
