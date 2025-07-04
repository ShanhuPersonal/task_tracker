#!/usr/bin/env python3
"""
Database Migration Script for Task Tracker
==========================================

This script migrates the database from the old structure (parent as string)
to the new structure (parent_id as foreign key).

Usage:
    python3 migrate_database.py

What this script does:
1. Creates the parents table if it doesn't exist
2. Adds parent_id column to users table if it doesn't exist
3. Creates parent records from existing user data
4. Updates users to reference parent_id instead of parent name
5. Removes the old parent column
6. Validates the migration

IMPORTANT: This script should be run on the EC2 server with the production database.
Make sure to backup your database before running this script!
"""

import sys
import os
from sqlalchemy import text, inspect
from datetime import datetime

# Add the current directory to Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from app import create_app
    from models import Parent, User, Task
    from extensions import db
except ImportError as e:
    print(f"❌ Error importing modules: {e}")
    print("Make sure you're running this script from the task_tracker directory")
    sys.exit(1)


def log_message(message):
    """Log a message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def backup_reminder():
    """Remind user to backup database"""
    print("=" * 60)
    print("🚨 IMPORTANT: DATABASE MIGRATION SCRIPT")
    print("=" * 60)
    print("This script will modify your database structure.")
    print("Please ensure you have backed up your database before proceeding!")
    print()
    response = input("Have you backed up your database? (yes/no): ").lower().strip()
    if response not in ['yes', 'y']:
        print("❌ Please backup your database first, then run this script again.")
        sys.exit(1)
    print()


def check_current_structure(db_session):
    """Check the current database structure"""
    log_message("Checking current database structure...")
    
    try:
        inspector = inspect(db_session.bind)
        tables = inspector.get_table_names()
        
        # Check if tables exist
        has_users = 'users' in tables
        has_parents = 'parents' in tables
        
        log_message(f"Tables found: {tables}")
        
        if not has_users:
            log_message("❌ Users table not found!")
            return False
        
        # Check users table structure
        users_columns = [col['name'] for col in inspector.get_columns('users')]
        has_parent_column = 'parent' in users_columns
        has_parent_id_column = 'parent_id' in users_columns
        
        log_message(f"Users table columns: {users_columns}")
        
        return {
            'has_users': has_users,
            'has_parents': has_parents,
            'has_parent_column': has_parent_column,
            'has_parent_id_column': has_parent_id_column,
            'users_columns': users_columns
        }
    except Exception as e:
        log_message(f"Error checking database structure: {e}")
        # Fallback method using direct SQL queries
        try:
            # Check if tables exist using SQL
            result = db_session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result.fetchall()]
            
            has_users = 'users' in tables
            has_parents = 'parents' in tables
            
            if has_users:
                # Check columns using PRAGMA
                result = db_session.execute(text("PRAGMA table_info(users)"))
                columns_info = result.fetchall()
                users_columns = [col[1] for col in columns_info]  # col[1] is the column name
                has_parent_column = 'parent' in users_columns
                has_parent_id_column = 'parent_id' in users_columns
                
                log_message(f"Tables found (fallback): {tables}")
                log_message(f"Users table columns (fallback): {users_columns}")
                
                return {
                    'has_users': has_users,
                    'has_parents': has_parents,
                    'has_parent_column': has_parent_column,
                    'has_parent_id_column': has_parent_id_column,
                    'users_columns': users_columns
                }
            else:
                return False
        except Exception as e2:
            log_message(f"Fallback method also failed: {e2}")
            return False


def create_parents_table(db_session):
    """Create the parents table if it doesn't exist"""
    log_message("Creating parents table...")
    
    try:
        db_session.execute(text("""
            CREATE TABLE IF NOT EXISTS parents (
                id INTEGER PRIMARY KEY,
                name VARCHAR(50) NOT NULL UNIQUE
            )
        """))
        db_session.commit()
        log_message("✅ Parents table created successfully")
        return True
    except Exception as e:
        log_message(f"❌ Error creating parents table: {e}")
        return False


def create_parent_records(db_session):
    """Create parent records from existing user data"""
    log_message("Creating parent records...")
    
    try:
        # Get unique parent names from users table
        result = db_session.execute(text("SELECT DISTINCT parent FROM users WHERE parent IS NOT NULL"))
        parent_names = [row[0] for row in result.fetchall()]
        
        log_message(f"Found parent names: {parent_names}")
        
        # Insert parent records
        for parent_name in parent_names:
            # Check if parent already exists
            existing = db_session.execute(text("SELECT id FROM parents WHERE name = :name"), 
                                        {'name': parent_name}).fetchone()
            if not existing:
                db_session.execute(text("INSERT INTO parents (name) VALUES (:name)"), 
                                 {'name': parent_name})
                log_message(f"✅ Created parent record: {parent_name}")
            else:
                log_message(f"✅ Parent record already exists: {parent_name}")
        
        db_session.commit()
        return True
    except Exception as e:
        log_message(f"❌ Error creating parent records: {e}")
        return False


def add_parent_id_column(db_session):
    """Add parent_id column to users table"""
    log_message("Adding parent_id column to users table...")
    
    try:
        db_session.execute(text("ALTER TABLE users ADD COLUMN parent_id INTEGER"))
        db_session.commit()
        log_message("✅ Added parent_id column successfully")
        return True
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            log_message("✅ parent_id column already exists")
            return True
        else:
            log_message(f"❌ Error adding parent_id column: {e}")
            return False


