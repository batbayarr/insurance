# Vultr Server Setup Guide

This guide will help you set up your Vultr server for deploying the Silicon4 Accounting Django application.

## Prerequisites
- Vultr server with Ubuntu 20.04+ (recommended)
- SSH access to your server
- Your server's IP address

## Step 1: Initial Server Setup

### 1.1 Update System Packages
```bash
sudo apt update && sudo apt upgrade -y
```

### 1.2 Install Required Software
```bash
# Install Python, pip, and virtualenv
sudo apt install python3 python3-pip python3-venv python3-dev -y

# Install PostgreSQL client (if connecting to external DB)
sudo apt install postgresql-client -y

# Install Nginx
sudo apt install nginx -y

# Install Git
sudo apt install git -y

# Install other utilities
sudo apt install curl wget unzip -y
```

### 1.3 Create Application User
```bash
# Create a dedicated user for the application
sudo adduser --system --group --shell /bin/bash silicon4
sudo usermod -aG www-data silicon4
```

## Step 2: Application Directory Setup

### 2.1 Create Application Directory
```bash
sudo mkdir -p /var/www/silicon4_accounting
sudo chown silicon4:www-data /var/www/silicon4_accounting
sudo chmod 755 /var/www/silicon4_accounting
```

### 2.2 Clone Repository
```bash
cd /var/www/silicon4_accounting
sudo -u silicon4 git clone https://github.com/YOUR_USERNAME/silicon4_accounting.git .
```

### 2.3 Create Virtual Environment
```bash
cd /var/www/silicon4_accounting
sudo -u silicon4 python3 -m venv venv
sudo -u silicon4 ./venv/bin/pip install --upgrade pip
```

## Step 3: Environment Configuration

### 3.1 Create Production Environment File
```bash
sudo -u silicon4 cp .env.production .env
sudo -u silicon4 nano .env
```

Update the following values in `.env`:
- `SECRET_KEY`: Generate a new secret key
- `ALLOWED_HOSTS`: Your server IP address
- `DB_PASSWORD`: Your PostgreSQL password
- `DEBUG=False`

### 3.2 Generate Secret Key
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## Step 4: Install Dependencies

```bash
cd /var/www/silicon4_accounting
sudo -u silicon4 ./venv/bin/pip install -r requirements.txt
```

## Step 5: Database Setup

### 5.1 Run Migrations
```bash
cd /var/www/silicon4_accounting
sudo -u silicon4 ./venv/bin/python manage.py migrate
```

### 5.2 Create Superuser (Optional)
```bash
sudo -u silicon4 ./venv/bin/python manage.py createsuperuser
```

### 5.3 Collect Static Files
```bash
sudo -u silicon4 ./venv/bin/python manage.py collectstatic --noinput
```

## Step 6: Configure Services

### 6.1 Setup Gunicorn Service
```bash
# Copy the service file
sudo cp gunicorn.service /etc/systemd/system/

# Reload systemd and enable the service
sudo systemctl daemon-reload
sudo systemctl enable gunicorn
```

### 6.2 Setup Nginx
```bash
# Copy nginx configuration
sudo cp nginx.conf /etc/nginx/sites-available/silicon4_accounting

# Create symbolic link
sudo ln -s /etc/nginx/sites-available/silicon4_accounting /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test nginx configuration
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx
```

### 6.3 Update Nginx Configuration
Edit `/etc/nginx/sites-available/silicon4_accounting` and replace `SERVER_IP` with your actual server IP address.

## Step 7: Firewall Configuration

```bash
# Enable UFW
sudo ufw enable

# Allow SSH
sudo ufw allow ssh

# Allow HTTP
sudo ufw allow 80

# Allow HTTPS (if using SSL later)
sudo ufw allow 443
```

## Step 8: Start Services

```bash
# Start Gunicorn
sudo systemctl start gunicorn

# Start Nginx
sudo systemctl start nginx

# Check status
sudo systemctl status gunicorn
sudo systemctl status nginx
```

## Step 9: GitHub Actions Setup

### 9.1 Generate SSH Key for GitHub Actions
```bash
# On your local machine, generate SSH key pair
ssh-keygen -t rsa -b 4096 -C "github-actions@silicon4" -f ~/.ssh/vultr_deploy

# Copy public key to server
ssh-copy-id -i ~/.ssh/vultr_deploy.pub root@YOUR_SERVER_IP
```

### 9.2 Add GitHub Secrets
In your GitHub repository, go to Settings > Secrets and variables > Actions, and add:

- `VULTR_HOST`: Your server IP address
- `VULTR_USERNAME`: `root` (or your SSH username)
- `VULTR_SSH_KEY`: Contents of `~/.ssh/vultr_deploy` (private key)

## Step 10: Test Deployment

1. Make a small change to your code
2. Commit and push to main branch
3. Check GitHub Actions tab for deployment status
4. Visit `http://YOUR_SERVER_IP` to verify the application

## Troubleshooting

### Check Logs
```bash
# Gunicorn logs
sudo journalctl -u gunicorn -f

# Nginx logs
sudo tail -f /var/log/nginx/silicon4_error.log
sudo tail -f /var/log/nginx/silicon4_access.log

# Application logs
tail -f /var/www/silicon4_accounting/logs/silicon4.log
```

### Common Issues
1. **Permission errors**: Ensure `silicon4` user owns the application directory
2. **Database connection**: Verify PostgreSQL is running and credentials are correct
3. **Static files**: Run `collectstatic` if CSS/JS files are missing
4. **Port conflicts**: Ensure ports 80 and 22 are not blocked by firewall

## Security Notes
- Change default SSH port (optional)
- Use strong passwords
- Keep system updated
- Consider setting up SSL certificate with Let's Encrypt
- Regular database backups

## Next Steps
- Set up automated database backups
- Configure SSL certificate
- Set up monitoring and logging
- Configure domain name (if available)
