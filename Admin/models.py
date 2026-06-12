"""Domain models for the IICE CRM.

Money fields use DecimalField for precision.
Soft delete enabled on Student and Session.
Audit fields (created_at / updated_at) on every domain model.
"""

import os
from decimal import Decimal
from typing import Optional

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import ProtectedError
from django.utils import timezone
from django.utils.text import slugify

from authentication.models import User


# ─────────────────────────────────────────────────────────────
#  Upload path helpers
# ─────────────────────────────────────────────────────────────

def student_profile_photo_path(instance, filename):
    return f"student_profiles/{instance.rollno}/{filename}"

def student_cnic_photo_path(instance, filename):
    return f"student_cnic/{instance.rollno}/{filename}"

def student_degree_photo_path(instance, filename):
    return f"student_degrees/{instance.rollno}/{filename}"

def session_photo_path(instance, filename):
    return f"session_photos/{slugify(instance.session_name)}/{filename}"


# ─────────────────────────────────────────────────────────────
#  Soft-delete managers
# ─────────────────────────────────────────────────────────────

class SoftDeleteManager(models.Manager):
    """Default manager that hides soft-deleted rows."""

    def get_queryset(self):
        return super().get_queryset().filter(deleted_at__isnull=True)


class AllObjectsManager(models.Manager):
    """Manager that returns ALL rows including soft-deleted ones (for admin recovery)."""

    def get_queryset(self):
        return super().get_queryset()


# ─────────────────────────────────────────────────────────────
#  Student
# ─────────────────────────────────────────────────────────────

class Student(models.Model):
    """A student enrolled at IICE Academy."""

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Completed', 'Completed'),
    ]
    INACTIVE_REASON_CHOICES = [
        ('Freeze', 'Freeze'),
        ('Left', 'Left'),
        ('Expelled', 'Expelled'),
        ('', 'None'),
    ]

    rollno = models.CharField(max_length=100, blank=True, null=True, unique=True)
    student_name = models.CharField(max_length=50, blank=True, null=True)
    father_name = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(unique=True, blank=True, null=True, db_index=True)
    cnic = models.CharField(max_length=15, blank=True, null=True)
    profile_photo = models.ImageField(upload_to=student_profile_photo_path, blank=True, null=True)
    cnic_photo = models.ImageField(upload_to=student_cnic_photo_path, blank=True, null=True)
    degree_photo = models.ImageField(upload_to=student_degree_photo_path, blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active', db_index=True)
    inactive_reason = models.CharField(max_length=10, choices=INACTIVE_REASON_CHOICES, default='', blank=True)
    mobile_no = models.CharField(max_length=15, blank=True, null=True)
    last_degree = models.CharField(max_length=50, blank=True, null=True)
    last_institution = models.CharField(max_length=50, blank=True, null=True)
    Temp_address = models.TextField(blank=True, null=True)
    Perm_address = models.TextField(blank=True, null=True)
    added_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='added_students'
    )

    # Audit
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    deleted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='deleted_students',
    )

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        indexes = [
            models.Index(fields=['status'], name='idx_student_status'),
            models.Index(fields=['created_at'], name='idx_student_created'),
        ]

    def generate_roll_number(self, session) -> str:
        """Generate a unique roll number for the student in the given session."""
        prefix = session.session_name[:3].upper()

        existing_students = Student.objects.filter(
            rollno__startswith=prefix,
            student_sessions__session=session
        ).exclude(rollno__isnull=True).exclude(rollno='')

        existing_numbers = []
        for student in existing_students:
            try:
                number_part = student.rollno.split('-')[1]
                existing_numbers.append(int(number_part))
            except (IndexError, ValueError):
                continue

        next_number = 1
        if existing_numbers:
            next_number = max(existing_numbers) + 1

        roll_number = f"{prefix}-{next_number:02d}"

        while Student.objects.filter(rollno=roll_number).exists():
            next_number += 1
            roll_number = f"{prefix}-{next_number:02d}"

        return roll_number

    @property
    def total_paid(self) -> Decimal:
        """Sum of confirmed payments across active sessions. Prefer total_paid_annotated in list views."""
        total = Decimal('0.00')
        for session in self.student_sessions.filter(status='Active'):
            for payment in session.student_payments.filter(payment_status='confirmed', amount__gt=0):
                total += payment.amount or Decimal('0.00')
        return total

    @property
    def total_fee(self) -> Decimal:
        """Total fee across active sessions, including a single registration fee on the primary session."""
        sessions_qs = self.student_sessions.filter(status='Active')

        base_total = Decimal('0.00')
        for s in sessions_qs:
            base_total += (s.fee or Decimal('0.00')) - (s.discount or Decimal('0.00'))

        primary_session = (
            sessions_qs.exclude(registration_date__isnull=True)
            .order_by('registration_date', 'id')
            .first()
            or sessions_qs.order_by('id').first()
        )

        one_time_reg_fee = Decimal('0.00')
        if primary_session:
            one_time_reg_fee = (
                primary_session.registration_fee
                if primary_session.registration_fee is not None
                else (primary_session.session.registration_fee or Decimal('0.00'))
            )

        return base_total + (one_time_reg_fee or Decimal('0.00'))

    @property
    def remaining_balance(self) -> Decimal:
        """Remaining balance owed by the student."""
        return max(Decimal('0.00'), self.total_fee - self.total_paid)

    @property
    def payment_status(self) -> str:
        """Display payment status: Paid / Partial / Unpaid."""
        if self.remaining_balance <= 0:
            return 'Paid'
        if self.total_paid > 0:
            return 'Partial'
        return 'Unpaid'

    def delete(self, deleted_by: Optional[User] = None, hard: bool = False, *args, **kwargs):
        """Soft delete by default. Blocks if confirmed payments exist."""
        if hard:
            return super().delete(*args, **kwargs)

        has_confirmed_payments = Payments.objects.filter(
            studentsession__student=self,
            payment_status='confirmed',
            amount__gt=0,
        ).exists()
        if has_confirmed_payments:
            raise ProtectedError(
                "Cannot delete student with confirmed payment history. Deactivate instead.",
                [],
            )

        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by
        self.status = 'Inactive'
        self.save(update_fields=['deleted_at', 'deleted_by', 'status', 'updated_at'])

    def __str__(self):
        return f"{self.student_name} ({self.rollno})"


