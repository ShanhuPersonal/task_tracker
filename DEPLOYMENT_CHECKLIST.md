# EC2 Deployment Checklist

## Pre-Deployment Checklist

- [ ] **CRITICAL: Backup your database**
  ```bash
  cp instance/task_tracker.db instance/task_tracker.db.backup.$(date +%Y%m%d_%H%M%S)
  ```

- [ ] **Stop the running application on EC2**
  ```bash
  sudo systemctl stop task-tracker
  # OR
  pkill -f "python.*app.py"
  ```

- [ ] **Update EC2 connection details in deploy script**
  - EC2 host (e.g., ec2-xxx-xxx-xxx-xxx.compute-1.amazonaws.com)
  - SSH user (usually 'ubuntu' or 'ec2-user')
  - SSH key path (e.g., ~/.ssh/your-key.pem)

## Deployment Commands

### Option 1: Automated Deployment
```bash
# Update the script with your EC2 details, then run:
./deploy_to_ec2.sh your-ec2-host.amazonaws.com ubuntu ~/.ssh/your-key.pem
```

### Option 2: Manual Upload
```bash
# Upload migration script
scp -i ~/.ssh/your-key.pem migrate_database.py ubuntu@your-ec2-host:/home/ubuntu/task_tracker/

# Upload updated application files
scp -i ~/.ssh/your-key.pem models.py ubuntu@your-ec2-host:/home/ubuntu/task_tracker/
scp -i ~/.ssh/your-key.pem routes/parent.py ubuntu@your-ec2-host:/home/ubuntu/task_tracker/routes/
scp -i ~/.ssh/your-key.pem templates/parent.html ubuntu@your-ec2-host:/home/ubuntu/task_tracker/templates/
scp -i ~/.ssh/your-key.pem app.py ubuntu@your-ec2-host:/home/ubuntu/task_tracker/
```

## On EC2 Server

### 1. SSH into EC2
```bash
ssh -i ~/.ssh/your-key.pem ubuntu@your-ec2-host
```

### 2. Navigate to Task Tracker Directory
```bash
cd /home/ubuntu/task_tracker  # Adjust path as needed
```

### 3. Make Migration Script Executable
```bash
chmod +x migrate_database.py
```

### 4. Run Migration
```bash
python3 migrate_database.py
```

### 5. Test Application
```bash
python3 app.py
# Test in browser: http://your-ec2-host:5000/parent
# Press Ctrl+C to stop test
```

### 6. Restart Service
```bash
sudo systemctl start task-tracker
# OR
nohup python3 app.py > app.log 2>&1 &
```

## Post-Deployment Verification

- [ ] **Parent page loads correctly**
  - Visit: `http://your-ec2-host:5000/parent`

- [ ] **User management works**
  - Can see existing users
  - Can edit user details
  - Can add new users

- [ ] **Task management works**
  - Can view tasks for each user
  - Can add/edit/delete tasks
  - Can copy tasks between users

- [ ] **Database integrity**
  - All existing data is preserved
  - Foreign key relationships work

## Rollback Plan (If Needed)

If something goes wrong:

```bash
# Stop the application
sudo systemctl stop task-tracker

# Restore database from backup
cp instance/task_tracker.db.backup.YYYYMMDD_HHMMSS instance/task_tracker.db

# Restore code files from backup directory (created by deploy script)
cp backup/YYYYMMDD_HHMMSS/* ./

# Restart application
sudo systemctl start task-tracker
```

## Troubleshooting

### Common Issues:

1. **Permission denied on migration script**
   ```bash
   chmod +x migrate_database.py
   ```

2. **Import errors**
   ```bash
   # Make sure you're in the correct directory
   ls -la  # Should see app.py, models.py, etc.
   ```

3. **Database locked**
   ```bash
   # Make sure the application is stopped
   sudo systemctl stop task-tracker
   pkill -f python
   ```

4. **Missing dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```

### Success Indicators:

✅ Migration script completes without errors
✅ All tests pass in the migration validation
✅ Parent page loads and shows users
✅ Can add new users with date picker
✅ Can copy tasks between users
✅ All existing tasks are preserved

## New Features Available After Migration:

1. **Enhanced User Management**
   - Add new users directly in parent portal
   - Edit users with proper date picker for DOB
   - AI difficulty defaults to 10 with validation

2. **Task Copying**
   - Copy all tasks from one user to another
   - Automatic duplicate prevention
   - Preserves all task properties

3. **Better Database Structure**
   - Proper foreign key relationships
   - Improved data integrity
   - Better performance for queries
