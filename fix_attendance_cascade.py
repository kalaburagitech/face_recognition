#!/usr/bin/env python3
"""
Fix attendance table foreign key to use CASCADE delete
"""
import sys
import os
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from src.utils.config import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_cascade():
    """Fix the foreign key constraint to use CASCADE"""
    try:
        db_url = config.get('database.url', 'postgresql://postgres:postgres@localhost:5432/face_recognition')
        
        logger.info(f"Connecting to database...")
        engine = create_engine(db_url)
        
        with engine.connect() as conn:
            # Drop the existing foreign key constraint
            logger.info("Dropping old foreign key constraint...")
            conn.execute(text("""
                ALTER TABLE attendance 
                DROP CONSTRAINT IF EXISTS attendance_person_id_fkey;
            """))
            conn.commit()
            
            # Add new foreign key with CASCADE delete
            logger.info("Adding new foreign key with CASCADE delete...")
            conn.execute(text("""
                ALTER TABLE attendance 
                ADD CONSTRAINT attendance_person_id_fkey 
                FOREIGN KEY (person_id) 
                REFERENCES persons(id) 
                ON DELETE CASCADE;
            """))
            conn.commit()
            
            logger.info("✓ Foreign key constraint fixed successfully!")
            
            # Verify the constraint
            result = conn.execute(text("""
                SELECT conname, confdeltype 
                FROM pg_constraint 
                WHERE conname = 'attendance_person_id_fkey';
            """))
            
            for row in result:
                logger.info(f"✓ Constraint verified: {row[0]}, Delete action: {row[1]} (c=CASCADE)")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = fix_cascade()
    sys.exit(0 if success else 1)
