"""
Management command to update expired session statuses.
Replaces the SessionStatusMiddleware which ran on EVERY request.

Usage: python manage.py update_session_status
Cron:  0 * * * * cd /path/to/project && python manage.py update_session_status
"""

import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

from Admin.models import Sessions, StudentSession, Student, Notification
from authentication.models import User

logger = logging.getLogger('crm.admin')


class Command(BaseCommand):
    help = 'Update expired session statuses to Completed (run via cron every hour)'

    def handle(self, *args, **options):
        today = timezone.now().date()

        expired = Sessions.objects.filter(
            status='Active',
            end_date__lt=today,
        )

        if not expired.exists():
            self.stdout.write('No expired sessions found.')
            return

        total_sessions = 0
        total_students = 0

        for session in expired:
            session.status = 'Completed'
            session.save(update_fields=['status'])
            total_sessions += 1

            # Update student sessions
            student_sessions = StudentSession.objects.filter(
                session=session, status='Active'
            )
            for ss in student_sessions:
                ss.status = 'Completed'
                ss.save(update_fields=['status'])

                ss.student.status = 'Completed'
                ss.student.save(update_fields=['status'])
                total_students += 1

        self.stdout.write(self.style.SUCCESS(
            f'Completed {total_sessions} expired sessions, '
            f'{total_students} students updated.'
        ))

        logger.info(
            f"Auto-completed {total_sessions} expired sessions, "
            f"{total_students} students updated to Ex-Student status."
        )

        # Create notification for admin
        try:
            admin_user = User.objects.filter(usertype=1).first()
            if admin_user:
                Notification.objects.create(
                    user=admin_user,
                    category='General',
                    content=f"System completed {total_sessions} expired session(s). "
                            f"{total_students} students updated.",
                )
        except Exception:
            logger.exception("Failed to create session completion notification")
