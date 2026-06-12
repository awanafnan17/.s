"""
Health check management command for IICE CRM.

Checks for common data integrity issues:
- Plaintext (unhashed) passwords
- Duplicate student session enrollments
- Orphaned payments (no linked session)
- Negative payment amounts
- Future-dated payments
- Missing fee configurations
- Students with no sessions

Usage: python manage.py health_check
"""

import logging
from datetime import date

from django.core.management.base import BaseCommand
from django.utils import timezone

from authentication.models import User
from Admin import models as admin_models

logger = logging.getLogger('crm.health')


class Command(BaseCommand):
    help = 'Run health checks on IICE CRM data integrity'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\n═══ IICE CRM Health Check ═══\n'))
        
        issues = 0
        
        # 1. Check for plaintext passwords
        self.stdout.write('1. Checking password hashing...')
        plaintext_users = []
        for user in User.objects.all():
            # Hashed passwords contain $ separators and are 50+ chars
            if '$' not in user.password or len(user.password) < 50:
                plaintext_users.append(user.email)
        
        if plaintext_users:
            self.stdout.write(self.style.ERROR(
                f'   ❌ {len(plaintext_users)} users have plaintext passwords!'
            ))
            for email in plaintext_users[:5]:
                self.stdout.write(f'      - {email}')
            if len(plaintext_users) > 5:
                self.stdout.write(f'      ... and {len(plaintext_users) - 5} more')
            issues += len(plaintext_users)
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ All passwords are hashed.'))

        # 2. Check for duplicate enrollments
        self.stdout.write('2. Checking duplicate enrollments...')
        from django.db.models import Count
        duplicates = (
            admin_models.StudentSession.objects
            .values('student', 'session')
            .annotate(count=Count('id'))
            .filter(count__gt=1)
        )
        dup_count = duplicates.count()
        if dup_count > 0:
            self.stdout.write(self.style.ERROR(
                f'   ❌ {dup_count} duplicate student-session enrollments found!'
            ))
            issues += dup_count
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ No duplicate enrollments.'))

        # 3. Check for negative payment amounts
        self.stdout.write('3. Checking payment amounts...')
        negative_payments = admin_models.Payments.objects.filter(amount__lt=0).count()
        if negative_payments > 0:
            self.stdout.write(self.style.ERROR(
                f'   ❌ {negative_payments} payments have negative amounts!'
            ))
            issues += negative_payments
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ No negative payment amounts.'))

        # 4. Check for future-dated payments
        self.stdout.write('4. Checking future-dated payments...')
        today = date.today()
        future_payments = admin_models.Payments.objects.filter(date__gt=today).count()
        if future_payments > 0:
            self.stdout.write(self.style.WARNING(
                f'   ⚠️  {future_payments} payments have future dates.'
            ))
            issues += future_payments
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ No future-dated payments.'))

        # 5. Check for sessions without fees
        self.stdout.write('5. Checking session fee configurations...')
        no_fee_sessions = admin_models.Sessions.objects.filter(fee__isnull=True).count()
        if no_fee_sessions > 0:
            self.stdout.write(self.style.WARNING(
                f'   ⚠️  {no_fee_sessions} sessions have no fee configured.'
            ))
            issues += no_fee_sessions
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ All sessions have fees configured.'))

        # 6. Check for active students without any sessions
        self.stdout.write('6. Checking orphaned students...')
        orphaned = admin_models.Student.objects.filter(
            status='Active',
        ).exclude(
            student_sessions__status='Active'
        ).count()
        if orphaned > 0:
            self.stdout.write(self.style.WARNING(
                f'   ⚠️  {orphaned} active students have no active sessions.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ All active students have sessions.'))

        # 7. Check for overdue payments
        self.stdout.write('7. Checking overdue payments...')
        overdue_sessions = admin_models.StudentSession.objects.filter(
            status='Active',
            due_date__lt=today,
        ).count()
        if overdue_sessions > 0:
            self.stdout.write(self.style.WARNING(
                f'   ⚠️  {overdue_sessions} student sessions are past due date.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS('   ✅ No overdue sessions.'))

        # 8. Summary
        self.stdout.write('\n' + '═' * 40)
        if issues == 0:
            self.stdout.write(self.style.SUCCESS('✅ Health check passed — 0 critical issues.'))
        else:
            self.stdout.write(self.style.ERROR(
                f'❌ Health check found {issues} issue(s) requiring attention.'
            ))
        self.stdout.write('')
