"""Environment variable helpers with redaction support."""

import os
import re
from typing import Any

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def get_env(key: str, default: str | None = None) -> str | None:
    """Get an environment variable."""
    return os.getenv(key, default)


def redact_sensitive(text: str) -> str:
    """Redact API keys and other sensitive information from text."""
    # Redact API keys (common patterns) - escape parentheses properly
    patterns = [
        (r'(?i)api[_-]?key["\']?\s*[:=]\s*["\']?)([a-zA-Z0-9_-]{20,})(["\']?)', r'\1***REDACTED***\3'),
        (r'(?i)password["\']?\s*[:=]\s*["\']?)([^"\'\s]+)(["\']?)', r'\1***REDACTED***\3'),
        (r'(?i)secret["\']?\s*[:=]\s*["\']?)([^"\'\s]+)(["\']?)', r'\1***REDACTED***\3'),
        (r'(?i)token["\']?\s*[:=]\s*["\']?)([^"\'\s]+)(["\']?)', r'\1***REDACTED***\3'),
    ]
    
    result = text
    for pattern, replacement in patterns:
        try:
            result = re.sub(pattern, replacement, result)
        except re.error:
            # If regex fails, just return the text as-is
            pass
    
    return result


class EnvError(RuntimeError):
    """Raised when a required environment variable is missing."""
    pass


def require_env(key: str) -> str:
    """Require an environment variable, raise if missing."""
    value = get_env(key)
    if value is None:
        raise EnvError(f"Required environment variable '{key}' is not set")
    return value







