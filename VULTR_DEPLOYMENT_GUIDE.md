# 🚀 Vultr Deployment Guide - Silicon4 Accounting

## ✅ **Files Updated Successfully**

Your production setup has been fixed and optimized:

### **Fixed Issues:**
- ✅ **deploy.yml**: Updated to use SSH key authentication (more secure)
- ✅ **deploy.yml**: Now calls `deploy.sh` script (cleaner deployment)
- ✅ **deploy.yml**: Removed dangerous `makemigrations` from auto-deployment
- ✅ **deploy.yml**: Added proper error handling and status reporting

### **Files Ready for Production:**
- ✅ `.github/workflows/deploy.yml` - GitHub Actions workflow
- ✅ `deploy.sh` - Server deployment script
- ✅ `gunicorn.service` - Systemd service configuration
- ✅ `nginx.conf` - Nginx reverse proxy config
- ✅ `server-setup.sh` - One-time server setup script

---

## 🔧 **Vultr Server Setup (One-time)**

### **Step 1: Upload Files to Server**
```bash
# On your Vultr server, run:
cd /root
wget https://raw.githubusercontent.com/YOUR_USERNAME/silicon4_accounting/main/server-setup.sh
chmod +x server-setup.sh
./server-setup.sh
```

### **Step 2: Clone Your Repository**
```bash
cd /var/www/silicon4_accounting
git clone https://github.com/YOUR_USERNAME/silicon4_accounting.git .
chown -R silicon4:www-data /var/www/silicon4_accounting
```

### **Step 3: Configure Environment**
```bash
# Create production environment file
cp .env.production .env
nano .env
```

**Update these values in `.env`:**
```env
SECRET_KEY=your-new-secret-key-here
DEBUG=False
ALLOWED_HOSTS=YOUR_SERVER_IP,localhost
DB_NAME=silicon4
DB_USER=postgres
DB_PASSWORD=your-database-password
DB_HOST=localhost
DB_PORT=5432
```

### **Step 4: Install Dependencies & Setup**
```bash
cd /var/www/silicon4_accounting
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
```

### **Step 5: Update Nginx Configuration**
```bash
# Edit nginx config to replace SERVER_IP
nano /etc/nginx/sites-available/silicon4_accounting
# Replace "SERVER_IP" with your actual Vultr server IP
```

### **Step 6: Start Services**
```bash
systemctl start gunicorn
systemctl restart nginx
systemctl status gunicorn
systemctl status nginx
```

---

## 🔑 **GitHub Secrets Setup**

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `VULTR_HOST` | Your Vultr server IP (e.g., `45.76.123.456`) |
| `VULTR_USERNAME` | `root` (or your SSH username) |
| `VULTR_SSH_KEY` | The private SSH key content (from earlier) |

**Remove:** `VULTR_PASSWORD` (not needed with SSH key)

---

## 🚀 **Deploy Your App**

### **First Deployment:**
1. Push all changes to main branch:
   ```bash
   git add .
   git commit -m "Add production deployment setup"
   git push origin main
   ```

2. Check GitHub Actions tab for deployment status

3. Visit `http://YOUR_SERVER_IP` to see your app

### **Future Deployments:**
- Just push to main branch - deployment happens automatically!
- Check GitHub Actions for deployment logs

---

## 🔍 **Troubleshooting**

### **Check Logs:**
```bash
# Gunicorn logs
journalctl -u gunicorn -f

# Nginx logs
tail -f /var/log/nginx/silicon4_error.log
tail -f /var/log/nginx/silicon4_access.log

# Application logs
tail -f /var/www/silicon4_accounting/logs/silicon4.log
```

### **Common Issues:**
1. **Permission errors**: `chown -R silicon4:www-data /var/www/silicon4_accounting`
2. **Database connection**: Check PostgreSQL is running and credentials are correct
3. **Static files**: Run `python manage.py collectstatic --noinput`
4. **Service not starting**: Check `systemctl status gunicorn`

---

## 📋 **Security Checklist**

- ✅ SSH key authentication (no passwords)
- ✅ Firewall configured (ports 22, 80, 443)
- ✅ Non-root user for application
- ✅ Proper file permissions
- ✅ Production security settings in Django
- ✅ Static files served by Nginx

---

## 🎯 **Next Steps After Deployment**

1. **Set up SSL certificate** (Let's Encrypt)
2. **Configure domain name** (if you have one)
3. **Set up automated database backups**
4. **Configure monitoring and alerts**
5. **Set up log rotation**

---

## 📞 **Support**

If you encounter any issues:
1. Check the logs first
2. Verify all services are running: `systemctl status gunicorn nginx`
3. Test database connection: `python manage.py dbshell`
4. Check GitHub Actions logs for deployment errors

Your Django accounting app is now ready for production deployment! 🎉
