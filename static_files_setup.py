#!/usr/bin/env python
"""
Static Files Setup Script for IICE CRM Production Deployment
This script helps configure static files and media handling for production.
"""

import os
import sys
import django
from pathlib import Path

# Add the project directory to Python path
project_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(project_dir))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'IICE.settings_production')

# Setup Django
django.setup()

from django.core.management import execute_from_command_line
from django.conf import settings
from django.contrib.staticfiles.management.commands.collectstatic import Command as CollectStaticCommand

def create_directories():
    """Create necessary directories for static files and media."""
    directories = [
        settings.STATIC_ROOT,
        settings.MEDIA_ROOT,
        os.path.join(settings.BASE_DIR, 'logs'),
    ]
    
    for directory in directories:
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"📁 Directory already exists: {directory}")

def set_permissions():
    """Set proper permissions for static files and media directories."""
    try:
        # Set permissions for media directory (needs write access)
        if os.path.exists(settings.MEDIA_ROOT):
            os.chmod(settings.MEDIA_ROOT, 0o755)
            print(f"✅ Set permissions for media directory: {settings.MEDIA_ROOT}")
        
        # Set permissions for static files directory
        if os.path.exists(settings.STATIC_ROOT):
            os.chmod(settings.STATIC_ROOT, 0o755)
            print(f"✅ Set permissions for static directory: {settings.STATIC_ROOT}")
        
        # Set permissions for logs directory
        logs_dir = os.path.join(settings.BASE_DIR, 'logs')
        if os.path.exists(logs_dir):
            os.chmod(logs_dir, 0o755)
            print(f"✅ Set permissions for logs directory: {logs_dir}")
            
    except Exception as e:
        print(f"⚠️  Warning: Could not set permissions: {e}")
        print("   You may need to set permissions manually on your hosting server.")

def collect_static_files():
    """Collect static files for production."""
    print("📦 Collecting static files...")
    try:
        execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
        print("✅ Static files collected successfully")
    except Exception as e:
        print(f"❌ Error collecting static files: {e}")
        return False
    return True

def create_htaccess():
    """Create .htaccess file for Apache servers."""
    htaccess_content = '''# IICE CRM Static Files Configuration

# Enable URL rewriting
RewriteEngine On

# Handle static files
RewriteRule ^static/(.*)$ /static/$1 [L]
RewriteRule ^media/(.*)$ /media/$1 [L]

# Handle Django application
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^(.*)$ passenger_wsgi.py [QSA,L]

# Security headers
Header always set X-Content-Type-Options nosniff
Header always set X-Frame-Options DENY
Header always set X-XSS-Protection "1; mode=block"

# Cache static files
<FilesMatch "\.(css|js|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$">
    ExpiresActive On
    ExpiresDefault "access plus 1 month"
    Header set Cache-Control "public, max-age=2592000"
</FilesMatch>

# Compress static files
<IfModule mod_deflate.c>
    AddOutputFilterByType DEFLATE text/plain
    AddOutputFilterByType DEFLATE text/html
    AddOutputFilterByType DEFLATE text/xml
    AddOutputFilterByType DEFLATE text/css
    AddOutputFilterByType DEFLATE application/xml
    AddOutputFilterByType DEFLATE application/xhtml+xml
    AddOutputFilterByType DEFLATE application/rss+xml
    AddOutputFilterByType DEFLATE application/javascript
    AddOutputFilterByType DEFLATE application/x-javascript
</IfModule>
'''
    
    htaccess_path = os.path.join(settings.BASE_DIR, '.htaccess')
    try:
        with open(htaccess_path, 'w') as f:
            f.write(htaccess_content)
        print(f"✅ Created .htaccess file: {htaccess_path}")
    except Exception as e:
        print(f"⚠️  Warning: Could not create .htaccess file: {e}")

def create_nginx_config():
    """Create nginx configuration snippet for static files."""
    nginx_config = '''# IICE CRM Nginx Configuration for Static Files
# Add this to your nginx server block

location /static/ {
    alias /home/iqraacad/public_html/IICE-CRM/staticfiles/;
    expires 30d;
    add_header Cache-Control "public, max-age=2592000";
    add_header X-Content-Type-Options nosniff;
}

location /media/ {
    alias /home/iqraacad/public_html/IICE-CRM/media/;
    expires 7d;
    add_header Cache-Control "public, max-age=604800";
    add_header X-Content-Type-Options nosniff;
}

# Gzip compression
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
'''
    
    nginx_config_path = os.path.join(settings.BASE_DIR, 'nginx_static_config.txt')
    try:
        with open(nginx_config_path, 'w') as f:
            f.write(nginx_config)
        print(f"✅ Created nginx config snippet: {nginx_config_path}")
    except Exception as e:
        print(f"⚠️  Warning: Could not create nginx config: {e}")

def main():
    """Main function to set up static files for production."""
    print("🚀 IICE CRM Static Files Setup")
    print("=" * 40)
    
    print("\n📁 Creating directories...")
    create_directories()
    
    print("\n🔐 Setting permissions...")
    set_permissions()
    
    print("\n📦 Collecting static files...")
    if collect_static_files():
        print("\n🌐 Creating web server configurations...")
        create_htaccess()
        create_nginx_config()
        
        print("\n✅ Static files setup completed successfully!")
        print("\n📋 Next steps:")
        print("1. Upload the project files to your hosting server")
        print("2. Ensure the .htaccess file is in your project root")
        print("3. Verify that static files are accessible via web browser")
        print("4. Test media file uploads and access")
        
        print("\n🔗 Static files URL:", settings.STATIC_URL)
        print("📁 Static files path:", settings.STATIC_ROOT)
        print("🔗 Media files URL:", settings.MEDIA_URL)
        print("📁 Media files path:", settings.MEDIA_ROOT)
    else:
        print("\n❌ Static files setup failed. Please check the errors above.")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())