# ─────────────────────────────────────────────────────────────
#  Sessions (course offerings)
# ─────────────────────────────────────────────────────────────

class Sessions(models.Model):
    """A course / session offered by the academy."""

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Completed', 'Completed'),
    ]

    SESSION_TYPE_CHOICES = [
        ('time_period', 'Time Period Session'),
        ('monthly', 'Monthly Session'),
    ]

    session_name = models.CharField(max_length=50)
    session_type = models.CharField(max_length=15, choices=SESSION_TYPE_CHOICES, default='time_period')
    start_date = models.DateField(null=True, blank=True, db_index=True)
    end_date = models.DateField(null=True, blank=True)
    session_photo = models.ImageField(upload_to=session_photo_path, blank=True, null=True)
    registration_fee = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    fee = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Fee for all session types",
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active', db_index=True)

    # Late fee policy
    late_fee_amount = models.DecimalField(
        max_digits=8, decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Late fee charged per overdue month (0 = no late fee).",
    )
    late_fee_grace_days = models.PositiveIntegerField(
        default=10,
        help_text="Days after due_day before late fee is applied.",
    )
    late_fee_maximum = models.DecimalField(
        max_digits=8, decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
        help_text="Maximum cumulative late fee (0 = no cap).",
    )
    due_day = models.PositiveSmallIntegerField(
        default=10,
        help_text="Day of month payments are due (1-28).",
    )

    # Audit
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Soft delete
    deleted_at = models.DateTimeField(null=True, blank=True, db_index=True)
    deleted_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='deleted_sessions',
    )

    objects = SoftDeleteManager()
    all_objects = AllObjectsManager()

    class Meta:
        indexes = [
            models.Index(fields=['status'], name='idx_sessions_status'),
            models.Index(fields=['start_date'], name='idx_sessions_start'),
        ]

    def clean(self):
        if not self.fee:
            raise ValidationError({'fee': 'Fee is required for all sessions.'})
        if not (1 <= self.due_day <= 28):
            raise ValidationError({'due_day': 'Due day must be between 1 and 28.'})

    def delete(self, deleted_by: Optional[User] = None, hard: bool = False, *args, **kwargs):
        """Soft delete by default. Blocks if confirmed payments exist on this session."""
        if hard:
            return super().delete(*args, **kwargs)

        confirmed_payments = Payments.objects.filter(
            studentsession__session=self,
            payment_status='confirmed',
            amount__gt=0,
        ).exists()
        if confirmed_payments:
            raise ProtectedError(
                "Cannot delete session with confirmed payment history. Archive it instead.",
                [],
            )

        self.deleted_at = timezone.now()
        self.deleted_by = deleted_by
        self.status = 'Inactive'
        self.save(update_fields=['deleted_at', 'deleted_by', 'status', 'updated_at'])

    def __str__(self):
        return f"{self.session_name} ({self.get_session_type_display()})"


