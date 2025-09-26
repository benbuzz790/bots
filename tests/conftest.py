import uuid


def get_unique_filename(prefix="test", extension="py"):
    """Generate a unique filename for testing."""
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{unique_id}.{extension}"
