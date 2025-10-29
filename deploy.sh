#!/bin/bash

# Exit on any error
set -e

echo "=========================================="
echo "Starting deployment..."
echo "=========================================="

# Pull latest code (force reset to match GitHub exactly)
echo "Pulling latest code from GitHub..."
git fetch origin
git reset --hard origin/main

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/Update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Restart Gunicorn service
echo "Restarting Gunicorn service..."
sudo systemctl restart gunicorn

# Restart Nginx service
echo "Restarting Nginx service..."
sudo systemctl restart nginx

# Check services status
echo "Checking service status..."
sudo systemctl status gunicorn --no-pager
sudo systemctl status nginx --no-pager

echo "=========================================="
echo "Deployment completed successfully!"
echo "=========================================="

