import os
import tempfile
import uuid


def get_unique_filename(prefix="test", extension="py"):
    """Generate a unique filename for testing."""
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{unique_id}.{extension}"


def create_safe_test_file(content, prefix="test", extension="py", directory=None):
    """Create a safe test file with given content in specified or temp directory."""
    if directory is None:
        # Create in temp directory
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=f".{extension}", prefix=f"{prefix}_", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            return f.name
    else:
        # Create in specified directory
        if directory == "tmp":
            # Use system temp directory
            directory = tempfile.gettempdir()

        # Ensure directory exists
        os.makedirs(directory, exist_ok=True)

        # Generate unique filename
        filename = get_unique_filename(prefix, extension)
        filepath = os.path.join(directory, filename)

        # Write content to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath
