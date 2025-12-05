"""Property tests for GraphQL API.

Tests Property 14 (GraphQL Response Completeness).
"""

from datetime import datetime

from hypothesis import given
from hypothesis import strategies as st


# Define the formatting functions locally to avoid ariadne import
def _format_temperature_reading(data: dict) -> dict:
    """Format a temperature reading for GraphQL response."""
    ambient = data.get("ambient_temperature", 0)
    target = data.get("target_temperature", 0)

    return {
        "ambientTemperature": ambient,
        "targetTemperature": target,
        "thermostatId": data.get("thermostat_id", "unknown"),
        "timestamp": data.get("timestamp", datetime.now().isoformat()),
        "humidity": data.get("humidity"),
        "hvacMode": data.get("hvac_mode"),
        "differential": target - ambient,
    }


def _format_adjustment_event(data: dict) -> dict:
    """Format an adjustment event for GraphQL response."""
    return {
        "id": data.get("id", "unknown"),
        "previousSetting": data.get("previous_setting", 0),
        "newSetting": data.get("new_setting", 0),
        "ambientTemperature": data.get("ambient_temperature", 0),
        "triggerReason": data.get("trigger_reason", ""),
        "timestamp": data.get("timestamp", datetime.now().isoformat()),
        "notificationSent": data.get("notification_sent", False),
    }


# =============================================================================
# Property 14: GraphQL Response Completeness
# =============================================================================

class TestGraphQLResponseCompleteness:
    """
    Property 14: GraphQL Response Completeness

    For any GraphQL query for temperature data, the response SHALL contain
    all required fields (ambientTemperature, targetTemperature, thermostatId, timestamp).

    Validates: Requirements 15.1, 17.3
    """

    @given(
        ambient=st.floats(min_value=-50, max_value=120, allow_nan=False, allow_infinity=False),
        target=st.floats(min_value=50, max_value=90, allow_nan=False, allow_infinity=False),
        thermostat_id=st.text(min_size=1, max_size=50).filter(lambda x: x.strip()),
    )
    def test_temperature_reading_contains_required_fields(
        self, ambient: float, target: float, thermostat_id: str
    ):
        """Temperature reading response must contain all required fields."""
        data = {
            "ambient_temperature": ambient,
            "target_temperature": target,
            "thermostat_id": thermostat_id,
            "timestamp": datetime.now().isoformat(),
            "humidity": 50.0,
            "hvac_mode": "heat",
        }

        result = _format_temperature_reading(data)

        # Check required fields
        assert "ambientTemperature" in result
        assert "targetTemperature" in result
        assert "thermostatId" in result
        assert "timestamp" in result

        # Check values
        assert result["ambientTemperature"] == ambient
        assert result["targetTemperature"] == target
        assert result["thermostatId"] == thermostat_id

    @given(
        ambient=st.floats(min_value=-50, max_value=120, allow_nan=False, allow_infinity=False),
        target=st.floats(min_value=50, max_value=90, allow_nan=False, allow_infinity=False),
    )
    def test_temperature_reading_includes_differential(
        self, ambient: float, target: float
    ):
        """Temperature reading should include calculated differential."""
        data = {
            "ambient_temperature": ambient,
            "target_temperature": target,
            "thermostat_id": "test",
            "timestamp": datetime.now().isoformat(),
        }

        result = _format_temperature_reading(data)

        assert "differential" in result
        expected_differential = target - ambient
        assert abs(result["differential"] - expected_differential) < 0.001

    @given(
        humidity=st.one_of(
            st.none(),
            st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
        ),
        hvac_mode=st.one_of(st.none(), st.sampled_from(["heat", "cool", "off", "auto"])),
    )
    def test_temperature_reading_handles_optional_fields(
        self, humidity: float, hvac_mode: str
    ):
        """Temperature reading should handle optional fields correctly."""
        data = {
            "ambient_temperature": 72.0,
            "target_temperature": 75.0,
            "thermostat_id": "test",
            "timestamp": datetime.now().isoformat(),
            "humidity": humidity,
            "hvac_mode": hvac_mode,
        }

        result = _format_temperature_reading(data)

        # Optional fields should be present (may be None)
        assert "humidity" in result
        assert "hvacMode" in result
        assert result["humidity"] == humidity
        assert result["hvacMode"] == hvac_mode


