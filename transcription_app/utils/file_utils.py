"""File handling and validation utilities."""

import os
import re
from typing import Optional

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for use in temporary files."""
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length to avoid path issues
    if len(sanitized) > 100:
        name, ext = os.path.splitext(sanitized)
        sanitized = name[:90] + ext
    return sanitized

def validate_audio_file(uploaded_file, supported_formats: list) -> tuple[bool, Optional[str]]:
    """Validate uploaded audio file."""
    if not uploaded_file:
        return False, "No file uploaded"
    
    # Check file extension
    file_extension = uploaded_file.name.split('.')[-1].lower()
    if file_extension not in supported_formats:
        return False, f"Unsupported file format. Supported formats: {', '.join(supported_formats)}"
    
    # Check file size (optional - could add size limits)
    file_size = uploaded_file.size if hasattr(uploaded_file, 'size') else len(uploaded_file.getvalue())
    if file_size == 0:
        return False, "File is empty"
    
    # Could add more validations here (e.g., max file size, file content validation)
    
    return True, None

def get_file_info(uploaded_file) -> dict:
    """Get information about uploaded file."""
    if not uploaded_file:
        return {}
    
    file_size = uploaded_file.size if hasattr(uploaded_file, 'size') else len(uploaded_file.getvalue())
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    return {
        'name': uploaded_file.name,
        'size': file_size,
        'size_mb': round(file_size / (1024 * 1024), 2),
        'extension': file_extension
    }