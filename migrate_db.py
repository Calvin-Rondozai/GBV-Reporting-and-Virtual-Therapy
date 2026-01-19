"""
Database migration script to add new columns to the reports table.
Run this script once to update your existing database schema.
"""
from app import app
from database import db, Report
from sqlalchemy import text

def migrate_database():
    """Add new columns to reports table if they don't exist"""
    with app.app_context():
        try:
            # Check if new columns exist by trying to query them
            db.session.execute(text("SELECT type_of_abuse FROM reports LIMIT 1"))
            print("Database schema is up to date. No migration needed.")
            return
        except Exception:
            # Columns don't exist, need to add them
            print("Adding new columns to reports table...")
            pass
        
        try:
            # Add new columns one by one with error handling
            columns_to_add = [
                ("type_of_abuse", "VARCHAR(200)"),
                ("gender_of_abuser", "VARCHAR(50)"),
                ("still_in_danger", "VARCHAR(20)"),
                ("relationship_with_abuser", "VARCHAR(200)"),
                ("what_happened", "TEXT"),
            ]
            
            for column_name, column_type in columns_to_add:
                try:
                    db.session.execute(text(f"ALTER TABLE reports ADD COLUMN {column_name} {column_type}"))
                    print(f"✓ Added column: {column_name}")
                except Exception as e:
                    if "duplicate column" in str(e).lower() or "already exists" in str(e).lower():
                        print(f"  Column {column_name} already exists, skipping...")
                    else:
                        print(f"  Warning: Could not add {column_name}: {e}")
            
            db.session.commit()
            print("\n✅ Database migration completed successfully!")
            print("You can now use the updated report system.")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during migration: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    print("Starting database migration...")
    migrate_database()
