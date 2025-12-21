#!/usr/bin/env python3
"""
Migration: Add check_in_time and check_out_time to attendance table
"""

import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

load_dotenv()

def migrate():
    # Database connection
    conn = psycopg2.connect(
        dbname=os.getenv('DB_NAME', 'face_recognition'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres'),
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432')
    )
    
    try:
        cur = conn.cursor()
        
        print("Adding check_in_time and check_out_time columns to attendance table...")
        
        # Add check_in_time column
        cur.execute("""
            ALTER TABLE attendance 
            ADD COLUMN IF NOT EXISTS check_in_time TIMESTAMP WITH TIME ZONE;
        """)
        
        # Add check_out_time column
        cur.execute("""
            ALTER TABLE attendance 
            ADD COLUMN IF NOT EXISTS check_out_time TIMESTAMP WITH TIME ZONE;
        """)
        
        # Migrate existing data: set check_in_time to marked_at for existing records
        cur.execute("""
            UPDATE attendance 
            SET check_in_time = marked_at 
            WHERE check_in_time IS NULL AND marked_at IS NOT NULL;
        """)
        
        conn.commit()
        print("✅ Successfully added check_in_time and check_out_time columns")
        print("✅ Migrated existing records: check_in_time = marked_at")
        
        # Show sample data
        cur.execute("""
            SELECT id, person_id, date, status, check_in_time, check_out_time 
            FROM attendance 
            LIMIT 5;
        """)
        
        rows = cur.fetchall()
        if rows:
            print("\nSample attendance records:")
            for row in rows:
                print(f"  ID: {row[0]}, Person: {row[1]}, Date: {row[2]}, Status: {row[3]}")
                print(f"    Check-in: {row[4]}, Check-out: {row[5]}")
        
        cur.close()
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
