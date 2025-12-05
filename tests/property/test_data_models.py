"""Property-based tests for data model serialization round-trip.

**Feature: nest-thermostat-agent, Property 12: Temperature Data Parsing Round-Trip**
**Validates: Requirements 1.3**
"""

from datetime import datetime, timezone
from hypothesis import given, strategies as st, assume

from src.models.data import (
    TemperatureData,
    AdjustmentResult,
    AdjustmentEvent,
    NotificationEvent,
    LogEvent,
    EventType,
    Severity,
)


# Custom strategies for generating valid data
temperature_strategy = st.floats(min_value=-50.0, max_value=150.0, allow_nan=False, allow_infinity=False)
humidity_strategy = st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False)
thermostat_id_strategy = st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('L', 'N', 'P')))
hvac_mode_strategy = st.sampled_from(["heat", "cool", "heat-cool", "off", None])
timestamp_strategy = st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31))


@given(
    ambient=temperature_strategy,
    target=temperature_strategy,
    thermostat_id=thermostat_id_strategy,
    timestamp=timestamp_strategy,
    humidity=st.one_of(st.none(), humidity_strategy),
    hvac_mode=hvac_mode_strategy,
)
def test_temperature_data_round_trip(
    ambient: float,
    target: float,
    thermostat_id: str,
    timestamp: datetime,
    humidity: float | None,
    hvac_mode: str | None,
) -> None:
    """
    **Feature: nest-thermostat-agent, Property 12: Temperature Data Parsing Round-Trip**
    **Validates: Requirements 1.3**
    
    For any valid TemperatureData, serializing to JSON and deserializing back
    should produce an equivalent object with the same temperature values.
    """
    assume(len(thermostat_id.strip()) > 0)  # Ensure non-empty thermostat ID
    
    original = TemperatureData(
        ambient_temperature=ambient,
        target_temperature=target,
        thermostat_id=thermostat_id,
        timestamp=timestamp,
        humidity=humidity,
        hvac_mode=hvac_mode,
    )
    
    # Round-trip through JSON
    json_str = original.to_json()
    restored = TemperatureData.from_json(json_str)
    
    # Verify temperature values are preserved
    assert restored.ambient_temperature == original.ambient_temperature
    assert restored.target_temperature == original.target_temperature
    assert restored.thermostat_id == original.thermostat_id
    assert restored.humidity == original.humidity
    assert restored.hvac_mode == original.hvac_mode
    
    # Timestamps should be equivalent (may lose timezone info in serialization)
    assert restored.timestamp.replace(tzinfo=None) == original.timestamp.replace(tzinfo=None)


@given(
    ambient=temperature_strategy,
    target=temperature_strategy,
    thermostat_id=thermostat_id_strategy,
    timestamp=timestamp_strategy,
    humidity=st.one_of(st.none(), humidity_strategy),
    hvac_mode=hvac_mode_strategy,
)
def test_temperature_data_dict_round_trip(
    ambient: float,
    target: float,
    thermostat_id: str,
    timestamp: datetime,
    humidity: float | None,
    hvac_mode: str | None,
) -> None:
    """
    **Feature: nest-thermostat-agent, Property 12: Temperature Data Parsing Round-Trip**
    **Validates: Requirements 1.3**
    
    For any valid TemperatureData, converting to dict and back should preserve values.
    """
    assume(len(thermostat_id.strip()) > 0)
    
    original = TemperatureData(
        ambient_temperature=ambient,
        target_temperature=target,
        thermostat_id=thermostat_id,
        timestamp=timestamp,
        humidity=humidity,
        hvac_mode=hvac_mode,
    )
    
    # Round-trip through dict
    data_dict = original.to_dict()
    restored = TemperatureData.from_dict(data_dict)
    
    assert restored.ambient_temperature == original.ambient_temperature
    assert restored.target_temperature == original.target_temperature
    assert restored.thermostat_id == original.thermostat_id
    assert restored.humidity == original.humidity
    assert restored.hvac_mode == original.hvac_mode