def update_parent_id_values(db_session):
    """Update parent_id values based on parent names"""
    log_message("Updating parent_id values...")
    
    try:
        # Update users to set parent_id based on parent name
        db_session.execute(text("""
            UPDATE users 
            SET parent_id = (
                SELECT id FROM parents WHERE parents.name = users.parent
            )
            WHERE parent IS NOT NULL
        """))
        db_session.commit()
        
        # Verify the update
        result = db_session.execute(text("""
            SELECT u.name, u.parent, u.parent_id, p.name as parent_name
            FROM users u
            LEFT JOIN parents p ON u.parent_id = p.id
        """))
        
        log_message("Updated user records:")
        for row in result.fetchall():
            log_message(f"  {row[0]}: parent='{row[1]}' -> parent_id={row[2]} ('{row[3]}')")
        
        return True
    except Exception as e:
        log_message(f"❌ Error updating parent_id values: {e}")
        return False


def remove_old_parent_column(db_session):
    """Remove the old parent column (SQLite version)"""
    log_message("Removing old parent column...")
    
    try:
        # For SQLite, we need to recreate the table without the parent column
        # First, get the current data
        result = db_session.execute(text("""
            SELECT id, name, dob, ai_difficulty, parent_id 
            FROM users 
            WHERE parent_id IS NOT NULL
        """))
        users_data = result.fetchall()
        
        log_message(f"Backing up {len(users_data)} user records...")
        
        # Create new table structure
        db_session.execute(text("""
            CREATE TABLE users_new (
                id INTEGER PRIMARY KEY,
                name VARCHAR(50) NOT NULL,
                dob VARCHAR(10) NOT NULL,
                ai_difficulty INTEGER NOT NULL DEFAULT 10,
                parent_id INTEGER NOT NULL,
                FOREIGN KEY (parent_id) REFERENCES parents(id)
            )
        """))
        
        # Copy data to new table
        for user in users_data:
            db_session.execute(text("""
                INSERT INTO users_new (id, name, dob, ai_difficulty, parent_id)
                VALUES (:id, :name, :dob, :ai_difficulty, :parent_id)
            """), {
                'id': user[0],
                'name': user[1],
                'dob': user[2],
                'ai_difficulty': user[3],
                'parent_id': user[4]
            })
        
        # Drop old table and rename new table
        db_session.execute(text("DROP TABLE users"))
        db_session.execute(text("ALTER TABLE users_new RENAME TO users"))
        
        db_session.commit()
        log_message("✅ Successfully removed old parent column")
        return True
    except Exception as e:
        log_message(f"❌ Error removing old parent column: {e}")
        return False


def validate_migration(db_session):
    """Validate that the migration was successful"""
    log_message("Validating migration...")
    
    try:
        # Check that all users have valid parent_id references
        result = db_session.execute(text("""
            SELECT u.id, u.name, u.parent_id, p.name as parent_name
            FROM users u
            LEFT JOIN parents p ON u.parent_id = p.id
            WHERE u.parent_id IS NULL OR p.id IS NULL
        """))
        
        orphaned_users = result.fetchall()
        if orphaned_users:
            log_message(f"❌ Found {len(orphaned_users)} users with invalid parent references:")
            for user in orphaned_users:
                log_message(f"  User {user[1]} (ID: {user[0]}) has parent_id: {user[2]}")
            return False
        
        # Check total counts
        users_count = db_session.execute(text("SELECT COUNT(*) FROM users")).scalar()
        parents_count = db_session.execute(text("SELECT COUNT(*) FROM parents")).scalar()
        tasks_count = db_session.execute(text("SELECT COUNT(*) FROM tasks")).scalar()
        
        log_message("Migration validation results:")
        log_message(f"  ✅ {parents_count} parent(s)")
        log_message(f"  ✅ {users_count} user(s)")
        log_message(f"  ✅ {tasks_count} task(s)")
        log_message("  ✅ All users have valid parent references")
        
        return True
    except Exception as e:
        log_message(f"❌ Error during validation: {e}")
        return False


def main():
    """Main migration function"""
    backup_reminder()
    
    log_message("Starting database migration...")
    
    # Create app and get database session
    app = create_app()
    
    with app.app_context():
        try:
            # Check current structure
            structure = check_current_structure(db.session)
            
            if not structure['has_users']:
                log_message("❌ Users table not found. Cannot proceed with migration.")
                return False
            
            # Check if migration is needed
            if (structure['has_parents'] and 
                structure['has_parent_id_column'] and 
                not structure['has_parent_column']):
                log_message("✅ Database already appears to be migrated!")
                return validate_migration(db.session)
            
            success = True
            
            # Step 1: Create parents table
            if not structure['has_parents']:
                success &= create_parents_table(db.session)
            
            # Step 2: Create parent records
            if success:
                success &= create_parent_records(db.session)
            
            # Step 3: Add parent_id column
            if success and not structure['has_parent_id_column']:
                success &= add_parent_id_column(db.session)
            
            # Step 4: Update parent_id values
            if success:
                success &= update_parent_id_values(db.session)
            
            # Step 5: Remove old parent column
            if success and structure['has_parent_column']:
                success &= remove_old_parent_column(db.session)
            
            # Step 6: Validate migration
            if success:
                success &= validate_migration(db.session)
            
            if success:
                log_message("🎉 Database migration completed successfully!")
                log_message("Your database now uses proper foreign key relationships.")
            else:
                log_message("❌ Database migration failed. Please check the errors above.")
                return False
                
        except Exception as e:
            log_message(f"❌ Unexpected error during migration: {e}")
            return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
