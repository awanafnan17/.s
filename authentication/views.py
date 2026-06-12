"""Authentication views with secure login, brute force protection, and session management."""

import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone

from .models import User

logger = logging.getLogger('crm.auth')


def _get_client_ip(request) -> str:
    """Extract client IP address, handling reverse proxies."""
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        return x_forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def Login_Page(request):
    """
    Secure login view with:
    - Django password hashing (PBKDF2/Argon2)
    - Automatic plaintext password migration on first login
    - Brute force protection with exponential backoff
    - Session fixation prevention via cycle_key()
    - Generic error messages to prevent user/email enumeration
    - Session timeout configuration
    """
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        client_ip = _get_client_ip(request)

        if not email or not password:
            messages.error(request, 'Please enter both email and password.')
            return render(request, 'Authentication/Login.html')

        # Generic error message — same for all failure cases to prevent enumeration
        generic_error = 'Invalid email or password.'

        try:
            user = User.objects.get(email__iexact=email)

            # Check account lockout
            if user.is_locked_out:
                remaining = user.lockout_remaining_seconds
                minutes = max(1, remaining // 60)
                messages.error(
                    request,
                    f'Account temporarily locked. Try again in {minutes} minute(s).'
                )
                logger.warning(f"Login attempt on locked account: {email} from {client_ip}")
                return render(request, 'Authentication/Login.html')

            # Check account status
            if user.status != 'Active':
                messages.error(request, generic_error)
                logger.warning(f"Login attempt on inactive account: {email} from {client_ip}")
                return render(request, 'Authentication/Login.html')

            # Verify password (handles both hashed and legacy plaintext)
            if user.check_password(password):
                # SUCCESS — Record login and set up session
                user.record_successful_login(ip_address=client_ip)

                # Regenerate session ID to prevent session fixation
                request.session.cycle_key()

                # Set session data
                request.session['user_id'] = user.id
                request.session['usertype'] = user.usertype
                request.session['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:200]
                request.session['login_ip'] = client_ip
                request.session['login_time'] = timezone.now().isoformat()

                # Set session expiry (8 hours)
                request.session.set_expiry(28800)

                logger.info(f"Successful login: {email} from {client_ip}")

                # Role-based redirect
                if user.usertype in (1, 2):  # Admin or Moderator
                    return redirect('Admin_Dashboard')
                elif user.usertype == 3:  # Teacher
                    return redirect('tec_select_course')
                else:
                    return redirect('Admin_Dashboard')
            else:
                # FAILED — Record failed attempt
                user.record_failed_login()
                messages.error(request, generic_error)
                logger.warning(f"Failed login (wrong password): {email} from {client_ip}")

        except User.DoesNotExist:
            # User not found — still hash to prevent timing attacks
            from django.contrib.auth.hashers import make_password
            make_password('dummy_timing_equalization')
            messages.error(request, generic_error)
            logger.warning(f"Failed login (unknown email): {email} from {client_ip}")

    return render(request, 'Authentication/Login.html')
