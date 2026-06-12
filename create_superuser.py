#!/usr/bin/env python
"""
IICE-CRM Superuser Creation Script
This script creates a Django superuser for the IICE CRM system.
Run this script from the CRM directory after activating the virtual environment.
"""

import os
import sys
import django
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from decouple import config
from django.conf import settings

def setup_environment():
    """Set up the Django environment with proper paths."""
    # Add the current directory to Python path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'IICE.settings_production')
    
    # Change to the script directory
    os.chdir(current_dir)

    # Detect .env and .env.production
    env_path = os.path.join(current_dir, '.env')
    env_production_path = os.path.join(current_dir, '.env.production')
    print(f"📄 .env present: {os.path.exists(env_path)} at {env_path}")
    print(f"📄 .env.production present: {os.path.exists(env_production_path)} at {env_production_path}")

    # If .env is missing but .env.production exists, load it into os.environ
    if not os.path.exists(env_path) and os.path.exists(env_production_path):
        print("ℹ️ Loading variables from .env.production into environment...")
        try:
            with open(env_production_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key and value and key not in os.environ:
                            os.environ[key] = value
            print("✅ .env.production variables loaded into environment.")
        except Exception as e:
            print(f"⚠️ Failed to load .env.production: {e}")

def create_superuser():
    """Create a superuser with predefined credentials."""
    
    print("=" * 50)
    print("🚀 IICE-CRM Superuser Creation Script")
    print("=" * 50)
    
    # Setup environment
    setup_environment()

    # Show environment configuration that Django will try to use
    print("🔎 Inspecting environment configuration...")
    db_url = os.environ.get('DATABASE_URL') or config('DATABASE_URL', default=None)
    db_name = os.environ.get('DB_NAME') or config('DB_NAME', default='(default)')
    db_user = os.environ.get('DB_USER') or config('DB_USER', default='(default)')
    db_password = os.environ.get('DB_PASSWORD') or config('DB_PASSWORD', default='')
    db_host = os.environ.get('DB_HOST') or config('DB_HOST', default='localhost')
    db_port = os.environ.get('DB_PORT') or config('DB_PORT', default='3306')
    print(f"   DATABASE_URL: {db_url}")
    print(f"   DB_NAME: {db_name}")
    print(f"   DB_USER: {db_user}")
    print(f"   DB_PASSWORD set: {'YES' if bool(db_password) else 'NO'}")
    print(f"   DB_HOST: {db_host}")
    print(f"   DB_PORT: {db_port}")
    if not db_password:
        print("⚠️ DB_PASSWORD is empty. Please set it in .env or DirectAdmin environment variables.")
        print("   If using .env, ensure the file name is exactly '.env' (not .env.production).")

    try:
        print("🔄 Setting up Django environment...")
        django.setup()
        print("✅ Django setup successful!")

        # Print the database settings Django is actually using
        db_settings = settings.DATABASES.get('default', {})
        print("🔧 Django DATABASES[default] in use:")
        print(f"   ENGINE: {db_settings.get('ENGINE')}")
        print(f"   NAME: {db_settings.get('NAME')}")
        print(f"   USER: {db_settings.get('USER')}")
        print(f"   HOST: {db_settings.get('HOST')}")
        print(f"   PORT: {db_settings.get('PORT')}")
        pwd_display = db_settings.get('PASSWORD')
        print(f"   PASSWORD set: {'YES' if bool(pwd_display) else 'NO'}")
        
        # Test database connection
        print("🔄 Testing database connection...")
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✅ Database connection successful!")
        
    except Exception as e:
        print(f"❌ Django/Database setup failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        print("\n🔧 Troubleshooting tips:")
        print("   1. Ensure a real DB_PASSWORD value is set (not NEW_PASSWORD)")
        print("   2. Copy .env.production to .env and set DB_* values correctly")
        print("   3. Or set environment variables in DirectAdmin Web Applications page")
        print("   4. Verify the DB user exists and its password in MySQL Management")
        return False
    
    # Get the User model
    User = get_user_model()
    
    # Superuser credentials
    # Read username from environment/config if available, fallback to explicit value
    username = os.environ.get('SUPERUSER_USERNAME') or config('SUPERUSER_USERNAME', default='huzaifa')
    email = 'callmehuzaifaimran@gmail.com'
    password = '1513'
    first_name = 'Huzaifa'
    
    try:
        # Check if user already exists (by username)
        if User.objects.filter(username=username).exists():
            print(f"⚠️  User with username '{username}' already exists!")
            user = User.objects.get(username=username)
            print(f"📧 Existing user: {user.first_name} {user.last_name} (username: {user.username}, email: {user.email})")
            
            # Update password if needed and ensure superuser privileges
            user.set_password(password)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            print("🔑 Password updated and superuser privileges ensured!")
        else:
            # Create new superuser (Django's default User requires a username)
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name='',
            )
            print(f"✅ Superuser created successfully!")
            print(f"👤 Username: {username}")
            print(f"📧 Email: {email}")
            print(f"👤 Name: {first_name}")
        
        print("\n" + "=" * 50)
        print("🎉 SUCCESS! You can now log in to the CRM:")
        print("🌐 URL: https://crm.iqraacademy.com.pk/admin/")
        print(f"👤 Username: {username}")
        print(f"🔑 Password: {password}")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")
        print(f"   Error type: {type(e).__name__}")
        print("\n🔧 Database troubleshooting:")
        print("   - Verify database user permissions")
        print("   - Run migrations if needed: python manage.py migrate")
        return False

if __name__ == '__main__':
    success = create_superuser()
    if not success:
        print("\n❌ Superuser creation failed!")
        sys.exit(1)
    else:
        print("\n✅ Superuser creation completed successfully!")