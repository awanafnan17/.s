#!/usr/bin/env python
"""
Database Configuration Helper for IICE CRM
This script helps configure and test database connections for production deployment.
"""

import os
import sys
import subprocess
from pathlib import Path

def check_mysql_client():
    """Check if MySQL client is available and install if needed."""
    print("🔍 Checking MySQL client installation...")
    
    try:
        import MySQLdb
        print("✅ MySQLdb (mysqlclient) is available")
        return 'mysqlclient'
    except ImportError:
        pass
    
    try:
        import pymysql
        print("✅ PyMySQL is available")
        return 'pymysql'
    except ImportError:
        pass
    
    print("❌ No MySQL client found")
    return None

def install_mysql_client():
    """Install MySQL client with fallback options."""
    print("📦 Installing MySQL client...")
    
    # Try mysqlclient first
    try:
        print("Trying to install mysqlclient...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'mysqlclient'])
        print("✅ mysqlclient installed successfully")
        return 'mysqlclient'
    except subprocess.CalledProcessError:
        print("⚠️  mysqlclient installation failed, trying PyMySQL...")
    
    # Fallback to PyMySQL
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'PyMySQL'])
        print("✅ PyMySQL installed successfully")
        return 'pymysql'
    except subprocess.CalledProcessError:
        print("❌ Failed to install MySQL client")
        return None

def configure_pymysql():
    """Configure PyMySQL as MySQLdb replacement."""
    settings_file = Path(__file__).parent / 'IICE' / 'settings_production.py'
    
    if not settings_file.exists():
        print(f"⚠️  Settings file not found: {settings_file}")
        return False
    
    # Read current settings
    with open(settings_file, 'r') as f:
        content = f.read()
    
    # Check if PyMySQL configuration already exists
    if 'pymysql.install_as_MySQLdb()' in content:
        print("✅ PyMySQL configuration already exists")
        return True
    
    # Add PyMySQL configuration at the top
    pymysql_config = '''"""Production settings for IICE CRM deployment."""

# Configure PyMySQL as MySQLdb replacement
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass

'''
    
    # Replace the first line with our configuration
    lines = content.split('\n')
    if lines[0].startswith('"""Production settings'):
        lines[0] = pymysql_config.strip()
        new_content = '\n'.join(lines)
        
        # Write back to file
        with open(settings_file, 'w') as f:
            f.write(new_content)
        
        print("✅ PyMySQL configuration added to settings")
        return True
    
    print("⚠️  Could not add PyMySQL configuration automatically")
    return False

def test_database_connection():
    """Test database connection with current settings."""
    print("🔍 Testing database connection...")
    
    try:
        # Set up Django environment
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'IICE.settings_production')
        
        import django
        from django.conf import settings
        from django.db import connection
        
        django.setup()
        
        # Test connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        if result and result[0] == 1:
            print("✅ Database connection successful!")
            
            # Get database info
            with connection.cursor() as cursor:
                cursor.execute("SELECT VERSION()")
                version = cursor.fetchone()[0]
                print(f"📊 MySQL Version: {version}")
                
                cursor.execute("SELECT DATABASE()")
                db_name = cursor.fetchone()[0]
                print(f"📊 Connected to database: {db_name}")
            
            return True
        else:
            print("❌ Database connection test failed")
            return False
            
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n💡 Troubleshooting tips:")
        print("1. Check your .env file has correct database credentials")
        print("2. Ensure MySQL service is running")
        print("3. Verify database 'iice_production' exists")
        print("4. Check user 'iice_user' has proper permissions")
        print("5. Review DATABASE_TROUBLESHOOTING.md for more help")
        return False

def create_test_env_file():
    """Create a test environment file with database settings."""
    env_file = Path(__file__).parent / '.env.test'
    
    if env_file.exists():
        print(f"✅ Test environment file already exists: {env_file}")
        return
    
    env_content = '''# Test Environment Configuration for Database Setup
# Copy this to .env and update with your actual values

# Django Settings
DEBUG=False
SECRET_KEY=test-secret-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,da600.is.cc

# Database Configuration
DB_NAME=iice_production
DB_USER=iice_user
DB_PASSWORD=CHANGE_THIS_TO_YOUR_SECURE_PASSWORD
DB_HOST=localhost
DB_PORT=3306

# Email Configuration (optional for database testing)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Logging
DJANGO_LOG_LEVEL=INFO
'''
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print(f"✅ Created test environment file: {env_file}")
        print("📝 Please update the database password and other settings")
    except Exception as e:
        print(f"❌ Failed to create test environment file: {e}")

def main():
    """Main function to configure database setup."""
    print("🗄️  IICE CRM Database Configuration Helper")
    print("=" * 50)
    
    # Step 1: Check MySQL client
    client_type = check_mysql_client()
    
    if not client_type:
        print("\n📦 Installing MySQL client...")
        client_type = install_mysql_client()
        
        if not client_type:
            print("\n❌ Failed to install MySQL client")
            print("\n💡 Manual installation options:")
            print("1. Install system dependencies first:")
            print("   - On Ubuntu/Debian: sudo apt-get install python3-dev default-libmysqlclient-dev build-essential")
            print("   - On CentOS/RHEL: sudo yum install python3-devel mysql-devel gcc")
            print("2. Then try: pip install mysqlclient")
            print("3. Or use PyMySQL: pip install PyMySQL")
            return 1
    
    # Step 2: Configure PyMySQL if needed
    if client_type == 'pymysql':
        print("\n🔧 Configuring PyMySQL...")
        configure_pymysql()
    
    # Step 3: Create test environment file
    print("\n📝 Creating test environment file...")
    create_test_env_file()
    
    # Step 4: Test database connection
    print("\n🔍 Testing database connection...")
    if test_database_connection():
        print("\n🎉 Database configuration completed successfully!")
        print("\n📋 Next steps:")
        print("1. Run database migrations: python manage.py migrate")
        print("2. Create superuser: python manage.py createsuperuser")
        print("3. Collect static files: python manage.py collectstatic")
    else:
        print("\n⚠️  Database connection failed")
        print("\n📋 Next steps:")
        print("1. Review the error messages above")
        print("2. Check DATABASE_TROUBLESHOOTING.md for solutions")
        print("3. Verify your database credentials in .env file")
        print("4. Ensure database and user exist (run database_setup.sql)")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())