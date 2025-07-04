#!/bin/bash

# EC2 Deployment Script for Task Tracker Database Migration
# =========================================================
# 
# This script helps deploy the database migration to EC2 server
# 
# Usage: ./deploy_to_ec2.sh [EC2_HOST] [EC2_USER]
# Example: ./deploy_to_ec2.sh ec2-xxx-xxx-xxx-xxx.compute-1.amazonaws.com ubuntu

set -e  # Exit on any error

# Configuration
EC2_HOST=${1:-"your-ec2-host.amazonaws.com"}
EC2_USER=${2:-"ubuntu"}
KEY_FILE=${3:-"~/.ssh/your-key.pem"}
REMOTE_PATH="/home/$EC2_USER/task_tracker"

echo "🚀 Starting EC2 deployment..."
echo "Host: $EC2_HOST"
echo "User: $EC2_USER"
echo "Remote path: $REMOTE_PATH"
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required files exist locally
print_step "Checking local files..."
required_files=("migrate_database.py" "models.py" "routes/parent.py" "templates/parent.html" "app.py")

for file in "${required_files[@]}"; do
    if [[ ! -f "$file" ]]; then
        print_error "Required file not found: $file"
        exit 1
    fi
done

print_step "✅ All required files found locally"

# Upload files to EC2
print_step "Uploading files to EC2..."

# Create backup directory on remote server
ssh -i "$KEY_FILE" "$EC2_USER@$EC2_HOST" "
    cd $REMOTE_PATH && 
    mkdir -p backup/\$(date +%Y%m%d_%H%M%S) &&
    echo 'Created backup directory'
"

# Backup current files
ssh -i "$KEY_FILE" "$EC2_USER@$EC2_HOST" "
    cd $REMOTE_PATH &&
    backup_dir=\"backup/\$(date +%Y%m%d_%H%M%S)\" &&
    cp -r models.py routes/parent.py templates/parent.html app.py \"\$backup_dir/\" 2>/dev/null || true &&
    echo 'Backed up existing files to '\$backup_dir
"

# Upload new files
scp -i "$KEY_FILE" migrate_database.py "$EC2_USER@$EC2_HOST:$REMOTE_PATH/"
scp -i "$KEY_FILE" models.py "$EC2_USER@$EC2_HOST:$REMOTE_PATH/"
scp -i "$KEY_FILE" routes/parent.py "$EC2_USER@$EC2_HOST:$REMOTE_PATH/routes/"
scp -i "$KEY_FILE" templates/parent.html "$EC2_USER@$EC2_HOST:$REMOTE_PATH/templates/"
scp -i "$KEY_FILE" app.py "$EC2_USER@$EC2_HOST:$REMOTE_PATH/"

print_step "✅ Files uploaded successfully"

# Make migration script executable
ssh -i "$KEY_FILE" "$EC2_USER@$EC2_HOST" "
    cd $REMOTE_PATH &&
    chmod +x migrate_database.py &&
    echo 'Made migration script executable'
"

print_step "✅ Migration script is ready"

echo
echo "🎉 Deployment completed successfully!"
echo
echo "Next steps:"
echo "1. SSH into your EC2 server:"
echo "   ssh -i $KEY_FILE $EC2_USER@$EC2_HOST"
echo
echo "2. Navigate to the task tracker directory:"
echo "   cd $REMOTE_PATH"
echo
echo "3. Stop the running application (if any):"
echo "   sudo systemctl stop task-tracker  # or kill the process"
echo
echo "4. Run the database migration:"
echo "   python3 migrate_database.py"
echo
echo "5. Test the application:"
echo "   python3 app.py"
echo
echo "6. Restart the service:"
echo "   sudo systemctl start task-tracker"
echo
print_warning "IMPORTANT: Make sure to backup your database before running the migration!"