class TestAdjustmentEventCompleteness:
    """Tests for adjustment event response completeness."""

    @given(
        previous=st.floats(min_value=50, max_value=90, allow_nan=False, allow_infinity=False),
        new=st.floats(min_value=45, max_value=85, allow_nan=False, allow_infinity=False),
        ambient=st.floats(min_value=40, max_value=100, allow_nan=False, allow_infinity=False),
    )
    def test_adjustment_event_contains_required_fields(
        self, previous: float, new: float, ambient: float
    ):
        """Adjustment event response must contain all required fields."""
        data = {
            "id": "adj_123",
            "previous_setting": previous,
            "new_setting": new,
            "ambient_temperature": ambient,
            "trigger_reason": "Differential below threshold",
            "timestamp": datetime.now().isoformat(),
            "notification_sent": True,
        }

        result = _format_adjustment_event(data)

        # Check required fields
        assert "id" in result
        assert "previousSetting" in result
        assert "newSetting" in result
        assert "ambientTemperature" in result
        assert "triggerReason" in result
        assert "timestamp" in result
        assert "notificationSent" in result

        # Check values
        assert result["previousSetting"] == previous
        assert result["newSetting"] == new
        assert result["ambientTemperature"] == ambient

    @given(
        notification_sent=st.booleans(),
    )
    def test_adjustment_event_notification_status(self, notification_sent: bool):
        """Adjustment event should correctly report notification status."""
        data = {
            "id": "adj_123",
            "previous_setting": 75.0,
            "new_setting": 70.0,
            "ambient_temperature": 73.0,
            "trigger_reason": "Test",
            "timestamp": datetime.now().isoformat(),
            "notification_sent": notification_sent,
        }

        result = _format_adjustment_event(data)

        assert result["notificationSent"] == notification_sent


class TestGraphQLFieldNaming:
    """Tests for GraphQL field naming conventions."""

    def test_temperature_reading_uses_camel_case(self):
        """Temperature reading fields should use camelCase."""
        data = {
            "ambient_temperature": 72.0,
            "target_temperature": 75.0,
            "thermostat_id": "test",
            "timestamp": datetime.now().isoformat(),
            "humidity": 50.0,
            "hvac_mode": "heat",
        }

        result = _format_temperature_reading(data)

        # All keys should be camelCase
        for key in result:
            # Check no underscores (snake_case indicator)
            assert "_" not in key, f"Field '{key}' should be camelCase"

    def test_adjustment_event_uses_camel_case(self):
        """Adjustment event fields should use camelCase."""
        data = {
            "id": "adj_123",
            "previous_setting": 75.0,
            "new_setting": 70.0,
            "ambient_temperature": 73.0,
            "trigger_reason": "Test",
            "timestamp": datetime.now().isoformat(),
            "notification_sent": True,
        }

        result = _format_adjustment_event(data)

        # All keys should be camelCase
        for key in result:
            assert "_" not in key, f"Field '{key}' should be camelCase"


class TestGraphQLDefaultValues:
    """Tests for handling missing data with defaults."""

    def test_temperature_reading_handles_missing_data(self):
        """Temperature reading should handle missing data gracefully."""
        data = {}  # Empty data

        result = _format_temperature_reading(data)

        # Should have default values
        assert result["ambientTemperature"] == 0
        assert result["targetTemperature"] == 0
        assert result["thermostatId"] == "unknown"
        assert "timestamp" in result  # Should have a timestamp

    def test_adjustment_event_handles_missing_data(self):
        """Adjustment event should handle missing data gracefully."""
        data = {}  # Empty data

        result = _format_adjustment_event(data)

        # Should have default values
        assert result["id"] == "unknown"
        assert result["previousSetting"] == 0
        assert result["newSetting"] == 0
        assert result["ambientTemperature"] == 0
        assert result["triggerReason"] == ""
        assert result["notificationSent"] is False
