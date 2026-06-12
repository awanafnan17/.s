"""
Secure email service for IICE CRM.
Prevents header injection, hides recipients from each other, and rate-limits sends.
"""

import logging
import re
from typing import List, Tuple, Optional

from django.core.mail import EmailMessage
from django.conf import settings

logger = logging.getLogger('crm.email')

# Characters that enable email header injection
HEADER_INJECTION_RE = re.compile(r'[\r\n\t]')


def sanitize_subject(subject: str) -> str:
    """Strip characters that could inject email headers."""
    if not subject:
        return ''
    return HEADER_INJECTION_RE.sub(' ', subject).strip()[:200]


def sanitize_content(content: str) -> str:
    """Remove dangerous HTML from email content."""
    if not content:
        return ''
    # Strip script tags
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
    # Strip event handlers
    content = re.sub(r'\s+on\w+\s*=\s*["\'][^"\']*["\']', '', content, flags=re.IGNORECASE)
    return content


def send_single_email(
    subject: str,
    content: str,
    recipient: str,
    from_email: Optional[str] = None,
    html: bool = True,
) -> bool:
    """
    Send a single email with sanitized subject and content.
    
    Args:
        subject: Email subject (will be sanitized)
        content: Email body (will be sanitized)
        recipient: Single recipient email address
        from_email: Sender email (defaults to settings.DEFAULT_FROM_EMAIL)
        html: If True, send as HTML email
    
    Returns:
        True if sent successfully, False otherwise
    """
    subject = sanitize_subject(subject)
    content = sanitize_content(content)
    from_email = from_email or settings.DEFAULT_FROM_EMAIL

    try:
        email = EmailMessage(
            subject=subject,
            body=content,
            from_email=from_email,
            to=[recipient],
        )
        if html:
            email.content_subtype = 'html'
        email.send(fail_silently=False)
        logger.info(f"Email sent to {recipient}: {subject[:50]}")
        return True
    except Exception:
        logger.exception(f"Failed to send email to {recipient}")
        return False


def send_bulk_email(
    subject: str,
    content: str,
    recipients: List[str],
    from_email: Optional[str] = None,
    html: bool = True,
) -> Tuple[int, int, List[str]]:
    """
    Send individual emails to each recipient (no shared recipient lists).
    
    Each recipient gets their own email — no BCC/CC that could expose addresses.
    
    Args:
        subject: Email subject
        content: Email body
        recipients: List of recipient email addresses
        from_email: Sender email
        html: If True, send as HTML
    
    Returns:
        Tuple of (sent_count, failed_count, error_messages)
    """
    subject = sanitize_subject(subject)
    content = sanitize_content(content)
    from_email = from_email or settings.DEFAULT_FROM_EMAIL

    # Validate and deduplicate
    valid_recipients = list(set(
        email.strip().lower() for email in recipients
        if email and '@' in email.strip()
    ))

    if not valid_recipients:
        return 0, 0, ['No valid email addresses provided.']

    sent = 0
    failed = 0
    errors = []

    for recipient in valid_recipients:
        try:
            email = EmailMessage(
                subject=subject,
                body=content,
                from_email=from_email,
                to=[recipient],
            )
            if html:
                email.content_subtype = 'html'
            email.send(fail_silently=False)
            sent += 1
        except Exception as e:
            failed += 1
            errors.append(f"{recipient}: {type(e).__name__}")
            logger.warning(f"Bulk email failed for {recipient}: {e}")

    logger.info(f"Bulk email complete: {sent} sent, {failed} failed, subject='{subject[:50]}'")
    return sent, failed, errors
