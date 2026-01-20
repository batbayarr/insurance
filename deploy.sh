#!/bin/bash

# Exit on any error
set -e

echo "=========================================="
echo "Starting deployment..."
echo "=========================================="

# Note: Git operations are handled by the workflow, so we skip them here

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/Update Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Install/Update Node dependencies (uses package-lock.json if present)
if command -v npm >/dev/null 2>&1; then
  if [ -f package-lock.json ]; then
    echo "Installing Node dependencies with npm ci..."
    npm ci || npm install
  else
    echo "Installing Node dependencies with npm install..."
    npm install
  fi
else
  echo "WARNING: npm not found. Skipping Node.js steps. Install Node.js if you need CSS building."
  echo "Continuing with Python-only deployment..."
fi

# Build Tailwind CSS bundle (if npm is available)
if command -v npm >/dev/null 2>&1 && [ -f "package.json" ]; then
  echo "Building Tailwind CSS..."
  npm run build:css || echo "WARNING: CSS build failed, continuing..."
  
  # Verify CSS file was built
  if [ ! -f "core/static/css/tailwind.build.css" ]; then
      echo "WARNING: tailwind.build.css was not created, but continuing..."
  else
      echo "✓ Tailwind CSS built successfully"
  fi
else
  echo "Skipping CSS build (npm not available or no package.json)"
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Verify CSS file was collected (if it exists)
if [ -f "staticfiles/css/tailwind.build.css" ]; then
    echo "✓ Static files collected successfully"
else
    echo "WARNING: tailwind.build.css not found in staticfiles, but continuing..."
fi

# Run database migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Restart Gunicorn service (if it exists)
if systemctl list-unit-files | grep -q gunicorn.service; then
  echo "Restarting Gunicorn service..."
  sudo systemctl restart gunicorn || echo "WARNING: Gunicorn restart failed"
else
  echo "WARNING: Gunicorn service not found. Install it with: sudo cp gunicorn.service /etc/systemd/system/ && sudo systemctl daemon-reload"
fi

# Restart Nginx service
echo "Restarting Nginx service..."
sudo systemctl restart nginx || echo "WARNING: Nginx restart failed"

# Check services status (non-blocking)
echo "Checking service status..."
sudo systemctl status gunicorn --no-pager || true
sudo systemctl status nginx --no-pager || true

echo "=========================================="
echo "Deployment completed successfully!"
echo "=========================================="