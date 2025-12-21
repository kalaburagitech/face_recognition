#!/usr/bin/env python3
"""
Migration script to add emp_id, emp_rank, and region fields to existing persons table
"""
import sys
sys.path.insert(0, '.')

from src.models.database import DatabaseManager
from sqlalchemy import text

def migrate_add_emp_fields():
    """Add emp_id, emp_rank, and region columns to persons table if they don't exist"""
    db = DatabaseManager()
    
    print("=" * 60)
    print("Migration: Add Employee Fields to Persons Table")
    print("=" * 60)
    
    try:
        with db.get_session() as session:
            # Check if columns exist
            result = session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'persons' 
                AND column_name IN ('emp_id', 'emp_rank', 'region')
            """))
            existing_columns = [row[0] for row in result]
            
            print(f"\nExisting columns: {existing_columns}")
            
            # Add missing columns
            if 'region' not in existing_columns:
                print("\n✓ Adding 'region' column...")
                session.execute(text("""
                    ALTER TABLE persons 
                    ADD COLUMN region VARCHAR(50) DEFAULT 'ka' NOT NULL
                """))
                session.execute(text("""
                    CREATE INDEX idx_persons_region ON persons(region)
                """))
                print("  ✓ Added 'region' column with default 'ka'")
            
            if 'emp_id' not in existing_columns:
                print("\n✓ Adding 'emp_id' column...")
                # First add as nullable
                session.execute(text("""
                    ALTER TABLE persons 
                    ADD COLUMN emp_id VARCHAR(100)
                """))
                
                # Generate emp_id for existing records
                session.execute(text("""
                    UPDATE persons 
                    SET emp_id = 'EMP' || LPAD(id::text, 6, '0')
                    WHERE emp_id IS NULL
                """))
                
                # Make it NOT NULL and UNIQUE
                session.execute(text("""
                    ALTER TABLE persons 
                    ALTER COLUMN emp_id SET NOT NULL
                """))
                session.execute(text("""
                    ALTER TABLE persons 
                    ADD CONSTRAINT persons_emp_id_key UNIQUE (emp_id)
                """))
                session.execute(text("""
                    CREATE INDEX idx_persons_emp_id ON persons(emp_id)
                """))
                print("  ✓ Added 'emp_id' column with auto-generated IDs")
            
            if 'emp_rank' not in existing_columns:
                print("\n✓ Adding 'emp_rank' column...")
                session.execute(text("""
                    ALTER TABLE persons 
                    ADD COLUMN emp_rank VARCHAR(100) DEFAULT 'Staff' NOT NULL
                """))
                session.execute(text("""
                    CREATE INDEX idx_persons_emp_rank ON persons(emp_rank)
                """))
                print("  ✓ Added 'emp_rank' column with default 'Staff'")
            
            # Add composite indexes if they don't exist
            print("\n✓ Adding composite indexes...")
            try:
                session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_person_region_client 
                    ON persons(region, client_id)
                """))
                session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_person_name_region 
                    ON persons(name, region)
                """))
                print("  ✓ Added composite indexes")
            except Exception as e:
                print(f"  ⚠ Indexes might already exist: {e}")
            
            session.commit()
            
            print("\n" + "=" * 60)
            print("✅ Migration completed successfully!")
            print("=" * 60)
            
            # Show updated schema
            result = session.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns 
                WHERE table_name = 'persons'
                ORDER BY ordinal_position
            """))
            
            print("\nUpdated persons table schema:")
            print("-" * 60)
            for row in result:
                print(f"  {row[0]:20} {row[1]:20} NULL={row[2]:5} DEFAULT={row[3]}")
            print("-" * 60)
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = migrate_add_emp_fields()
    sys.exit(0 if success else 1)
