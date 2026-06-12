"""User model with secure password hashing and brute force protection."""

import os
import logging
from django.db import models
from django.contrib.auth.hashers import make_password, check_password as django_check_password
from django.utils import timezone
from django.utils.text import slugify

logger = logging.getLogger('crm.auth')


def profile_photo_path(instance, filename):
    """Generate safe upload path for profile photos."""
    extension = filename.split('.')[-1].lower()
    safe_name = f"{slugify(instance.first_name)}_{slugify(instance.last_name)}_{slugify(instance.email)}.{extension}"
    return f"faculty_profiles/{safe_name}"


def cnic_photo_path(instance, filename):
    """Generate safe upload path for CNIC photos."""
    extension = filename.split('.')[-1].lower()
    safe_name = f"{slugify(instance.first_name)}_{slugify(instance.last_name)}_cnic.{extension}"
    return f"faculty_cnic/{safe_name}"


def degree_photo_path(instance, filename):
    """Generate safe upload path for degree photos."""
    extension = filename.split('.')[-1].lower()
    safe_name = f"{slugify(instance.first_name)}_{slugify(instance.last_name)}_degree.{extension}"
    return f"faculty_degrees/{safe_name}"


class User(models.Model):
    """Custom User model with password hashing, brute force protection, and audit fields."""

    USER_TYPE_CHOICES = [
        (1, 'Admin'),
        (2, 'Moderator'),
        (3, 'Teacher'),
    ]

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
    ]

    # Core fields
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)  # Increased for hashed passwords
    profile_photo = models.ImageField(upload_to=profile_photo_path, blank=True, null=True)
    usertype = models.PositiveSmallIntegerField(choices=USER_TYPE_CHOICES, default=3)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active')
    mobile_no = models.CharField(max_length=15, blank=True, null=True)
    cnic = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    joining_date = models.DateField(null=True, blank=True)
    cnic_photo = models.ImageField(upload_to=cnic_photo_path, blank=True, null=True)
    degree_photo = models.ImageField(upload_to=degree_photo_path, blank=True, null=True)

    # Security fields
    failed_login_attempts = models.PositiveIntegerField(default=0)
    lockout_until = models.DateTimeField(null=True, blank=True)
    last_login = models.DateTimeField(null=True, blank=True)
    last_login_ip = models.GenericIPAddressField(null=True, blank=True)

    # Audit
    updated_at = models.DateTimeField(auto_now=True)

    def set_password(self, raw_password: str) -> None:
        """Hash and store password using Django's PBKDF2 hasher."""
        self.password = make_password(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """
        Verify password against stored hash.
        Handles legacy plaintext migration: if the stored password is not
        a valid hash, compare directly and auto-migrate to hashed on success.
        """
        stored = self.password

        # Check if already hashed (Django hashes contain $ separators)
        if '$' in stored and len(stored) > 50:
            return django_check_password(raw_password, stored)

        # Legacy plaintext comparison with constant-time comparison
        import hmac
        if hmac.compare_digest(raw_password.encode('utf-8'), stored.encode('utf-8')):
            # Auto-migrate to hashed password on successful login
            logger.info(f"Auto-migrating plaintext password for user: {self.email}")
            self.set_password(raw_password)
            self.save(update_fields=['password'])
            return True

        return False

    @property
    def is_locked_out(self) -> bool:
        """Check if user account is currently locked due to too many failed attempts."""
        if self.lockout_until and self.lockout_until > timezone.now():
            return True
        return False

    @property
    def lockout_remaining_seconds(self) -> int:
        """Seconds remaining in lockout period. Returns 0 if not locked."""
        if self.is_locked_out:
            delta = self.lockout_until - timezone.now()
            return max(0, int(delta.total_seconds()))
        return 0

    def record_failed_login(self) -> None:
        """Record a failed login attempt. Lock account after 5 attempts."""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 5:
            # Exponential backoff: 5min, 15min, 30min, 1hr, etc.
            multiplier = min(self.failed_login_attempts - 4, 6)
            lockout_minutes = 5 * (2 ** (multiplier - 1))
            self.lockout_until = timezone.now() + timezone.timedelta(minutes=lockout_minutes)
            logger.warning(
                f"Account locked for {lockout_minutes}min due to {self.failed_login_attempts} "
                f"failed attempts: {self.email}"
            )
        self.save(update_fields=['failed_login_attempts', 'lockout_until'])

    def record_successful_login(self, ip_address: str = None) -> None:
        """Reset failed attempts and record login metadata."""
        self.failed_login_attempts = 0
        self.lockout_until = None
        self.last_login = timezone.now()
        if ip_address:
            self.last_login_ip = ip_address
        self.save(update_fields=[
            'failed_login_attempts', 'lockout_until', 'last_login', 'last_login_ip'
        ])

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
