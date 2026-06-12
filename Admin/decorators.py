"""
Role-Based Access Control (RBAC) decorators for the IICE CRM.

Usage:
    @login_required           — Any authenticated user
    @admin_required           — Admin (1) or Moderator (2) only
    @admin_only               — Admin (1) only
    @role_required(1, 2, 3)   — Specific roles
"""

import logging
from functools import wraps
from typing import Callable

from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib import messages

from authentication.models import User

logger = logging.getLogger('crm.security')

# Role constants
ROLE_ADMIN = 1
ROLE_MODERATOR = 2
ROLE_TEACHER = 3


def login_required(view_func: Callable) -> Callable:
    """
    Require authenticated session with a valid, active user.
    Validates user_id in session AND verifies user still exists and is active.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        user_id = request.session.get('user_id')
        if not user_id:
            if _is_ajax(request):
                return JsonResponse({'success': False, 'error': 'Authentication required.'}, status=401)
            return redirect('home')

        # Verify user exists and is active
        try:
            user = User.objects.get(id=user_id, status='Active')
            # Cache on request to avoid re-querying in views
            request._cached_user = user
        except User.DoesNotExist:
            logger.warning(f"Session references invalid/inactive user_id={user_id}, flushing session")
            request.session.flush()
            if _is_ajax(request):
                return JsonResponse({'success': False, 'error': 'Session expired.'}, status=401)
            messages.error(request, 'Your session has expired. Please log in again.')
            return redirect('home')

        return view_func(request, *args, **kwargs)
    return wrapper


def role_required(*allowed_roles: int) -> Callable:
    """
    Require specific user roles. Must be used AFTER @login_required.
    
    Usage:
        @login_required
        @role_required(ROLE_ADMIN, ROLE_MODERATOR)
        def my_view(request): ...
    """
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            user_role = request.session.get('usertype')
            if user_role not in allowed_roles:
                logger.warning(
                    f"Unauthorized access: user_id={request.session.get('user_id')}, "
                    f"role={user_role}, required={allowed_roles}, path={request.path}"
                )
                if _is_ajax(request):
                    return JsonResponse({'success': False, 'error': 'Insufficient permissions.'}, status=403)
                messages.error(request, 'You do not have permission to access this page.')
                # Redirect teachers to attendance, others to dashboard
                if user_role == ROLE_TEACHER:
                    return redirect('tec_select_course')
                return redirect('Admin_Dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(view_func: Callable) -> Callable:
    """Shortcut: require Admin (1) or Moderator (2)."""
    @wraps(view_func)
    @login_required
    @role_required(ROLE_ADMIN, ROLE_MODERATOR)
    def wrapper(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_only(view_func: Callable) -> Callable:
    """Shortcut: require Admin (1) only — not moderators."""
    @wraps(view_func)
    @login_required
    @role_required(ROLE_ADMIN)
    def wrapper(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)
    return wrapper


def teacher_redirect_to_attendance(view_func: Callable) -> Callable:
    """
    Legacy decorator — redirects Teachers to attendance page.
    Kept for backward compatibility but should be replaced with @role_required.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        session_usertype = request.session.get('usertype')
        if session_usertype == ROLE_TEACHER:
            return redirect('tec_select_course')
        return view_func(request, *args, **kwargs)
    return wrapper


def _is_ajax(request) -> bool:
    """Check if request is AJAX (XMLHttpRequest)."""
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'
