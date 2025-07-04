# EC2 Database Migration Guide

## Overview
This guide helps you update the Task Tracker database structure on your EC2 server from the old parent name system to the new parent_id foreign key system.

## Prerequisites
- SSH access to your EC2 server
- Python 3 and pip installed on EC2
- Current Task Tracker application running
- **BACKUP YOUR DATABASE FIRST!**

## Method 1: Automated Migration (Recommended)

### Step 1: Upload Files to EC2
```bash
# Make the deployment script executable
chmod +x deploy_to_ec2.sh

# Run the deployment script (update with your actual EC2 details)
./deploy_to_ec2.sh your-ec2-host.amazonaws.com ubuntu ~/.ssh/your-key.pem
```

### Step 2: SSH into EC2 and Run Migration
```bash
# SSH into your EC2 server
ssh -i ~/.ssh/your-key.pem ubuntu@your-ec2-host.amazonaws.com

# Navigate to task tracker directory
cd /home/ubuntu/task_tracker

# Stop the running application
sudo systemctl stop task-tracker
# OR if running manually:
# pkill -f "python.*app.py"

# Run the migration script
python3 migrate_database.py

# Test the application
python3 app.py

# If everything works, restart the service
sudo systemctl start task-tracker
```

## Method 2: Manual Migration

### Step 1: Upload Files Manually
```bash
# Upload required files
scp -i ~/.ssh/your-key.pem migrate_database.py ubuntu@your-ec2-host:/home/ubuntu/task_tracker/
scp -i ~/.ssh/your-key.pem models.py ubuntu@your-ec2-host:/home/ubuntu/task_tracker/
scp -i ~/.ssh/your-key.pem routes/parent.py ubuntu@your-ec2-host:/home/ubuntu/task_tracker/routes/
scp -i ~/.ssh/your-key.pem templates/parent.html ubuntu@your-ec2-host:/home/ubuntu/task_tracker/templates/
scp -i ~/.ssh/your-key.pem app.py ubuntu@your-ec2-host:/home/ubuntu/task_tracker/
```

### Step 2: Run Migration on EC2
```bash
# SSH into server
ssh -i ~/.ssh/your-key.pem ubuntu@your-ec2-host

# Navigate to directory
cd /home/ubuntu/task_tracker

# Backup database
cp instance/task_tracker.db instance/task_tracker.db.backup.$(date +%Y%m%d_%H%M%S)

# Stop application
sudo systemctl stop task-tracker

# Run migration
python3 migrate_database.py

# Test application
python3 app.py
```

## Method 3: Step-by-Step SQL Migration

If the automated script doesn't work, you can run these SQL commands manually:

### Step 1: Connect to Database
```bash
cd /home/ubuntu/task_tracker
sqlite3 instance/task_tracker.db
```

### Step 2: Run SQL Commands
```sql
-- Create parents table
CREATE TABLE IF NOT EXISTS parents (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

-- Insert parent records
INSERT OR IGNORE INTO parents (name) 
SELECT DISTINCT parent FROM users WHERE parent IS NOT NULL;

-- Add parent_id column
ALTER TABLE users ADD COLUMN parent_id INTEGER;

-- Update parent_id values
UPDATE users 
SET parent_id = (SELECT id FROM parents WHERE parents.name = users.parent)
WHERE parent IS NOT NULL;

-- Check the update worked
SELECT u.name, u.parent, u.parent_id, p.name as parent_name
FROM users u
LEFT JOIN parents p ON u.parent_id = p.id;

-- For SQLite, we need to recreate the table to remove the old parent column
-- (This is complex, so use the Python script for this step)
```

### Step 3: Exit and Test
```sql
.exit
```

```bash
# Test the application
python3 app.py
```

## Verification

After migration, verify these things work:
1. Parent page loads: `http://your-server:5000/parent`
2. Users are displayed correctly
3. You can add new users
4. You can copy tasks between users
5. All existing tasks are still there

## Rollback (If Needed)

If something goes wrong:
```bash
# Stop the application
sudo systemctl stop task-tracker

# Restore from backup
cp instance/task_tracker.db.backup.YYYYMMDD_HHMMSS instance/task_tracker.db

# Restore old code files from backup directory
cp backup/YYYYMMDD_HHMMSS/* ./

# Restart application
sudo systemctl start task-tracker
```

## New Features After Migration

Once migrated, you'll have these new features:
- ✅ Add new users in parent portal
- ✅ Edit existing users with date picker for DOB
- ✅ Copy tasks from one user to another
- ✅ Proper database relationships with foreign keys
- ✅ Better data integrity and performance

## Support

If you encounter issues:
1. Check the migration script output for error messages
2. Verify all required Python packages are installed
3. Ensure database file permissions are correct
4. Check that the Flask app can import all required modules

## Database Schema Changes

**Before Migration:**
```
users: id, name, dob, ai_difficulty, parent (string)
```

**After Migration:**
```
parents: id, name
users: id, name, dob, ai_difficulty, parent_id (foreign key)
```
