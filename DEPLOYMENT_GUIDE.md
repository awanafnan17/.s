# IICE CRM Deployment Guide

This guide provides step-by-step instructions for deploying the IICE CRM application on your hosting service (da600.is.cc).

## 🚀 Quick Start

### Prerequisites
- Access to hosting control panel: https://da600.is.cc:2222/evo/
- Username: `iqraacad`
- Password: `YegDgCkeA6Jjw3VPcFeX`
- Python 3.8+ support on hosting
- MySQL database access

## 📋 Deployment Steps

### Step 1: Access Your Hosting Control Panel

1. Navigate to: https://da600.is.cc:2222/evo/
2. Login with:
   - Username: `iqraacad`
   - Password: `YegDgCkeA6Jjw3VPcFeX`

### Step 2: Upload Project Files

**⚠️ Note:** If File Manager doesn't upload folders properly, use command-line methods below.

#### Option A: Via SCP (Secure Copy) - ⚠️ Authentication Issues
```bash
# From your local machine (Windows PowerShell or Git Bash)
# Navigate to your project directory
cd "C:\Users\Afnan Awan\Downloads\CRM"

# Upload entire project folder
scp -r IICE-CRM iqraacad@da600.is.cc:/home/iqraacad/public_html/

# If prompted for password, use: YegDgCkeA6Jjw3VPcFeX
# Note: If getting "Permission denied", try Option E (ZIP upload) instead
```

#### Option A2: Via SFTP (Alternative to SCP)
```bash
# Connect via SFTP
sftp iqraacad@da600.is.cc
# Password: YegDgCkeA6Jjw3VPcFeX

# Navigate to web directory
cd public_html

# Create project directory
mkdir IICE-CRM
cd IICE-CRM

# Upload files recursively
put -r C:\Users\Afnan Awan\Downloads\CRM\IICE-CRM\*

# Exit SFTP
quit
```

#### Option B: Via RSYNC (if available)
```bash
# Sync entire project folder
rsync -avz --progress IICE-CRM/ iqraacad@da600.is.cc:/home/iqraacad/public_html/IICE-CRM/
```

#### Option C: Via FTP Commands
```bash
# Connect via FTP
ftp da600.is.cc
# Username: iqraacad
# Password: YegDgCkeA6Jjw3VPcFeX

# Navigate to web directory
cd public_html

# Create project directory
mkdir IICE-CRM
cd IICE-CRM

# Upload files (you'll need to do this for each file/folder)
put manage.py
put requirements-production.txt
put database_setup.sql
# ... continue for all files

# For folders, create them first then upload contents
mkdir Admin
cd Admin
put Admin/*
cd ..
# ... repeat for all folders
```

#### Option D: Create Upload Script
```bash
# Create a batch upload script
echo "#!/bin/bash" > upload.sh
echo "scp -r * iqraacad@da600.is.cc:/home/iqraacad/public_html/IICE-CRM/" >> upload.sh
chmod +x upload.sh
./upload.sh
```

#### Option E: Via File Manager (Alternative Method)
1. **Compress your project:**
   ```bash
   # Create a zip file of your project
   cd "C:\Users\Afnan Awan\Downloads\CRM"
   tar -czf IICE-CRM.tar.gz IICE-CRM/
   # Or use 7-Zip/WinRAR to create IICE-CRM.zip
   ```

2. **Upload and extract:**
   - Upload the zip/tar.gz file via File Manager
   - SSH into your server and extract:
   ```bash
   ssh iqraacad@da600.is.cc
   cd public_html
   tar -xzf IICE-CRM.tar.gz
   # or unzip IICE-CRM.zip
   ```

### Step 3: Install Python (if not available)

**Check if Python is installed:**
```bash
python --version
# or try
python3 --version
```

**If Python is not installed, contact your hosting provider or:**

1. **For shared hosting:** Most hosting providers have Python pre-installed. If not available, contact support to enable Python or upgrade your hosting plan.

