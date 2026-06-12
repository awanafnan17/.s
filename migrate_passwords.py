"""
One-time script to hash all existing plaintext passwords.

Usage: python manage.py shell < migrate_passwords.py
   OR: python manage.py runscript migrate_passwords  (if django-extensions installed)

This script:
1. Scans all users for plaintext (unhashed) passwords
2. Hashes them using Django's PBKDF2 hasher
3. Reports how many were migrated

SAFE TO RE-RUN: Already-hashed passwords are skipped.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'IICE.settings')
django.setup()

from authentication.models import User


def migrate():
    users = User.objects.all()
    migrated = 0
    already_hashed = 0
    
    for user in users:
        # Check if password is already hashed (contains $ and is 50+ chars)
        if '$' in user.password and len(user.password) >= 50:
            already_hashed += 1
            continue
        
        # It's plaintext — hash it
        raw_password = user.password
        user.set_password(raw_password)
        user.save(update_fields=['password'])
        migrated += 1
        print(f"  Migrated: {user.email} ({user.get_usertype_display()})")
    
    print(f"\nDone.")
    print(f"  Migrated:       {migrated} passwords to PBKDF2 hash")
    print(f"  Already hashed: {already_hashed}")
    print(f"  Total users:    {users.count()}")


if __name__ == '__main__':
    migrate()
else:
    migrate()
