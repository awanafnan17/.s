#!/usr/bin/env python
"""
Security Configuration Script for IICE CRM Production Deployment
This script helps configure security settings for production deployment.
"""

import os
import sys
import secrets
import string
from pathlib import Path

def generate_secret_key(length=50):
    """Generate a secure Django SECRET_KEY."""
    characters = string.ascii_letters + string.digits + '!@#$%^&*(-_=+)'
    return ''.join(secrets.choice(characters) for _ in range(length))

def create_security_checklist():
    """Create a security checklist for production deployment."""
    checklist = '''
# IICE CRM Production Security Checklist

## ✅ Essential Security Steps

### 1. Environment Variables
- [ ] Set DEBUG=False in production
- [ ] Generate and set a new SECRET_KEY
- [ ] Configure ALLOWED_HOSTS with your domain
- [ ] Use encrypted email passwords
- [ ] Set secure database credentials

### 2. HTTPS/SSL Configuration
- [ ] Enable SSL certificate on hosting provider
- [ ] Update settings to enforce HTTPS
- [ ] Test SSL certificate validity
- [ ] Configure HSTS headers

### 3. Database Security
- [ ] Use strong database passwords
- [ ] Create dedicated database user with minimal privileges
- [ ] Enable database connection encryption if available
- [ ] Regular database backups

### 4. File Permissions
- [ ] Set proper file permissions (755 for directories, 644 for files)
- [ ] Secure media upload directory
- [ ] Protect sensitive configuration files
- [ ] Ensure log files are not publicly accessible

### 5. Web Server Security
- [ ] Configure security headers
- [ ] Disable server signature/version disclosure
- [ ] Set up proper error pages
- [ ] Configure rate limiting if available

### 6. Application Security
- [ ] Keep Django and dependencies updated
- [ ] Review and secure admin interface
- [ ] Implement proper user authentication
- [ ] Validate all user inputs

### 7. Monitoring and Logging
- [ ] Set up error logging
- [ ] Monitor for suspicious activities
- [ ] Regular security audits
- [ ] Backup and recovery procedures

## 🔒 Security Headers Configuration

Add these headers to your web server configuration:

```apache
# Apache .htaccess
Header always set X-Content-Type-Options nosniff
Header always set X-Frame-Options DENY
Header always set X-XSS-Protection "1; mode=block"
Header always set Referrer-Policy "strict-origin-when-cross-origin"
Header always set Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self';"
```

```nginx
# Nginx configuration
add_header X-Content-Type-Options nosniff;
add_header X-Frame-Options DENY;
add_header X-XSS-Protection "1; mode=block";
add_header Referrer-Policy "strict-origin-when-cross-origin";
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self';";
```

## 🚨 Security Incident Response

### If you suspect a security breach:
1. Immediately change all passwords
2. Review access logs
3. Update all dependencies
4. Scan for malware
5. Notify users if data was compromised
6. Document the incident

## 📞 Security Resources

- Django Security Documentation: https://docs.djangoproject.com/en/stable/topics/security/
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Mozilla Security Guidelines: https://infosec.mozilla.org/guidelines/web_security

---

**Remember**: Security is an ongoing process, not a one-time setup!
'''
    
    checklist_path = Path(__file__).parent / 'SECURITY_CHECKLIST.md'
    try:
        with open(checklist_path, 'w') as f:
            f.write(checklist)
        print(f"✅ Created security checklist: {checklist_path}")
    except Exception as e:
        print(f"⚠️  Warning: Could not create security checklist: {e}")

def create_ssl_setup_guide():
    """Create SSL setup guide for the hosting provider."""
    ssl_guide = '''
# SSL/HTTPS Setup Guide for da600.is.cc

## Step 1: Enable SSL in Control Panel

1. Log in to your hosting control panel: https://da600.is.cc:2222/evo/
2. Navigate to SSL/TLS section
3. Enable SSL certificate for your domain
4. Choose between:
   - Free Let's Encrypt certificate (recommended)
   - Upload your own certificate
   - Purchase SSL certificate from provider

## Step 2: Force HTTPS Redirect

### Option A: Via Control Panel
1. Look for "Force HTTPS" or "SSL Redirect" option
2. Enable it for your domain

### Option B: Via .htaccess
Add this to your .htaccess file:

```apache
# Force HTTPS redirect
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
```

## Step 3: Update Django Settings

After SSL is active, uncomment these lines in `settings_production.py`:

```python
# SSL/HTTPS Settings (enable when SSL is configured)
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

## Step 4: Test SSL Configuration

1. Visit your site with https://
2. Check for SSL certificate validity
3. Test SSL configuration: https://www.ssllabs.com/ssltest/
4. Verify all resources load over HTTPS

## Step 5: Update External References

1. Update any hardcoded HTTP URLs to HTTPS
2. Update social media links
3. Update API endpoints
4. Update email templates with HTTPS links

## Troubleshooting SSL Issues

### Mixed Content Errors
- Ensure all resources (CSS, JS, images) use HTTPS
- Use protocol-relative URLs: `//example.com/style.css`
- Or use Django's `{% load static %}` template tag

### Certificate Errors
- Verify certificate covers your domain
- Check certificate expiration date
- Ensure certificate chain is complete

### Redirect Loops
- Check for conflicting redirect rules
- Verify Django SSL settings are correct
- Check hosting provider's SSL configuration

---

**Note**: Always test SSL configuration thoroughly before going live!
'''
    
    ssl_guide_path = Path(__file__).parent / 'SSL_SETUP_GUIDE.md'
    try:
        with open(ssl_guide_path, 'w') as f:
            f.write(ssl_guide)
        print(f"✅ Created SSL setup guide: {ssl_guide_path}")
    except Exception as e:
        print(f"⚠️  Warning: Could not create SSL setup guide: {e}")