2. **For VPS/Dedicated servers:**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install python3 python3-pip python3-venv
   
   # CentOS/RHEL
   sudo yum install python3 python3-pip
   
   # Create symlink if needed
   sudo ln -s /usr/bin/python3 /usr/bin/python
   ```

### Step 4: Set Up Database

1. **Create Database:** ✅ COMPLETED
   - Database created: `iqraacad_iice_production`
   - Username: `iqraacad_iice_production` 
   - Password: `unHmnyGfZMjIAIIrHI` (auto-generated)
   - Hostname: `localhost`
   - All privileges granted automatically

2. **Run Database Setup:**
   
   **Method 1: Using SSH (Command Line)**
   ```bash
   mysql -u iqraacad_iice_production -p iqraacad_iice_production < database_setup.sql
   # When prompted for password, enter: unHmnyGfZMjIAIIrHI
   ```

   **Method 2: Using phpMyAdmin (Recommended for shared hosting)**
   1. Log into your hosting control panel
   2. Open phpMyAdmin
   3. Select the `iqraacad_iice_production` database
   4. Go to the "Import" tab
   5. Choose the `database_setup.sql` file
   6. Click "Go" to import

   **Note:** The database_setup.sql file has been simplified to avoid permission errors. It only contains basic verification queries that work with regular database user privileges.

**Testing Database Connection:**
After importing, you can test your database connection using:
```bash
mysql -u iqraacad_iice_production -p iqraacad_iice_production < test_database_connection.sql
```
Or import `test_database_connection.sql` via phpMyAdmin to verify everything is working correctly.

### Step 5: Upload and Extract Files

1. **Upload the project archive:**
   - Upload `IICE-CRM.tar.gz` to your server's `public_html` directory
   - You can use FTP, cPanel File Manager, or hosting control panel

2. **Extract the archive:**
   ```bash
   cd /home/iqraacad/public_html
   tar -xzf IICE-CRM.tar.gz
   rm IICE-CRM.tar.gz  # Optional: remove the archive after extraction
   ```

3. **Verify extraction:**
   ```bash
   ls -la IICE-CRM/
   ```

### Step 6: Configure Environment Variables

1. **Copy environment file:**
   ```bash
   cp .env.production .env
   ```

2. **Edit `.env` file with your actual values:**
   ```env
   DEBUG=False
   SECRET_KEY=your-very-long-random-secret-key-here
   ALLOWED_HOSTS=da600.is.cc,www.da600.is.cc
   
   # Database (using actual hosting credentials)
   DB_NAME=iqraacad_iice_production
   DB_USER=iqraacad_iice_production
   DB_PASSWORD=unHmnyGfZMjIAIIrHI
   DB_HOST=localhost
   DB_PORT=3306
   
   # Email (use encrypted password)
   EMAIL_ENCRYPTION_KEY=your-encryption-key
   EMAIL_HOST_PASSWORD_ENCRYPTED=your-encrypted-password
   ```

### Step 7: Set Up Python Environment

1. **Create virtual environment:**
   ```bash
   python -m venv /home/iqraacad/venv
   source /home/iqraacad/venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install --upgrade pip
   pip install -r requirements-production.txt
   ```

### Step 8: Run Django Setup Commands

```bash
# Navigate to project directory
cd /home/iqraacad/public_html/IICE-CRM

# Activate virtual environment
source /home/iqraacad/venv/bin/activate

# Collect static files
python manage.py collectstatic --noinput --settings=IICE.settings_production

# Run migrations
python manage.py migrate --settings=IICE.settings_production

# Create superuser
python manage.py createsuperuser --settings=IICE.settings_production
```

### Step 9: Configure Web Server

1. **Create `passenger_wsgi.py` in project root:**
   ```python
   import sys
   import os
   
   # Add project directory to Python path
   sys.path.insert(0, '/home/iqraacad/public_html/IICE-CRM')
   
   # Set Django settings module
   os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'IICE.settings_production')
   
   # Import Django WSGI application
   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```

2. **Create `.htaccess` file:**
   ```apache
   RewriteEngine On
   RewriteCond %{REQUEST_FILENAME} !-f
   RewriteCond %{REQUEST_FILENAME} !-d
   RewriteRule ^(.*)$ passenger_wsgi.py [QSA,L]
   
   # Static files
   RewriteRule ^static/(.*)$ /static/$1 [L]
   RewriteRule ^media/(.*)$ /media/$1 [L]
   ```

### Step 10: Set File Permissions

```bash
# Set proper permissions
chmod -R 755 /home/iqraacad/public_html/IICE-CRM
chmod -R 777 /home/iqraacad/public_html/IICE-CRM/media
chmod -R 777 /home/iqraacad/public_html/IICE-CRM/logs
```

## 🔧 Automated Deployment

For easier deployment, use the provided deployment script:

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment script
./deploy.sh
```

