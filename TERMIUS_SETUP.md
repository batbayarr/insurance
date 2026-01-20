# 🖥️ Termius Setup Guide for Insurance Project

This guide will help you set up and use Termius to manage your Vultr server for the Insurance project.

## 📱 **Setting Up Termius**

### Step 1: Add Your Vultr Server to Termius

1. Open Termius app
2. Click the **"+"** button to add a new host
3. Fill in the connection details:
   - **Label**: `Insurance Vultr Server` (or any name you prefer)
   - **Address**: Your Vultr server IP address
   - **Username**: `root` (or your SSH username)
   - **Port**: `22`
   - **Authentication**: Choose one:
     - **Password**: Enter your server password
     - **Key**: Use SSH key (more secure - recommended)

4. Click **"Save"** and then **"Connect"**

### Step 2: Generate SSH Key for GitHub Actions (Recommended)

Using Termius terminal, run these commands:

```bash
# Generate SSH key pair on your local machine
ssh-keygen -t rsa -b 4096 -C "github-actions@insurance" -f ~/.ssh/insurance_deploy

# Copy public key to your Vultr server
ssh-copy-id -i ~/.ssh/insurance_deploy.pub root@YOUR_SERVER_IP
```

**Or using Termius:**
1. In Termius, go to your host settings
2. Navigate to **Keys** section
3. Generate a new key or import an existing one
4. Copy the public key and add it to your server's `~/.ssh/authorized_keys`

### Step 3: Get Private Key for GitHub Secrets

After generating the SSH key, copy the private key content:

```bash
# On your local machine
cat ~/.ssh/insurance_deploy
```

Copy the entire output (including `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END OPENSSH PRIVATE KEY-----`)

## 🔑 **GitHub Secrets Configuration**

Go to your GitHub repository: **Settings → Secrets and variables → Actions**

Add these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `VULTR_HOST` | Your server IP (e.g., `45.76.123.456`) | Vultr server IP address |
| `VULTR_USERNAME` | `root` | SSH username |
| `VULTR_SSH_KEY` | Contents of `~/.ssh/insurance_deploy` | Private SSH key (entire content) |

**Remove** `VULTR_PASSWORD` if it exists (not needed with SSH key)

## 🚀 **Running Server Setup via Termius**

### Initial Server Setup

1. Connect to your server via Termius
2. Run the setup script:

```bash
# Download the setup script
cd /root
wget https://raw.githubusercontent.com/batbayarr/insurance/main/server-setup.sh
chmod +x server-setup.sh
./server-setup.sh
```

### Manual Setup Steps (if needed)

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install required software
sudo apt install -y python3 python3-pip python3-venv python3-dev nginx git postgresql-client curl wget unzip

# 3. Create application user
sudo adduser --system --group --shell /bin/bash insurance
sudo usermod -aG www-data insurance

# 4. Create application directory
sudo mkdir -p /var/www/insurance
sudo chown insurance:www-data /var/www/insurance
sudo chmod 755 /var/www/insurance

# 5. Clone repository
cd /var/www/insurance
sudo -u insurance git clone https://github.com/batbayarr/insurance.git .

# 6. Create virtual environment
sudo -u insurance python3 -m venv venv
sudo -u insurance ./venv/bin/pip install --upgrade pip

# 7. Install dependencies
sudo -u insurance ./venv/bin/pip install -r requirements.txt
```

## 📋 **Common Termius Commands**

### Check Service Status
```bash
# Gunicorn status
sudo systemctl status gunicorn

# Nginx status
sudo systemctl status nginx
```

### View Logs
```bash
# Gunicorn logs (real-time)
sudo journalctl -u gunicorn -f

# Nginx access logs
sudo tail -f /var/log/nginx/insurance_access.log

# Nginx error logs
sudo tail -f /var/log/nginx/insurance_error.log

# Application logs
tail -f /var/www/insurance/logs/gunicorn-access.log
```

### Restart Services
```bash
# Restart Gunicorn
sudo systemctl restart gunicorn

# Restart Nginx
sudo systemctl restart nginx

# Restart both
sudo systemctl restart gunicorn && sudo systemctl restart nginx
```

### File Management
```bash
# Edit environment file
sudo nano /var/www/insurance/.env

# Edit Nginx config
sudo nano /etc/nginx/sites-available/insurance

# Check file permissions
ls -la /var/www/insurance
```

### Deployment Commands
```bash
# Manual deployment
cd /var/www/insurance
sudo -u insurance git pull origin main
sudo -u insurance ./deploy.sh

# Or run deploy steps manually
cd /var/www/insurance
source venv/bin/activate
git pull origin main
pip install -r requirements.txt
npm ci
npm run build:css
python manage.py collectstatic --noinput
python manage.py migrate
sudo systemctl restart gunicorn
```

## 🔧 **Troubleshooting via Termius**

### Permission Issues
```bash
# Fix ownership
sudo chown -R insurance:www-data /var/www/insurance

# Fix permissions
sudo chmod -R 755 /var/www/insurance
```

### Service Won't Start
```bash
# Check Gunicorn logs
sudo journalctl -u gunicorn -n 50

# Test Gunicorn manually
cd /var/www/insurance
source venv/bin/activate
gunicorn config.wsgi:application --bind 127.0.0.1:8000
```

### Nginx Configuration Issues
```bash
# Test Nginx config
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
cd /var/www/insurance
source venv/bin/activate
python manage.py dbshell
```

## 🔐 **Security Best Practices**

1. **Use SSH Keys**: Always use SSH key authentication instead of passwords
2. **Keep Termius Updated**: Update Termius app regularly
3. **Use Sudo**: Run commands with appropriate permissions
4. **Firewall**: Ensure firewall is configured (ports 22, 80, 443)
5. **Regular Updates**: Keep server packages updated

## 📱 **Termius Tips**

- **Snippets**: Save common commands as snippets in Termius for quick access
- **Port Forwarding**: Use Termius port forwarding for local development
- **SFTP**: Use Termius SFTP feature to transfer files easily
- **Groups**: Organize multiple servers into groups
- **Tags**: Tag your servers for better organization

## 🎯 **Quick Reference**

| Task | Command |
|------|---------|
| Connect to server | Open Termius → Select host → Connect |
| Check app status | `sudo systemctl status gunicorn` |
| View logs | `sudo journalctl -u gunicorn -f` |
| Restart app | `sudo systemctl restart gunicorn` |
| Deploy manually | `cd /var/www/insurance && ./deploy.sh` |
| Edit config | `sudo nano /var/www/insurance/.env` |

---

**Need Help?** Check the main deployment guide or GitHub Actions logs for deployment issues.

