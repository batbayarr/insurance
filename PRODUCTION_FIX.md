# Production CSS Fix - Quick Guide

## Issue
404 error for `/static/css/tailwind.build.css` on production server (45.32.55.203)

## Solution

### Step 1: SSH into Production Server
```bash
ssh your_user@45.32.55.203
```

### Step 2: Navigate to Application Directory
```bash
cd /var/www/silicon4_accounting
```

### Step 3: Run Deployment Script
```bash
./deploy.sh
```

This will:
- Pull latest code from GitHub
- Build Tailwind CSS (`npm run build:css`)
- Collect static files (`python manage.py collectstatic`)
- Verify CSS file exists
- Restart services

### Step 4: Update Nginx Configuration
```bash
# Copy the updated nginx.conf
sudo cp nginx.conf /etc/nginx/sites-available/silicon4_accounting

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

### Step 5: Verify File Exists
```bash
# Check if CSS file was built
ls -la core/static/css/tailwind.build.css

# Check if CSS file was collected
ls -la staticfiles/css/tailwind.build.css

# Check nginx can access it
ls -la /var/www/silicon4_accounting/staticfiles/css/tailwind.build.css
```

### Step 6: Check File Permissions
```bash
# Ensure nginx can read the files
sudo chown -R silicon4:www-data /var/www/silicon4_accounting/staticfiles
sudo chmod -R 755 /var/www/silicon4_accounting/staticfiles
```

### Step 7: Test in Browser
1. Open: `http://45.32.55.203`
2. Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
3. Check browser console - should no longer see 404 error

## Manual Steps (if deploy.sh fails)

If the deployment script fails, run these manually:

```bash
# Activate virtual environment
source venv/bin/activate

# Build CSS
npm run build:css

# Verify CSS was built
ls -la core/static/css/tailwind.build.css

# Collect static files
python manage.py collectstatic --noinput

# Verify CSS was collected
ls -la staticfiles/css/tailwind.build.css

# Restart services
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

## Troubleshooting

### If CSS file still not found:
1. Check nginx error logs: `sudo tail -f /var/log/nginx/silicon4_error.log`
2. Check nginx access logs: `sudo tail -f /var/log/nginx/silicon4_access.log`
3. Verify STATIC_ROOT in settings: `python manage.py shell -c "from django.conf import settings; print(settings.STATIC_ROOT)"`
4. Test static file URL: `curl -I http://45.32.55.203/static/css/tailwind.build.css`