def create_secure_env_template():
    """Create a secure environment template with generated values."""
    secret_key = generate_secret_key()
    
    secure_env = f'''# SECURE PRODUCTION ENVIRONMENT CONFIGURATION
# Generated on: {os.popen('date').read().strip()}

# CRITICAL: Keep this file secure and never commit to version control!

# Django Core Settings
DEBUG=False
SECRET_KEY={secret_key}
ALLOWED_HOSTS=da600.is.cc,www.da600.is.cc,localhost,127.0.0.1

# Database Configuration (Update with your actual values)
DB_NAME=iice_production
DB_USER=iice_user
DB_PASSWORD=CHANGE_THIS_TO_SECURE_PASSWORD
DB_HOST=localhost
DB_PORT=3306

# Email Configuration (Use encrypted passwords)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=indrivecopy@gmail.com

# Email Encryption (Generate these using management command)
EMAIL_ENCRYPTION_KEY=GENERATE_USING_ENCRYPT_EMAIL_PASSWORD_COMMAND
EMAIL_HOST_PASSWORD_ENCRYPTED=GENERATE_USING_ENCRYPT_EMAIL_PASSWORD_COMMAND

# Alternative: Plain text email password (less secure)
# EMAIL_HOST_PASSWORD=your-gmail-app-password

DEFAULT_FROM_EMAIL=indrivecopy@gmail.com

# Admin Configuration
ADMIN_EMAIL=admin@iice.com
SERVER_EMAIL=server@iice.com

# Logging Level
DJANGO_LOG_LEVEL=INFO

# Time Zone
TIME_ZONE=UTC

# Security Settings (Enable after SSL is configured)
# SECURE_SSL_REDIRECT=True
# SESSION_COOKIE_SECURE=True
# CSRF_COOKIE_SECURE=True

# Optional: Cache Configuration
# REDIS_URL=redis://127.0.0.1:6379/1

# Hosting Provider Specific
HOSTING_PROVIDER=da600.is.cc
DOMAIN_NAME=da600.is.cc
'''
    
    secure_env_path = Path(__file__).parent / '.env.secure'
    try:
        with open(secure_env_path, 'w') as f:
            f.write(secure_env)
        print(f"✅ Created secure environment template: {secure_env_path}")
        print(f"🔑 Generated new SECRET_KEY: {secret_key[:20]}...")
        print("⚠️  IMPORTANT: Update database password and email settings!")
    except Exception as e:
        print(f"⚠️  Warning: Could not create secure environment template: {e}")

def main():
    """Main function to set up security configurations."""
    print("🔒 IICE CRM Security Setup")
    print("=" * 40)
    
    print("\n📋 Creating security checklist...")
    create_security_checklist()
    
    print("\n🔐 Creating SSL setup guide...")
    create_ssl_setup_guide()
    
    print("\n🔑 Creating secure environment template...")
    create_secure_env_template()
    
    print("\n✅ Security setup completed!")
    print("\n📋 Next steps:")
    print("1. Review the SECURITY_CHECKLIST.md file")
    print("2. Follow the SSL_SETUP_GUIDE.md for HTTPS configuration")
    print("3. Update .env.secure with your actual values")
    print("4. Copy .env.secure to .env on your production server")
    print("5. Set proper file permissions (600) for .env file")
    
    print("\n🚨 Security Reminders:")
    print("- Never commit .env files to version control")
    print("- Use strong, unique passwords for all accounts")
    print("- Keep Django and dependencies updated")
    print("- Enable SSL/HTTPS before going live")
    print("- Regular security audits and backups")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())