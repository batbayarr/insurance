#!/bin/bash

# Vultr Server Setup Script for Silicon4 Accounting
# Run this script on your Vultr server as root

set -e

echo "=========================================="
echo "Setting up Silicon4 Accounting on Vultr"
echo "=========================================="

# Update system
echo "Updating system packages..."
apt update && apt upgrade -y

# Install required software
echo "Installing required software..."
apt install -y python3 python3-pip python3-venv python3-dev nginx git postgresql-client curl wget unzip

# Create application user
echo "Creating application user..."
adduser --system --group --shell /bin/bash silicon4 || true
usermod -aG www-data silicon4 || true

# Create application directory
echo "Creating application directory..."
mkdir -p /var/www/silicon4_accounting
chown silicon4:www-data /var/www/silicon4_accounting
chmod 755 /var/www/silicon4_accounting

# Create logs directory
echo "Creating logs directory..."
mkdir -p /var/www/silicon4_accounting/logs
chown silicon4:www-data /var/www/silicon4_accounting/logs

# Clone repository (you'll need to replace with your actual repo URL)
echo "Cloning repository..."
cd /var/www/silicon4_accounting
# git clone https://github.com/YOUR_USERNAME/silicon4_accounting.git .

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
chown -R silicon4:www-data venv

# Install systemd service
echo "Installing Gunicorn service..."
cp gunicorn.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable gunicorn

# Configure Nginx
echo "Configuring Nginx..."
cp nginx.conf /etc/nginx/sites-available/silicon4_accounting
ln -sf /etc/nginx/sites-available/silicon4_accounting /etc/nginx/sites-enabled/
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
echo "1. Replace YOUR_GITHUB_REPO_URL in this script with your actual repo URL"
echo "2. Run: git clone YOUR_GITHUB_REPO_URL ."
echo "3. Create .env file with your production settings"
echo "4. Run: python3 -m venv venv && source venv/bin/activate"
echo "5. Run: pip install -r requirements.txt"
echo "6. Run: python manage.py migrate"
echo "7. Run: python manage.py collectstatic --noinput"
echo "8. Run: systemctl start gunicorn"
echo "9. Update nginx.conf with your server IP"
echo "10. Run: systemctl restart nginx"
echo ""
echo "Then add your GitHub Secrets and push to main branch!"
