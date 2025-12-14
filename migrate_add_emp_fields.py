"""
Migration script to add emp_id and emp_rank columns to existing persons table
Run this ONCE before using the updated system
"""
from sqlalchemy import create_engine, text
import sys

# Database URL - Update if needed
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/face_recognition"

def migrate_database():
    """Add emp_id and emp_rank columns to persons table"""
    try:
        engine = create_engine(DATABASE_URL)
        
        with engine.connect() as conn:
            print("Adding emp_id column...")
            try:
                conn.execute(text("ALTER TABLE persons ADD COLUMN emp_id VARCHAR(100)"))
                conn.commit()
                print("✓ emp_id column added")
            except Exception as e:
                if "already exists" in str(e):
                    print("✓ emp_id column already exists")
                else:
                    raise
            
            print("Adding emp_rank column...")
            try:
                conn.execute(text("ALTER TABLE persons ADD COLUMN emp_rank VARCHAR(100)"))
                conn.commit()
                print("✓ emp_rank column added")
            except Exception as e:
                if "already exists" in str(e):
                    print("✓ emp_rank column already exists")
                else:
                    raise
            
            # Update existing records with dummy values
            print("Updating existing records with placeholder values...")
            conn.execute(text("UPDATE persons SET emp_id = 'EMP' || id::text WHERE emp_id IS NULL"))
            conn.execute(text("UPDATE persons SET emp_rank = 'Staff' WHERE emp_rank IS NULL"))
            conn.commit()
            print("✓ Existing records updated")
            
            # Make columns NOT NULL
            print("Making columns NOT NULL...")
            conn.execute(text("ALTER TABLE persons ALTER COLUMN emp_id SET NOT NULL"))
            conn.execute(text("ALTER TABLE persons ALTER COLUMN emp_rank SET NOT NULL"))
            conn.commit()
            print("✓ Columns set to NOT NULL")
            
            # Add unique constraint to emp_id
            print("Adding unique constraint to emp_id...")
            try:
                conn.execute(text("ALTER TABLE persons ADD CONSTRAINT persons_emp_id_key UNIQUE (emp_id)"))
                conn.commit()
                print("✓ Unique constraint added")
            except Exception as e:
                if "already exists" in str(e):
                    print("✓ Unique constraint already exists")
                else:
                    raise
            
            # Add indexes
            print("Adding indexes...")
            try:
                conn.execute(text("CREATE INDEX idx_persons_emp_id ON persons(emp_id)"))
                conn.commit()
                print("✓ emp_id index added")
            except Exception as e:
                if "already exists" in str(e):
                    print("✓ emp_id index already exists")
                else:
                    raise
            
            try:
                conn.execute(text("CREATE INDEX idx_persons_emp_rank ON persons(emp_rank)"))
                conn.commit()
                print("✓ emp_rank index added")
            except Exception as e:
                if "already exists" in str(e):
                    print("✓ emp_rank index already exists")
                else:
                    raise
        
        print("\n✅ Migration completed successfully!")
        print("You can now use the updated system with emp_id and emp_rank fields.")
        
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    migrate_database()
