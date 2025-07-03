#!/bin/bash

echo "Stopping any running Flask app..."
# Kill any python process running app.py
pkill -f app.py

# Optional: small delay to ensure processes are stopped
sleep 2

echo "Starting Flask app..."
# Start Flask with nohup in background
nohup /home/ec2-user/miniconda3/envs/py313/bin/python app.py &

echo "Flask app restarted. Logs are in nohup.out"

