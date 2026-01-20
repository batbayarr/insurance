#!/bin/bash

# Vultr Server Setup Script for Insurance Project
# Run this script on your Vultr Ubuntu server as root

set -e

echo "=========================================="
echo "Setting up Insurance Project on Vultr"
echo "=========================================="

# Update system
echo "Updating system packages..."
apt update && apt upgrade -y

# Install required software
echo "Installing required software..."
apt install -y python3 python3-pip python3-venv python3-dev nginx git postgresql-client curl wget unzip

# Create application user
echo "Creating application user..."
adduser --system --group --shell /bin/bash insurance || true
usermod -aG www-data insurance || true

# Create application directory
echo "Creating application directory..."
mkdir -p /var/www/insurance
chown insurance:www-data /var/www/insurance
chmod 755 /var/www/insurance

# Create logs directory
echo "Creating logs directory..."
mkdir -p /var/www/insurance/logs
chown insurance:www-data /var/www/insurance/logs

# Clone repository
echo "Cloning repository..."
cd /var/www/insurance
git clone https://github.com/batbayarr/insurance.git .

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
chown -R insurance:www-data venv

# Install systemd service (ensure we're in the right directory)
echo "Installing Gunicorn service..."
cd /var/www/insurance
if [ ! -f "gunicorn.service" ]; then
    echo "ERROR: gunicorn.service not found in /var/www/insurance"
    exit 1
fi
cp gunicorn.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable gunicorn

# Configure Nginx
echo "Configuring Nginx..."
cd /var/www/insurance
if [ ! -f "nginx.conf" ]; then
    echo "ERROR: nginx.conf not found in /var/www/insurance"
    exit 1
fi
cp nginx.conf /etc/nginx/sites-available/insurance
ln -sf /etc/nginx/sites-available/insurance /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
echo "Testing Nginx configuration..."
nginx -t

# Enable and start services
echo "Starting services..."
systemctl enable nginx
systemctl start nginx

# Configure firewall
echo "Configuring firewall..."
ufw --force enable
ufw allow ssh
ufw allow 80
ufw allow 443

echo "=========================================="
echo "Server setup completed!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Create .env file with your production settings"
echo "2. Run: cd /var/www/insurance && source venv/bin/activate"
echo "3. Run: pip install -r requirements.txt"
echo "4. Run: python manage.py migrate"
echo "5. Run: python manage.py collectstatic --noinput"
echo "6. Update nginx.conf with your server IP or domain name"
echo "7. Run: systemctl restart nginx"
echo "8. Run: systemctl start gunicorn"
echo ""
echo "Then add your GitHub Secrets (VULTR_HOST, VULTR_USERNAME, VULTR_PASSWORD) and push to main branch!"
