"""Shared pytest fixtures and Hypothesis settings."""

import pytest
from hypothesis import settings

# Register Hypothesis profiles
settings.register_profile("ci", max_examples=100, deadline=None)
settings.register_profile("dev", max_examples=10, deadline=None)

# Load CI profile by default
settings.load_profile("ci")


@pytest.fixture
def sample_temperature_data():
    """Sample temperature data for testing."""
    return {
        "ambient_temperature": 72.0,
        "target_temperature": 75.0,
        "thermostat_id": "test-thermostat-001",
    }
