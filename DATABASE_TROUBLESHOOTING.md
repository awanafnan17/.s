# Database Setup Troubleshooting Guide

## 🔧 Common Issues and Solutions

### Issue 1: MySQL Client Not Installed

**Error**: `django.core.exceptions.ImproperlyConfigured: Error loading MySQLdb module`

**Solution**:
```bash
# Install MySQL client
pip install mysqlclient

# If mysqlclient fails, try PyMySQL as alternative:
pip install PyMySQL

# Then add this to your Django settings:
# import pymysql
# pymysql.install_as_MySQLdb()
```

### Issue 2: Database Connection Refused

**Error**: `django.db.utils.OperationalError: (2003, "Can't connect to MySQL server")`

**Solutions**:
1. **Check MySQL service is running**:
   ```bash
   # On hosting control panel, ensure MySQL service is active
   # Or contact hosting support
   ```

2. **Verify database credentials**:
   - Check `.env` file has correct database settings
   - Ensure passwords match what you set in database_setup.sql
   - Verify database name is `iice_production`

3. **Check host and port**:
   ```env
   DB_HOST=localhost  # or your hosting provider's DB host
   DB_PORT=3306       # default MySQL port
   ```

### Issue 3: Access Denied for User

**Error**: `django.db.utils.OperationalError: (1045, "Access denied for user 'iice_user'@'localhost'")`

**Solutions**:
1. **Reset user password**:
   ```sql
   ALTER USER 'iice_user'@'localhost' IDENTIFIED BY 'your_new_password';
   FLUSH PRIVILEGES;
   ```

2. **Check user exists**:
   ```sql
   SELECT User, Host FROM mysql.user WHERE User = 'iice_user';
   ```

3. **Recreate user if needed**:
   ```sql
   DROP USER IF EXISTS 'iice_user'@'localhost';
   CREATE USER 'iice_user'@'localhost' IDENTIFIED BY 'your_secure_password';
   GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER ON iice_production.* TO 'iice_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

### Issue 4: Database Does Not Exist

**Error**: `django.db.utils.OperationalError: (1049, "Unknown database 'iice_production'")`

**Solution**:
```sql
-- Create the database
CREATE DATABASE iice_production CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Verify it was created
SHOW DATABASES LIKE 'iice_production';
```

### Issue 5: Character Set Issues

**Error**: Garbled text or encoding errors

**Solution**:
1. **Ensure database uses UTF8MB4**:
   ```sql
   ALTER DATABASE iice_production CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

2. **Update Django settings**:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'OPTIONS': {
               'charset': 'utf8mb4',
               'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
           },
       }
   }
   ```

### Issue 6: Migration Errors

**Error**: Various migration-related errors

**Solutions**:
1. **Check migration status**:
   ```bash
   python manage.py showmigrations
   ```

2. **Run migrations step by step**:
   ```bash
   python manage.py migrate --run-syncdb
   python manage.py migrate authentication
   python manage.py migrate Admin
   python manage.py migrate
   ```

3. **If migrations are corrupted**:
   ```bash
   # Backup your data first!
   python manage.py migrate --fake-initial
   ```

### Issue 7: Permission Denied on Hosting

**Error**: Permission errors when creating database or user

**Solutions**:
1. **Use hosting control panel**:
   - Log into your hosting control panel
   - Navigate to MySQL/Database section
   - Create database and user through the interface

2. **Contact hosting support**:
   - Some hosting providers restrict direct SQL user creation
   - Ask them to run the database_setup.sql script

3. **Use phpMyAdmin** (if available):
   - Access phpMyAdmin from control panel
   - Import the database_setup.sql file

## 🔍 Diagnostic Commands

### Test Database Connection
```python
# Create test_db_connection.py
import os
import django
from django.conf import settings
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'IICE.settings_production')
django.setup()

try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        print("✅ Database connection successful!")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
```

### Check Database Settings
```python
# Add to Django shell: python manage.py shell
from django.conf import settings
print("Database settings:")
for key, value in settings.DATABASES['default'].items():
    if key != 'PASSWORD':
        print(f"{key}: {value}")
    else:
        print(f"{key}: {'*' * len(str(value))}")
```

### Verify MySQL Version
```sql
SELECT VERSION();
```

## 🚨 Emergency Recovery

### If Database is Corrupted
1. **Backup current state**:
   ```bash
   mysqldump -u iice_backup -p iice_production > backup_$(date +%Y%m%d).sql
   ```

2. **Drop and recreate database**:
   ```sql
   DROP DATABASE IF EXISTS iice_production;
   CREATE DATABASE iice_production CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```

3. **Restore from backup**:
   ```bash
   mysql -u iice_user -p iice_production < backup_20240101.sql
   ```

4. **Run fresh migrations**:
   ```bash
   python manage.py migrate
   ```

### If All Else Fails
1. **Use SQLite for testing**:
   ```python
   # Temporarily in settings_production.py
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.sqlite3',
           'NAME': BASE_DIR / 'db.sqlite3',
       }
   }
   ```

2. **Contact hosting support** with:
   - Error messages
   - Database configuration details
   - Steps you've already tried

## 📞 Getting Help

### Information to Provide When Seeking Help
1. **Exact error message**
2. **Hosting provider details**
3. **Django version**: `python -m django --version`
4. **MySQL version**: `SELECT VERSION();`
5. **Python version**: `python --version`
6. **Database settings** (without passwords)

### Useful Commands for Support
```bash
# Check Django configuration
python manage.py check --deploy

# Test database connection
python manage.py dbshell

# Show migration status
python manage.py showmigrations

# Collect system info
python -m django --version
python --version
pip list | grep -i mysql
```

---

**Remember**: Always backup your database before making changes!