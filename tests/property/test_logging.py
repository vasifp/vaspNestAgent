"""Property-based tests for log event completeness.

**Feature: nest-thermostat-agent, Property 7: Log Event Completeness**
**Validates: Requirements 1.5, 2.4, 3.4, 5.5**
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from src.agents.logging import LoggingAgent
from src.config import Config
from src.models.data import (
    AdjustmentEvent,
    EventType,
    LogEvent,
    NotificationEvent,
    Severity,
    TemperatureData,
)

# Strategies for generating test data
temperature_strategy = st.floats(min_value=-50.0, max_value=150.0, allow_nan=False, allow_infinity=False)
humidity_strategy = st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)
thermostat_id_strategy = st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N')))
timestamp_strategy = st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31))
message_strategy = st.text(min_size=1, max_size=200)


def create_mock_config() -> Config:
    """Create a mock configuration for testing."""
    config = Config()
    config.cloudwatch_log_group = "/test/logs"
    config.aws_region = "us-east-1"
    return config


@given(
    ambient=temperature_strategy,
    target=temperature_strategy,
    thermostat_id=thermostat_id_strategy,
    timestamp=timestamp_strategy,
    humidity=st.one_of(st.none(), humidity_strategy),
)
@settings(max_examples=20, deadline=None)
def test_temperature_reading_log_contains_required_fields(
    ambient: float,
    target: float,
    thermostat_id: str,
    timestamp: datetime,
    humidity: float | None,
) -> None:
    """
    **Feature: nest-thermostat-agent, Property 7: Log Event Completeness**
    **Validates: Requirements 1.5**

    For any temperature reading, the log entry SHALL contain timestamp,
    ambient temperature, target temperature, and thermostat identifier.
    """
    assume(len(thermostat_id.strip()) > 0)

    temp_data = TemperatureData(
        ambient_temperature=ambient,
        target_temperature=target,
        thermostat_id=thermostat_id,
        timestamp=timestamp,
        humidity=humidity,
    )

    # Create log event as the LoggingAgent would
    log_event = LogEvent(
        timestamp=datetime.now(),
        event_type=EventType.TEMPERATURE_READING,
        severity=Severity.INFO,
        data={
            "ambient_temperature": temp_data.ambient_temperature,
            "target_temperature": temp_data.target_temperature,
            "thermostat_id": temp_data.thermostat_id,
            "humidity": temp_data.humidity,
        },
        message=f"Temperature: ambient={temp_data.ambient_temperature}°F, target={temp_data.target_temperature}°F",
    )

    # Verify required fields are present
    assert log_event.timestamp is not None
    assert log_event.event_type == EventType.TEMPERATURE_READING
    assert "ambient_temperature" in log_event.data
    assert "target_temperature" in log_event.data
    assert "thermostat_id" in log_event.data

    # Verify values match
    assert log_event.data["ambient_temperature"] == ambient
    assert log_event.data["target_temperature"] == target
    assert log_event.data["thermostat_id"] == thermostat_id


@given(
    previous_setting=temperature_strategy,
    new_setting=temperature_strategy,
    ambient_temperature=temperature_strategy,
    trigger_reason=message_strategy,
    thermostat_id=thermostat_id_strategy,
    timestamp=timestamp_strategy,
)
@settings(max_examples=20, deadline=None)
def test_adjustment_event_log_contains_required_fields(
    previous_setting: float,
    new_setting: float,
    ambient_temperature: float,
    trigger_reason: str,
    thermostat_id: str,
    timestamp: datetime,
) -> None:
    """
    **Feature: nest-thermostat-agent, Property 7: Log Event Completeness**
    **Validates: Requirements 2.4**

    For any temperature adjustment, the log entry SHALL contain timestamp,
    previous setting, new setting, and trigger reason.
    """
    assume(len(thermostat_id.strip()) > 0)
    assume(len(trigger_reason.strip()) > 0)

    adjustment_event = AdjustmentEvent(
        previous_setting=previous_setting,
        new_setting=new_setting,
        ambient_temperature=ambient_temperature,
        trigger_reason=trigger_reason,
        timestamp=timestamp,
        thermostat_id=thermostat_id,
    )

    # Create log event as the LoggingAgent would
    log_event = LogEvent(
        timestamp=datetime.now(),
        event_type=EventType.TEMPERATURE_ADJUSTMENT,
        severity=Severity.INFO,
        data={
            "previous_setting": adjustment_event.previous_setting,
            "new_setting": adjustment_event.new_setting,
            "ambient_temperature": adjustment_event.ambient_temperature,
            "trigger_reason": adjustment_event.trigger_reason,
            "thermostat_id": adjustment_event.thermostat_id,
        },
        message=f"Temperature adjusted: {adjustment_event.previous_setting}°F → {adjustment_event.new_setting}°F",
    )

    # Verify required fields are present
    assert log_event.timestamp is not None
    assert log_event.event_type == EventType.TEMPERATURE_ADJUSTMENT
    assert "previous_setting" in log_event.data
    assert "new_setting" in log_event.data
    assert "trigger_reason" in log_event.data
    assert "thermostat_id" in log_event.data

    # Verify values match
    assert log_event.data["previous_setting"] == previous_setting
    assert log_event.data["new_setting"] == new_setting
    assert log_event.data["trigger_reason"] == trigger_reason


@given(
    success=st.booleans(),
    message_summary=message_strategy,
    timestamp=timestamp_strategy,
)
@settings(max_examples=20, deadline=None)
def test_notification_event_log_contains_required_fields(
    success: bool,
    message_summary: str,
    timestamp: datetime,
) -> None:
    """
    **Feature: nest-thermostat-agent, Property 7: Log Event Completeness**
    **Validates: Requirements 3.4**

    For any notification event, the log entry SHALL contain timestamp
    and success status.
    """
    assume(len(message_summary.strip()) > 0)

    notification_event = NotificationEvent(
        phone_number_masked="***-***-0574",
        message_summary=message_summary,
        success=success,
        timestamp=timestamp,
    )

    # Create log event as the LoggingAgent would
    event_type = EventType.NOTIFICATION_SENT if success else EventType.NOTIFICATION_FAILED
    log_event = LogEvent(
        timestamp=datetime.now(),
        event_type=event_type,
        severity=Severity.INFO if success else Severity.WARNING,
        data={
            "phone_number_masked": notification_event.phone_number_masked,
            "message_summary": notification_event.message_summary,
            "success": notification_event.success,
        },
        message=f"Notification {'sent' if success else 'failed'}: {message_summary}",
    )

    # Verify required fields are present
    assert log_event.timestamp is not None
    assert log_event.event_type in (EventType.NOTIFICATION_SENT, EventType.NOTIFICATION_FAILED)
    assert "success" in log_event.data
    assert "phone_number_masked" in log_event.data

    # Verify values match
    assert log_event.data["success"] == success


@given(
    event_type=st.sampled_from(list(EventType)),
    severity=st.sampled_from(list(Severity)),
    message=st.one_of(st.none(), message_strategy),
)
@settings(max_examples=20, deadline=None)
def test_all_log_events_have_timestamp_and_type(
    event_type: EventType,
    severity: Severity,
    message: str | None,
) -> None:
    """
    **Feature: nest-thermostat-agent, Property 7: Log Event Completeness**
    **Validates: Requirements 1.5, 2.4, 3.4, 5.5**

    For any log event, the entry SHALL contain a timestamp and event type.
    """
    log_event = LogEvent(
        timestamp=datetime.now(),
        event_type=event_type,
        severity=severity,
        data={"test": "data"},
        message=message,
    )

    # Verify timestamp is present and valid
    assert log_event.timestamp is not None
    assert isinstance(log_event.timestamp, datetime)

    # Verify event type is present and valid
    assert log_event.event_type is not None
    assert isinstance(log_event.event_type, EventType)

    # Verify severity is present
    assert log_event.severity is not None
    assert isinstance(log_event.severity, Severity)

    # Verify serialization preserves fields
    json_str = log_event.to_json()
    restored = LogEvent.from_json(json_str)

    assert restored.event_type == log_event.event_type
    assert restored.severity == log_event.severity
    assert restored.data == log_event.data


def test_log_event_json_contains_all_fields() -> None:
    """
    **Feature: nest-thermostat-agent, Property 7: Log Event Completeness**
    **Validates: Requirements 1.5, 2.4, 3.4, 5.5**

    Log event JSON serialization should contain all required fields.
    """
    log_event = LogEvent(
        timestamp=datetime.now(),
        event_type=EventType.TEMPERATURE_READING,
        severity=Severity.INFO,
        data={"ambient_temperature": 72.0, "target_temperature": 75.0},
        message="Test message",
    )

    event_dict = log_event.to_dict()

    # Verify all required fields are in the dict
    assert "timestamp" in event_dict
    assert "event_type" in event_dict
    assert "severity" in event_dict
    assert "data" in event_dict

    # Verify values are correct types
    assert isinstance(event_dict["timestamp"], str)  # ISO format
    assert isinstance(event_dict["event_type"], str)
    assert isinstance(event_dict["severity"], str)
    assert isinstance(event_dict["data"], dict)


@pytest.mark.asyncio
async def test_logging_agent_logs_temperature_with_all_fields() -> None:
    """
    **Feature: nest-thermostat-agent, Property 7: Log Event Completeness**
    **Validates: Requirements 1.5**

    LoggingAgent should log temperature readings with all required fields.
    """
    config = create_mock_config()
    agent = LoggingAgent(config)

    # Mock the CloudWatch client
    agent._client = MagicMock()
    agent._client.put_log_events = AsyncMock(return_value=True)
    agent._client.publish_temperature_reading = AsyncMock(return_value=True)
    agent._initialized = True

    temp_data = TemperatureData(
        ambient_temperature=72.0,
        target_temperature=75.0,
        thermostat_id="test-thermostat",
        timestamp=datetime.now(),
        humidity=45.0,
        hvac_mode="HEAT",
    )

    result = await agent.log_temperature_reading(temp_data)

    assert result["success"] is True

    # Verify event was buffered with correct data
    assert len(agent._event_buffer) == 1
    event = agent._event_buffer[0]

    assert event.event_type == EventType.TEMPERATURE_READING
    assert event.timestamp is not None
    assert event.data["ambient_temperature"] == 72.0
    assert event.data["target_temperature"] == 75.0
    assert event.data["thermostat_id"] == "test-thermostat"


@pytest.mark.asyncio
async def test_logging_agent_logs_adjustment_with_all_fields() -> None:
    """
    **Feature: nest-thermostat-agent, Property 7: Log Event Completeness**
    **Validates: Requirements 2.4**

    LoggingAgent should log adjustments with all required fields.
    """
    config = create_mock_config()
    agent = LoggingAgent(config)

    # Mock the CloudWatch client
    agent._client = MagicMock()
    agent._client.put_log_events = AsyncMock(return_value=True)
    agent._client.publish_adjustment_count = AsyncMock(return_value=True)
    agent._initialized = True

    adjustment = AdjustmentEvent(
        previous_setting=75.0,
        new_setting=70.0,
        ambient_temperature=73.0,
        trigger_reason="Ambient within 5°F of target",
        timestamp=datetime.now(),
        thermostat_id="test-thermostat",
    )

    result = await agent.log_adjustment(adjustment)

    assert result["success"] is True

    # Verify event was buffered with correct data
    assert len(agent._event_buffer) == 1
    event = agent._event_buffer[0]

    assert event.event_type == EventType.TEMPERATURE_ADJUSTMENT
    assert event.timestamp is not None
    assert event.data["previous_setting"] == 75.0
    assert event.data["new_setting"] == 70.0
    assert event.data["trigger_reason"] == "Ambient within 5°F of target"
