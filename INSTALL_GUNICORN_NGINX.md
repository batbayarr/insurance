# 🔧 Install Django, Gunicorn and Nginx

Quick guide to install Django, Gunicorn and Nginx on your Ubuntu server.

## 📋 **Installation Commands**

### Step 1: Install Nginx (System Package)

**Via Termius (connected to your insurance server):**

```bash
# Update package list
sudo apt update

# Install Nginx
sudo apt install -y nginx

# Check Nginx version
nginx -v

# Check Nginx status
sudo systemctl status nginx
```

### Step 2: Install Django and Gunicorn (Python Packages)

**Django and Gunicorn are already in your `requirements.txt`**, so install all dependencies at once:

**Option A: Install all requirements (recommended - includes Django, Gunicorn, and all dependencies)**
```bash
# Navigate to your project directory
cd /var/www/insurance

# Activate virtual environment
source venv/bin/activate

# Install all requirements (includes Django==4.2.23, Gunicorn==21.2.0, and all other packages)
pip install -r requirements.txt
```

**Option B: Install individually (if needed)**
```bash
# Navigate to your project directory
cd /var/www/insurance

# Activate virtual environment
source venv/bin/activate

# Install Django
pip install Django==4.2.23

# Install Gunicorn
pip install gunicorn==21.2.0

# Install other dependencies
pip install -r requirements.txt
```

**Option B: Install system-wide (not recommended)**
```bash
sudo apt install -y gunicorn
```

### Step 3: Verify Installations

```bash
# Activate virtual environment first
cd /var/www/insurance
source venv/bin/activate

# Check Django version
python -m django --version
# or
python manage.py --version

# Check Gunicorn
gunicorn --version

# Check Nginx
nginx -v

# Check if services are running
sudo systemctl status nginx
```

## 🚀 **Quick Setup (If Not Done Yet)**

If you haven't run the full setup script yet, you can install everything at once:

```bash
# Install system packages (includes Nginx)
sudo apt update
sudo apt install -y python3 python3-pip python3-venv python3-dev nginx git postgresql-client curl wget unzip

# Navigate to project
cd /var/www/insurance

# Create/activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages (includes Django, Gunicorn, and all dependencies)
pip install -r requirements.txt

# Verify Django installation
python manage.py --version
```

## ✅ **After Installation**

1. **Start Nginx:**
   ```bash
   sudo systemctl start nginx
   sudo systemctl enable nginx
   ```

2. **Test Nginx:**
   ```bash
   sudo nginx -t
   ```

3. **Configure Gunicorn service:**
   ```bash
   cd /var/www/insurance
   sudo cp gunicorn.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable gunicorn
   ```

4. **Start Gunicorn:**
   ```bash
   sudo systemctl start gunicorn
   sudo systemctl status gunicorn
   ```

## 🔍 **Troubleshooting**

### Nginx not starting?
```bash
# Check Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Check if port 80 is in use
sudo netstat -tulpn | grep :80
```

### Django or Gunicorn not found?
```bash
# Make sure virtual environment is activated
cd /var/www/insurance
source venv/bin/activate

# Check Django
python manage.py --version
python -m django --version

# Check Gunicorn
which gunicorn
gunicorn --version

# If not found, reinstall requirements
pip install -r requirements.txt
```

### Permission issues?
```bash
# Fix ownership
sudo chown -R insurance:www-data /var/www/insurance
```

---

**Note:** The `server-setup.sh` script installs both automatically. If you run that script, you don't need to install manually.