# ─────────────────────────────────────────────────────────────
#  StudentSession (enrollment)
# ─────────────────────────────────────────────────────────────

class StudentSession(models.Model):
    """A student's enrollment in a session."""

    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Completed', 'Completed'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_sessions')
    session = models.ForeignKey(Sessions, on_delete=models.CASCADE, related_name='session_students')
    registration_date = models.DateField(null=True, blank=True)
    registration_fee = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    fee = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    due_date = models.DateField(null=True, blank=True)
    next_monthly_due = models.DateField(null=True, blank=True)
    discount = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Active', db_index=True)
    notes = models.TextField(blank=True, null=True)

    # Late fee state
    is_fee_waived = models.BooleanField(default=False)

    # Audit
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('student', 'session')]
        indexes = [
            models.Index(fields=['status'], name='idx_ss_status'),
            models.Index(fields=['session', 'status'], name='idx_ss_session_status'),
        ]

    def clean(self):
        super().clean()
        if self.status == 'Active':
            existing_active = StudentSession.objects.filter(
                student=self.student,
                status='Active'
            ).exclude(pk=self.pk)

            if existing_active.exists():
                raise ValidationError(
                    f'Student {self.student.student_name} is already enrolled in an active session: '
                    f'{existing_active.first().session.session_name}. '
                    f'Please complete or withdraw from the current session before enrolling in a new one.'
                )

    def save(self, *args, **kwargs):
        if not self.pk:
            has_previous = StudentSession.objects.filter(student=self.student).exists()
            if has_previous and self.registration_fee is None:
                self.registration_fee = Decimal('0.00')
                if not self.notes:
                    self.notes = ""
                self.notes += " [Registration fee waived - re-enrollment policy]"

        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def is_primary_session(self) -> bool:
        """True if this is the student's primary (earliest) active session."""
        sessions_qs = self.student.student_sessions.filter(status='Active')
        primary = (
            sessions_qs.exclude(registration_date__isnull=True)
            .order_by('registration_date', 'id')
            .first()
            or sessions_qs.order_by('id').first()
        )
        return bool(primary and primary.id == self.id)

    @property
    def session_paid(self) -> Decimal:
        """Confirmed non-late-fee payments for this session."""
        total = Decimal('0.00')
        for payment in self.student_payments.filter(
            payment_status='confirmed',
            amount__gt=0,
            is_late_fee_payment=False,
        ):
            total += payment.amount or Decimal('0.00')
        return total

    @property
    def session_balance(self) -> Decimal:
        """Remaining balance for this session (registration fee only on primary session)."""
        reg_fee = Decimal('0.00')
        if self.is_primary_session:
            reg_fee = (
                self.registration_fee
                if self.registration_fee is not None
                else (self.session.registration_fee or Decimal('0.00'))
            )
        total_fee = (self.fee or Decimal('0.00')) + reg_fee - (self.discount or Decimal('0.00'))
        return max(Decimal('0.00'), total_fee - self.session_paid)

    @property
    def session_total_fee(self) -> Decimal:
        """Total fee for this session (registration fee only on primary session)."""
        reg_fee = Decimal('0.00')
        if self.is_primary_session:
            reg_fee = (
                self.registration_fee
                if self.registration_fee is not None
                else (self.session.registration_fee or Decimal('0.00'))
            )
        return (self.fee or Decimal('0.00')) + reg_fee - (self.discount or Decimal('0.00'))

    def __str__(self):
        return f"{self.student} - {self.session}"


