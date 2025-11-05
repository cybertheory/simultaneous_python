"""Generate unique IDs for runs and other entities."""

import ulid


def generate_run_id() -> str:
    """Generate a unique run ID using ULID."""
    return str(ulid.new())


def generate_id() -> str:
    """Generate a unique ID using ULID."""
    return str(ulid.new())







