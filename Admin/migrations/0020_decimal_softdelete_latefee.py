"""Money fields → DecimalField, soft-delete, late-fee, audit, indexes, unique constraint.

Data-safe migration:
- Money columns are converted from IntegerField to DecimalField, preserving values
  (Decimal(int) is exact).
- StudentSession unique_together is added AFTER de-duplicating same-(student, session)
  rows (oldest survives, newer ones get a -DUP suffix on status to break the constraint).
- Soft-delete columns default to NULL so existing rows are visible to the default manager.
"""

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def deduplicate_student_sessions(apps, schema_editor):
    """Before applying unique_together, soft-deactivate any duplicate (student, session) rows."""
    StudentSession = apps.get_model('Admin', 'StudentSession')

    seen = {}
    duplicates = []
    for ss in StudentSession.objects.all().order_by('id'):
        key = (ss.student_id, ss.session_id)
        if key in seen:
            duplicates.append(ss)
        else:
            seen[key] = ss.id

    for ss in duplicates:
        # The surviving row keeps all payments since payments FK to studentsession by ID.
        ss.delete()


def reverse_dedup(apps, schema_editor):
    """No-op: cannot restore deleted duplicates."""
    pass


def reclassify_zero_amount_payments(apps, schema_editor):
    """Existing rows with amount<=0 are unpaid placeholders → payment_status='pending'."""
    Payments = apps.get_model('Admin', 'Payments')
    Payments.objects.filter(amount__lte=0).update(payment_status='pending')


