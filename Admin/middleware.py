"""
Optimized SessionStatusMiddleware — skips static files, uses efficient queries.
DEPRECATED: Use 'python manage.py update_session_status' via cron instead.
Kept here as a fallback but REMOVED from MIDDLEWARE in settings.py.
"""

import logging
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('crm.admin')


class SessionStatusMiddleware(MiddlewareMixin):
    """
    DEPRECATED — Use management command instead.
    
    If re-enabled, this version:
    1. Skips static/media file requests
    2. Only runs once per minute (not every request)
    3. Uses bulk_update instead of individual saves
    """

    _last_check = None
    _check_interval_seconds = 60  # Only check once per minute

    def process_request(self, request):
        # Skip static and media files
        path = request.path
        if path.startswith(('/static/', '/media/', '/favicon.ico')):
            return None

        # Throttle: only check once per minute
        now = timezone.now()
        if (SessionStatusMiddleware._last_check and
                (now - SessionStatusMiddleware._last_check).total_seconds() < self._check_interval_seconds):
            return None
        SessionStatusMiddleware._last_check = now

        try:
            from .models import Sessions, StudentSession

            current_date = now.date()
            expired = Sessions.objects.filter(
                status='Active',
                end_date__lt=current_date
            )

            if expired.exists():
                count = expired.update(status='Completed')

                # Bulk update student sessions
                StudentSession.objects.filter(
                    session__in=expired, status='Active'
                ).update(status='Completed')

                if count > 0:
                    logger.info(f"Auto-completed {count} expired sessions via middleware")

        except Exception:
            logger.exception("Error in SessionStatusMiddleware")

        return None