## Alternative Hosting Options (For Reference)

### 1. Railway (Recommended for cloud deployment)
- **Free Tier**: $5 credit per month (usually sufficient for small apps)
- **Pros**: Easy deployment, automatic HTTPS, good performance
- **Cons**: Limited free usage
- **Best for**: Production-ready deployments

### 2. PythonAnywhere
- **Free Tier**: Truly free with limitations
- **Pros**: Beginner-friendly, no credit card required
- **Cons**: Custom domains not available on free tier
- **Best for**: Testing and demonstrations

### Alternative Deployment Steps for Railway (if needed)

#### Prerequisites
1. GitHub account
2. Railway account (sign up at railway.app)
3. Push your code to GitHub repository

#### Step 1: Prepare Your Repository
1. Ensure all files are committed to your GitHub repository
2. Make sure the following files are present:
   - `requirements.txt`
   - `Procfile`
   - `runtime.txt`
   - `railway.json`

#### Step 2: Deploy on Railway
1. Go to [Railway.app](https://railway.app)
2. Sign in with GitHub
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your IICE-CRM repository
6. Railway will automatically detect it's a Django app

#### Step 3: Configure Environment Variables
In Railway dashboard, go to Variables tab and add:

```env
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=your-app-name.railway.app
DATABASE_URL=postgresql://...
EMAIL_HOST_PASSWORD=your-email-password
```

## 🔐 Security Configuration

### SSL Certificate Setup

1. **Enable SSL in hosting control panel**
2. **Update `.env` file:**
   ```env
   # Uncomment these lines in settings_production.py after SSL is active
   # SECURE_SSL_REDIRECT = True
   # SESSION_COOKIE_SECURE = True
   # CSRF_COOKIE_SECURE = True
   ```

### Email Encryption Setup

1. **Generate encryption key:**
   ```bash
   python manage.py encrypt_email_password --generate-key
   ```

2. **Encrypt your email password:**
   ```bash
   python manage.py encrypt_email_password --password "your-email-password"
   ```

3. **Update `.env` with encrypted values**

## 📊 Monitoring and Maintenance

### Log Files
- Application logs: `/home/iqraacad/public_html/IICE-CRM/logs/django.log`
- Error logs: Check hosting control panel

### Database Backup
```bash
# Create backup
mysqldump -u iice_user -p iice_production > backup_$(date +%Y%m%d).sql

# Restore backup
mysql -u iice_user -p iice_production < backup_20240101.sql
```

### Regular Maintenance
```bash
# Update dependencies
pip install -r requirements-production.txt --upgrade

# Run migrations
python manage.py migrate --settings=IICE.settings_production

# Collect static files
python manage.py collectstatic --noinput --settings=IICE.settings_production
```

## 🚨 Troubleshooting

### Common Issues

1. **500 Internal Server Error:**
   - Check error logs in hosting control panel
   - Verify file permissions
   - Check `.env` configuration

2. **Database Connection Error:**
   - Verify database credentials in `.env`
   - Check if database exists
   - Ensure database user has proper privileges

3. **Static Files Not Loading:**
   - Run `collectstatic` command
   - Check file permissions
   - Verify `.htaccess` configuration

4. **Email Not Working:**
   - Check email configuration in `.env`
   - Verify Gmail App Password
   - Test email encryption/decryption

### Debug Mode (Temporary)

For troubleshooting, temporarily enable debug mode:

```env
# In .env file (NEVER leave this in production)
DEBUG=True
```

**⚠️ Remember to set `DEBUG=False` after troubleshooting!**

## 📞 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Review log files for error messages
3. Verify all configuration steps were completed
4. Contact hosting support if server-related issues persist

## 🔒 Security Best Practices

1. **Never commit sensitive data to version control**
2. **Use strong, unique passwords**
3. **Keep dependencies updated**
4. **Enable SSL/HTTPS**
5. **Regular database backups**
6. **Monitor log files for suspicious activity**
7. **Use encrypted email passwords**

---

**🎉 Congratulations!** Your IICE CRM application should now be successfully deployed and running on your hosting service.

Access your application at: `https://da600.is.cc/IICE-CRM/`
Admin panel: `https://da600.is.cc/IICE-CRM/admin/`