#!/usr/bin/env python3
"""
Migration: Add location coordinates to attendance table
"""
import psycopg2
from psycopg2 import sql

def migrate():
    """Add check-in and check-out location columns"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            dbname='face_recognition',
            user='postgres',
            password='postgres',
            host='localhost',
            port='5432'
        )
        
        cur = conn.cursor()
        
        print("Adding location columns to attendance table...")
        
        # Add check-in location columns
        cur.execute("""
            ALTER TABLE attendance 
            ADD COLUMN IF NOT EXISTS check_in_latitude DOUBLE PRECISION,
            ADD COLUMN IF NOT EXISTS check_in_longitude DOUBLE PRECISION,
            ADD COLUMN IF NOT EXISTS check_in_location_accuracy DOUBLE PRECISION;
        """)
        
        # Add check-out location columns
        cur.execute("""
            ALTER TABLE attendance 
            ADD COLUMN IF NOT EXISTS check_out_latitude DOUBLE PRECISION,
            ADD COLUMN IF NOT EXISTS check_out_longitude DOUBLE PRECISION,
            ADD COLUMN IF NOT EXISTS check_out_location_accuracy DOUBLE PRECISION;
        """)
        
        # Create index for location queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_attendance_checkin_location 
            ON attendance(check_in_latitude, check_in_longitude);
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_attendance_checkout_location 
            ON attendance(check_out_latitude, check_out_longitude);
        """)
        
        conn.commit()
        print("✅ Successfully added location columns to attendance table")
        
        # Show table structure
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'attendance'
            ORDER BY ordinal_position;
        """)
        
        print("\n📋 Updated attendance table structure:")
        for row in cur.fetchall():
            print(f"  - {row[0]}: {row[1]} (nullable: {row[2]})")
        
        cur.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Migration: Add Location Tracking to Attendance")
    print("=" * 60)
    migrate()