# ─────────────────────────────────────────────────────────────
#  Lead
# ─────────────────────────────────────────────────────────────

class Lead(models.Model):
    """An inquiry / prospective student."""

    INQUIRY_CHOICES = [
        ('Call', 'Call'),
        ('Message', 'Message'),
        ('Physical Visit', 'Physical Visit'),
    ]

    name = models.CharField(max_length=50)
    email = models.EmailField(unique=True, blank=True, null=True)
    mobile_no = models.CharField(max_length=15, blank=True, null=True)
    area_of_residence = models.CharField(max_length=100, blank=True, null=True)
    session = models.ForeignKey(Sessions, on_delete=models.SET_NULL, null=True, blank=True)
    date = models.DateField(auto_now_add=True)
    form_of_inquiry = models.CharField(max_length=20, choices=INQUIRY_CHOICES, default='Call')

    # Audit
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name}"


# ─────────────────────────────────────────────────────────────
#  Payments
# ─────────────────────────────────────────────────────────────

class Payments(models.Model):
    """Fee payment record — the single source of truth for revenue.

    Payment status:
        pending   — placeholder / unpaid installment
        confirmed — actual payment received
        refunded  — payment reversed
    """

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('refunded', 'Refunded'),
    ]

    studentsession = models.ForeignKey(
        StudentSession, on_delete=models.CASCADE, related_name='student_payments'
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        null=True, blank=True,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))],
    )
    date = models.DateField(blank=True, null=True, db_index=True)
    payment_status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUS_CHOICES,
        default='confirmed',
        db_index=True,
    )
    month = models.CharField(
        max_length=7,
        blank=True, null=True,
        db_index=True,
        help_text="YYYY-MM that this payment applies to (for monthly sessions / late fee tracking).",
    )

    # Late fee bookkeeping
    is_late_fee_payment = models.BooleanField(default=False, db_index=True)
    late_fee_waived = models.BooleanField(default=False)
    late_fee_waiver_reason = models.CharField(max_length=255, blank=True, null=True)
    late_fee_waived_by = models.ForeignKey(
        User, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='waived_late_fees',
    )

    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['studentsession', 'amount'], name='idx_pay_session_amount'),
            models.Index(fields=['studentsession', 'payment_status'], name='idx_pay_session_status'),
        ]

    def __str__(self):
        return f"Payment Rs.{self.amount} - {self.studentsession}"


# ─────────────────────────────────────────────────────────────
#  Attendance
# ─────────────────────────────────────────────────────────────

class Attendance(models.Model):
    """Daily attendance record."""

    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
    ]

    course = models.ForeignKey(Sessions, on_delete=models.CASCADE)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['course', 'date'], name='idx_attend_course_date'),
        ]


# ─────────────────────────────────────────────────────────────
#  Notification
# ─────────────────────────────────────────────────────────────

class Notification(models.Model):
    """System notifications surfaced to users."""

    CATEGORIES = [
        ('General', 'General'),
        ('Late Fee', 'Late fee'),
        ('New Entry', 'New Entry'),
        ('Deletion', 'Deletion'),
        ('New Fee', 'New Fee'),
        ('Updation', 'Updation'),
        ('Monthly Renewal', 'Monthly Renewal'),
        ('Payment', 'Payment'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    date = models.DateTimeField(auto_now_add=True)
    category = models.CharField(max_length=20, choices=CATEGORIES)
    content = models.TextField(max_length=200, blank=True, null=True)
    is_read = models.BooleanField(default=False, db_index=True)

    # Optional scoping fields for dedup (e.g. one late-fee notice per student/session/month)
    student_session = models.ForeignKey(
        StudentSession, on_delete=models.CASCADE,
        null=True, blank=True,
        related_name='notifications',
    )
    notification_month = models.CharField(
        max_length=7, blank=True, null=True,
        help_text="YYYY-MM key for deduplicating recurring notifications.",
    )

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['-date'], name='idx_notif_date_desc'),
            models.Index(fields=['user', 'is_read'], name='idx_notif_user_read'),
        ]
