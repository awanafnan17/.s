"""
File upload validation for IICE CRM.
Validates file type, size, and content using magic bytes.
"""

import logging
import os
from typing import Tuple

logger = logging.getLogger('crm.security')

# Maximum file upload sizes
MAX_UPLOAD_SIZE_MB = 5
MAX_UPLOAD_SIZE_BYTES = MAX_UPLOAD_SIZE_MB * 1024 * 1024
MAX_PDF_PAGES = 500

# Magic bytes for file type detection
MAGIC_BYTES = {
    b'%PDF': 'application/pdf',
    b'\xff\xd8\xff': 'image/jpeg',
    b'\x89PNG': 'image/png',
    b'GIF87a': 'image/gif',
    b'GIF89a': 'image/gif',
}

ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
ALLOWED_PDF_EXTENSIONS = {'.pdf'}


def validate_pdf(uploaded_file) -> Tuple[bool, str]:
    """
    Validate a PDF file upload.
    
    Checks:
    1. File is not empty
    2. File size is within limit
    3. File extension is .pdf
    4. File content starts with %PDF magic bytes
    
    Returns:
        (is_valid, error_message)
    """
    if not uploaded_file:
        return False, 'No file provided.'

    if uploaded_file.size == 0:
        return False, 'File is empty.'

    if uploaded_file.size > MAX_UPLOAD_SIZE_BYTES:
        return False, f'File too large. Maximum size is {MAX_UPLOAD_SIZE_MB}MB.'

    # Extension check
    _, ext = os.path.splitext(uploaded_file.name)
    if ext.lower() not in ALLOWED_PDF_EXTENSIONS:
        return False, f'Invalid file type "{ext}". Only PDF files are allowed.'

    # Magic byte check
    try:
        header = uploaded_file.read(8)
        uploaded_file.seek(0)  # Reset for later use

        if not header.startswith(b'%PDF'):
            logger.warning(
                f"PDF magic byte mismatch: file={uploaded_file.name}, "
                f"header={header[:4].hex()}"
            )
            return False, 'File does not appear to be a valid PDF.'
    except Exception:
        logger.exception(f"Error reading file header: {uploaded_file.name}")
        return False, 'Error validating file.'

    return True, 'Valid PDF.'


def validate_image(uploaded_file) -> Tuple[bool, str]:
    """
    Validate an image file upload.
    
    Checks:
    1. File is not empty
    2. File size is within limit
    3. File extension is valid image type
    4. Magic bytes match expected image format
    
    Returns:
        (is_valid, error_message)
    """
    if not uploaded_file:
        return False, 'No file provided.'

    if uploaded_file.size == 0:
        return False, 'File is empty.'

    if uploaded_file.size > MAX_UPLOAD_SIZE_BYTES:
        return False, f'File too large. Maximum size is {MAX_UPLOAD_SIZE_MB}MB.'

    # Extension check
    _, ext = os.path.splitext(uploaded_file.name)
    if ext.lower() not in ALLOWED_IMAGE_EXTENSIONS:
        return False, f'Invalid file type "{ext}". Allowed: {", ".join(ALLOWED_IMAGE_EXTENSIONS)}'

    # Magic byte check
    try:
        header = uploaded_file.read(8)
        uploaded_file.seek(0)

        is_valid_magic = any(header.startswith(magic) for magic in MAGIC_BYTES.keys())
        if not is_valid_magic:
            logger.warning(
                f"Image magic byte mismatch: file={uploaded_file.name}, "
                f"header={header[:4].hex()}"
            )
            return False, 'File does not appear to be a valid image.'
    except Exception:
        logger.exception(f"Error reading file header: {uploaded_file.name}")
        return False, 'Error validating file.'

    return True, 'Valid image.'


def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to prevent path traversal and injection.
    
    Strips directory components, removes non-alphanumeric characters
    (except dots, hyphens, underscores), and limits length.
    """
    # Strip directory components
    filename = os.path.basename(filename)

    # Keep only safe characters
    name, ext = os.path.splitext(filename)
    import re
    name = re.sub(r'[^\w\-]', '_', name)
    ext = re.sub(r'[^\w\.]', '', ext)

    # Limit length
    name = name[:100]

    return f"{name}{ext}"
