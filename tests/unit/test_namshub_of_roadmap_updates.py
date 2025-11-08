"""Tests for namshub_of_roadmap_updates.py"""

import pytest
from bots.namshubs import namshub_of_roadmap_updates


def test_namshub_module_exists():
    """Test that the namshub module can be imported."""
    assert namshub_of_roadmap_updates is not None


def test_namshub_has_invoke_function():
    """Test that the namshub has an invoke function."""
    assert hasattr(namshub_of_roadmap_updates, "invoke")
    assert callable(namshub_of_roadmap_updates.invoke)


def test_namshub_has_metadata():
    """Test that the namshub has __namshub__ metadata."""
    assert hasattr(namshub_of_roadmap_updates, "__namshub__")
    metadata = namshub_of_roadmap_updates.__namshub__
    assert "name" in metadata
    assert "description" in metadata
    assert "parameters" in metadata
    assert metadata["name"] == "roadmap_updates"


def test_namshub_has_system_message_setter():
    """Test that the namshub has a system message setter function."""
    assert hasattr(namshub_of_roadmap_updates, "_set_roadmap_system_message")
    assert callable(namshub_of_roadmap_updates._set_roadmap_system_message)


def test_invoke_signature():
    """Test that invoke has the correct signature."""
    import inspect

    sig = inspect.signature(namshub_of_roadmap_updates.invoke)
    params = list(sig.parameters.keys())
    assert "bot" in params
    assert "pr_number" in params
    assert "kwargs" in params