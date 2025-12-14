#!/usr/bin/env python3
"""
Migration script to add attendance table
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from src.utils.config import config
from src.models.database import Base, Attendance
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    """Add attendance table to database"""
    try:
        # Get database URL
        db_url = config.get('database.url', 'postgresql://postgres:postgres@localhost:5432/face_recognition')
        
        logger.info(f"Connecting to database...")
        engine = create_engine(db_url)
        
        # Create attendance table
        logger.info("Creating attendance table...")
        Attendance.__table__.create(engine, checkfirst=True)
        
        logger.info("✓ Attendance table created successfully!")
        
        # Verify table exists
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM attendance"))
            count = result.scalar()
            logger.info(f"✓ Attendance table verified (current records: {count})")
        
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