@given(
    success=st.booleans(),
    previous_target=temperature_strategy,
    new_target=temperature_strategy,
    timestamp=timestamp_strategy,
    error_message=st.one_of(st.none(), st.text(min_size=1, max_size=200)),
)
def test_adjustment_result_round_trip(
    success: bool,
    previous_target: float,
    new_target: float,
    timestamp: datetime,
    error_message: str | None,
) -> None:
    """
    **Feature: nest-thermostat-agent, Property 12: Temperature Data Parsing Round-Trip**
    **Validates: Requirements 1.3**
    
    For any valid AdjustmentResult, serializing and deserializing should preserve values.
    """
    original = AdjustmentResult(
        success=success,
        previous_target=previous_target,
        new_target=new_target,
        timestamp=timestamp,
        error_message=error_message,
    )
    
    json_str = original.to_json()
    restored = AdjustmentResult.from_json(json_str)
    
    assert restored.success == original.success
    assert restored.previous_target == original.previous_target
    assert restored.new_target == original.new_target
    assert restored.error_message == original.error_message


@given(
    previous_setting=temperature_strategy,
    new_setting=temperature_strategy,
    ambient_temperature=temperature_strategy,
    trigger_reason=st.text(min_size=1, max_size=100),
    timestamp=timestamp_strategy,
    thermostat_id=thermostat_id_strategy,
    notification_sent=st.booleans(),
)
def test_adjustment_event_round_trip(
    previous_setting: float,
    new_setting: float,
    ambient_temperature: float,
    trigger_reason: str,
    timestamp: datetime,
    thermostat_id: str,
    notification_sent: bool,
) -> None:
    """
    **Feature: nest-thermostat-agent, Property 12: Temperature Data Parsing Round-Trip**
    **Validates: Requirements 1.3**
    
    For any valid AdjustmentEvent, serializing and deserializing should preserve values.
    """
    assume(len(thermostat_id.strip()) > 0)
    assume(len(trigger_reason.strip()) > 0)
    
    original = AdjustmentEvent(
        previous_setting=previous_setting,
        new_setting=new_setting,
        ambient_temperature=ambient_temperature,
        trigger_reason=trigger_reason,
        timestamp=timestamp,
        thermostat_id=thermostat_id,
        notification_sent=notification_sent,
    )
    
    json_str = original.to_json()
    restored = AdjustmentEvent.from_json(json_str)
    
    assert restored.previous_setting == original.previous_setting
    assert restored.new_setting == original.new_setting
    assert restored.ambient_temperature == original.ambient_temperature
    assert restored.trigger_reason == original.trigger_reason
    assert restored.thermostat_id == original.thermostat_id
    assert restored.notification_sent == original.notification_sent
    assert restored.event_type == original.event_type


@given(
    event_type=st.sampled_from(list(EventType)),
    severity=st.sampled_from(list(Severity)),
    timestamp=timestamp_strategy,
    message=st.one_of(st.none(), st.text(min_size=1, max_size=200)),
)
def test_log_event_round_trip(
    event_type: EventType,
    severity: Severity,
    timestamp: datetime,
    message: str | None,
) -> None:
    """
    **Feature: nest-thermostat-agent, Property 12: Temperature Data Parsing Round-Trip**
    **Validates: Requirements 1.3**
    
    For any valid LogEvent, serializing and deserializing should preserve values.
    """
    original = LogEvent(
        timestamp=timestamp,
        event_type=event_type,
        severity=severity,
        data={"test_key": "test_value", "number": 42},
        message=message,
    )
    
    json_str = original.to_json()
    restored = LogEvent.from_json(json_str)
    
    assert restored.event_type == original.event_type
    assert restored.severity == original.severity
    assert restored.data == original.data
    assert restored.message == original.message