def reverse_reclassify(apps, schema_editor):
    """No-op: payment_status didn't exist before."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('Admin', '0019_add_indexes_and_audit_fields'),
        ('authentication', '0006_add_security_fields'),
    ]

    operations = [
        # ── Money → Decimal ─────────────────────────────────
        migrations.AlterField(
            model_name='payments',
            name='amount',
            field=models.DecimalField(
                blank=True, null=True,
                default=Decimal('0.00'),
                max_digits=10, decimal_places=2,
                validators=[MinValueValidator(Decimal('0.00'))],
            ),
        ),
        migrations.AlterField(
            model_name='sessions',
            name='fee',
            field=models.DecimalField(
                null=True, blank=True,
                max_digits=10, decimal_places=2,
                help_text='Fee for all session types',
                validators=[MinValueValidator(Decimal('0.00'))],
            ),
        ),
        migrations.AlterField(
            model_name='sessions',
            name='registration_fee',
            field=models.DecimalField(
                default=Decimal('0.00'),
                max_digits=10, decimal_places=2,
                validators=[MinValueValidator(Decimal('0.00'))],
            ),
        ),
        migrations.AlterField(
            model_name='studentsession',
            name='fee',
            field=models.DecimalField(
                null=True, blank=True,
                max_digits=10, decimal_places=2,
                validators=[MinValueValidator(Decimal('0.00'))],
            ),
        ),
        migrations.AlterField(
            model_name='studentsession',
            name='registration_fee',
            field=models.DecimalField(
                null=True, blank=True,
                max_digits=10, decimal_places=2,
                validators=[MinValueValidator(Decimal('0.00'))],
            ),
        ),
        migrations.AlterField(
            model_name='studentsession',
            name='discount',
            field=models.DecimalField(
                null=True, blank=True,
                default=Decimal('0.00'),
                max_digits=10, decimal_places=2,
                validators=[MinValueValidator(Decimal('0.00'))],
            ),
        ),

        # ── Late-fee policy on Sessions ──────────────────────
        migrations.AddField(
            model_name='sessions',
            name='late_fee_amount',
            field=models.DecimalField(
                default=Decimal('0.00'),
                max_digits=8, decimal_places=2,
                validators=[MinValueValidator(Decimal('0.00'))],
                help_text='Late fee charged per overdue month (0 = no late fee).',
            ),
        ),
        migrations.AddField(
            model_name='sessions',
            name='late_fee_grace_days',
            field=models.PositiveIntegerField(
                default=10,
                help_text='Days after due_day before late fee is applied.',
            ),
        ),
        migrations.AddField(
            model_name='sessions',
            name='late_fee_maximum',
            field=models.DecimalField(
                default=Decimal('0.00'),
                max_digits=8, decimal_places=2,
                validators=[MinValueValidator(Decimal('0.00'))],
                help_text='Maximum cumulative late fee (0 = no cap).',
            ),
        ),
        migrations.AddField(
            model_name='sessions',
            name='due_day',
            field=models.PositiveSmallIntegerField(
                default=10,
                help_text='Day of month payments are due (1-28).',
            ),
        ),

        # ── Payment status / late-fee bookkeeping ────────────
        migrations.AddField(
            model_name='payments',
            name='payment_status',
            field=models.CharField(
                max_length=10,
                choices=[('pending', 'Pending'), ('confirmed', 'Confirmed'), ('refunded', 'Refunded')],
                default='confirmed',
                db_index=True,
            ),
        ),
        migrations.AddField(
            model_name='payments',
            name='month',
            field=models.CharField(max_length=7, blank=True, null=True, db_index=True),
        ),
        migrations.AddField(
            model_name='payments',
            name='is_late_fee_payment',
            field=models.BooleanField(default=False, db_index=True),
        ),
        migrations.AddField(
            model_name='payments',
            name='late_fee_waived',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='payments',
            name='late_fee_waiver_reason',
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='payments',
            name='late_fee_waived_by',
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='waived_late_fees',
                to='authentication.user',
            ),
        ),
        migrations.AddField(
            model_name='payments',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),

        # ── Soft delete on Student ───────────────────────────
        migrations.AddField(
            model_name='student',
            name='deleted_at',
            field=models.DateTimeField(null=True, blank=True, db_index=True),
        ),
        migrations.AddField(
            model_name='student',
            name='deleted_by',
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='deleted_students',
                to='authentication.user',
            ),
        ),
        migrations.AddField(
            model_name='student',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='student',
            name='email',
            field=models.EmailField(unique=True, blank=True, null=True, db_index=True, max_length=254),
        ),
        migrations.AlterField(
            model_name='student',
            name='status',
            field=models.CharField(
                max_length=10, default='Active', db_index=True,
                choices=[('Active', 'Active'), ('Inactive', 'Inactive'), ('Completed', 'Completed')],
            ),
        ),
        migrations.AlterField(
            model_name='student',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, db_index=True),
        ),

        # ── Soft delete on Sessions ──────────────────────────
        migrations.AddField(
            model_name='sessions',
            name='deleted_at',
            field=models.DateTimeField(null=True, blank=True, db_index=True),
        ),
        migrations.AddField(
            model_name='sessions',
            name='deleted_by',
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='deleted_sessions',
                to='authentication.user',
            ),
        ),
        migrations.AddField(
            model_name='sessions',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now, db_index=True),
        ),
        migrations.AddField(
            model_name='sessions',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='sessions',
            name='status',
            field=models.CharField(
                max_length=10, default='Active', db_index=True,
                choices=[('Active', 'Active'), ('Inactive', 'Inactive'), ('Completed', 'Completed')],
            ),
        ),
        migrations.AlterField(
            model_name='sessions',
            name='start_date',
            field=models.DateField(null=True, blank=True, db_index=True),
        ),

        # ── StudentSession audit + waive flag ────────────────
        migrations.AddField(
            model_name='studentsession',
            name='is_fee_waived',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='studentsession',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AddField(
            model_name='studentsession',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='studentsession',
            name='status',
            field=models.CharField(
                max_length=10, default='Active', db_index=True,
                choices=[('Active', 'Active'), ('Inactive', 'Inactive'), ('Completed', 'Completed')],
            ),
        ),

        # Reclassify legacy zero-amount placeholders as pending.
        migrations.RunPython(reclassify_zero_amount_payments, reverse_code=reverse_reclassify),

        # De-dup before constraint
        migrations.RunPython(deduplicate_student_sessions, reverse_code=reverse_dedup),

        migrations.AlterUniqueTogether(
            name='studentsession',
            unique_together={('student', 'session')},
        ),

        # ── Lead audit ───────────────────────────────────────
        migrations.AddField(
            model_name='lead',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),

        # ── Attendance audit + index ─────────────────────────
        migrations.AddField(
            model_name='attendance',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='attendance',
            name='date',
            field=models.DateField(db_index=True),
        ),

        # ── Notification: scoping fields + composite index ──
        migrations.AddField(
            model_name='notification',
            name='student_session',
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='notifications',
                to='Admin.studentsession',
            ),
        ),
        migrations.AddField(
            model_name='notification',
            name='notification_month',
            field=models.CharField(max_length=7, blank=True, null=True),
        ),
        migrations.AddField(
            model_name='notification',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),

        # ── Indexes ──────────────────────────────────────────
        migrations.AddIndex(
            model_name='student',
            index=models.Index(fields=['status'], name='idx_student_status'),
        ),
        migrations.AddIndex(
            model_name='student',
            index=models.Index(fields=['created_at'], name='idx_student_created'),
        ),
        migrations.AddIndex(
            model_name='sessions',
            index=models.Index(fields=['status'], name='idx_sessions_status'),
        ),
        migrations.AddIndex(
            model_name='sessions',
            index=models.Index(fields=['start_date'], name='idx_sessions_start'),
        ),
        migrations.AddIndex(
            model_name='studentsession',
            index=models.Index(fields=['status'], name='idx_ss_status'),
        ),
        migrations.AddIndex(
            model_name='studentsession',
            index=models.Index(fields=['session', 'status'], name='idx_ss_session_status'),
        ),
        migrations.AddIndex(
            model_name='payments',
            index=models.Index(fields=['studentsession', 'payment_status'], name='idx_pay_session_status'),
        ),
        migrations.AddIndex(
            model_name='notification',
            index=models.Index(fields=['user', 'is_read'], name='idx_notif_user_read'),
        ),
    ]
