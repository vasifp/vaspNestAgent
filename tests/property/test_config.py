"""Property-based tests for configuration validation.

**Feature: nest-thermostat-agent, Property 6: Configuration Validation**
**Validates: Requirements 5.3, 5.4**
"""

import pytest
from hypothesis import given, strategies as st, assume

from src.config import Config, ConfigurationError


# Valid value strategies
valid_polling_interval = st.integers(min_value=10, max_value=3600)
valid_cooldown_period = st.integers(min_value=60, max_value=86400)
valid_temperature_threshold = st.floats(min_value=1.0, max_value=20.0, allow_nan=False)
valid_temperature_adjustment = st.floats(min_value=1.0, max_value=20.0, allow_nan=False)
valid_http_port = st.integers(min_value=1, max_value=65535)
valid_error_threshold = st.integers(min_value=1, max_value=1000)
valid_aws_region = st.sampled_from([
    "us-east-1", "us-west-2", "eu-west-1", "ap-southeast-1", "sa-east-1"
])
valid_phone_number = st.sampled_from([
    "480-442-0574",
    "(480) 442-0574",
    "4804420574",
    "+14804420574",
    "123-456-7890",
])

# Invalid value strategies
invalid_polling_interval_low = st.integers(min_value=-1000, max_value=9)
invalid_polling_interval_high = st.integers(min_value=3601, max_value=100000)
invalid_cooldown_period_low = st.integers(min_value=-1000, max_value=59)
invalid_cooldown_period_high = st.integers(min_value=86401, max_value=1000000)
invalid_temperature_threshold_low = st.floats(min_value=-100.0, max_value=0.9, allow_nan=False)
invalid_temperature_threshold_high = st.floats(min_value=20.1, max_value=100.0, allow_nan=False)
invalid_http_port_low = st.integers(min_value=-1000, max_value=0)
invalid_http_port_high = st.integers(min_value=65536, max_value=100000)
invalid_aws_region = st.sampled_from([
    "invalid", "us_east_1", "US-EAST-1", "useast1", "123-456-7"
])


@given(
    polling_interval=valid_polling_interval,
    cooldown_period=valid_cooldown_period,
    temperature_threshold=valid_temperature_threshold,
    temperature_adjustment=valid_temperature_adjustment,
    http_port=valid_http_port,
    error_threshold=valid_error_threshold,
    aws_region=valid_aws_region,
)
def test_valid_config_passes_validation(
    polling_interval: int,
    cooldown_period: int,
    temperature_threshold: float,
    temperature_adjustment: float,
    http_port: int,
    error_threshold: int,
    aws_region: str,
) -> None:
    """
    **Feature: nest-thermostat-agent, Property 6: Configuration Validation**
    **Validates: Requirements 5.3, 5.4**
    
    For any configuration with values within valid ranges, validation should pass.
    """
    config = Config(
        polling_interval=polling_interval,
        cooldown_period=cooldown_period,
        temperature_threshold=temperature_threshold,
        temperature_adjustment=temperature_adjustment,
        http_port=http_port,
        error_threshold=error_threshold,
        aws_region=aws_region,
        cloudwatch_log_group="/vaspNestAgent/logs",
    )
    
    # Should not raise
    config.validate()


@given(polling_interval=invalid_polling_interval_low)
def test_invalid_polling_interval_low_fails_validation(polling_interval: int) -> None:
    """
    **Feature: nest-thermostat-agent, Property 6: Configuration Validation**
    **Validates: Requirements 5.3, 5.4**
    
    For any polling_interval below minimum, validation should fail.
    """
    config = Config(polling_interval=polling_interval)
    
    with pytest.raises(ConfigurationError) as exc_info:
        config.validate()
    
    assert "polling_interval" in str(exc_info.value)


@given(polling_interval=invalid_polling_interval_high)
def test_invalid_polling_interval_high_fails_validation(polling_interval: int) -> None:
    """
    **Feature: nest-thermostat-agent, Property 6: Configuration Validation**
    **Validates: Requirements 5.3, 5.4**
    
    For any polling_interval above maximum, validation should fail.
    """
    config = Config(polling_interval=polling_interval)
    
    with pytest.raises(ConfigurationError) as exc_info:
        config.validate()
    
    assert "polling_interval" in str(exc_info.value)


@given(cooldown_period=invalid_cooldown_period_low)
def test_invalid_cooldown_period_low_fails_validation(cooldown_period: int) -> None:
    """
    **Feature: nest-thermostat-agent, Property 6: Configuration Validation**
    **Validates: Requirements 5.3, 5.4**
    
    For any cooldown_period below minimum, validation should fail.
    """
    config = Config(cooldown_period=cooldown_period)
    
    with pytest.raises(ConfigurationError) as exc_info:
        config.validate()
    
    assert "cooldown_period" in str(exc_info.value)


@given(cooldown_period=invalid_cooldown_period_high)
def test_invalid_cooldown_period_high_fails_validation(cooldown_period: int) -> None:
    """
    **Feature: nest-thermostat-agent, Property 6: Configuration Validation**
    **Validates: Requirements 5.3, 5.4**
    
    For any cooldown_period above maximum, validation should fail.
    """
    config = Config(cooldown_period=cooldown_period)
    
    with pytest.raises(ConfigurationError) as exc_info:
        config.validate()
    
    assert "cooldown_period" in str(exc_info.value)


@given(temperature_threshold=invalid_temperature_threshold_low)
def test_invalid_temperature_threshold_low_fails_validation(temperature_threshold: float) -> None:
    """
    **Feature: nest-thermostat-agent, Property 6: Configuration Validation**
    **Validates: Requirements 5.3, 5.4**
    
    For any temperature_threshold below minimum, validation should fail.
    """
    config = Config(temperature_threshold=temperature_threshold)
    
    with pytest.raises(ConfigurationError) as exc_info:
        config.validate()
    
    assert "temperature_threshold" in str(exc_info.value)


@given(temperature_threshold=invalid_temperature_threshold_high)
def test_invalid_temperature_threshold_high_fails_validation(temperature_threshold: float) -> None:
    """
    **Feature: nest-thermostat-agent, Property 6: Configuration Validation**
    **Validates: Requirements 5.3, 5.4**
    
    For any temperature_threshold above maximum, validation should fail.
    """
    config = Config(temperature_threshold=temperature_threshold)
    
    with pytest.raises(ConfigurationError) as exc_info:
        config.validate()
    
    assert "temperature_threshold" in str(exc_info.value)


@given(http_port=invalid_http_port_low)
def test_invalid_http_port_low_fails_validation(http_port: int) -> None:
    """
    **Feature: nest-thermostat-agent, Property 6: Configuration Validation**
    **Validates: Requirements 5.3, 5.4**
    
    For any http_port below minimum, validation should fail.
    """
    config = Config(http_port=http_port)
    
    with pytest.raises(ConfigurationError) as exc_info:
        config.validate()
    
    assert "http_port" in str(exc_info.value)


@given(http_port=invalid_http_port_high)
def test_invalid_http_port_high_fails_validation(http_port: int) -> None:
    """
    **Feature: nest-thermostat-agent, Property 6: Configuration Validation**
    **Validates: Requirements 5.3, 5.4**
    
    For any http_port above maximum, validation should fail.
    """
    config = Config(http_port=http_port)
    
    with pytest.raises(ConfigurationError) as exc_info:
        config.validate()
    
    assert "http_port" in str(exc_info.value)


@given(aws_region=invalid_aws_region)
def test_invalid_aws_region_fails_validation(aws_region: str) -> None:
    """
    **Feature: nest-thermostat-agent, Property 6: Configuration Validation**
    **Validates: Requirements 5.3, 5.4**
    
    For any AWS region with invalid format, validation should fail.
    """
    config = Config(aws_region=aws_region)
    
    with pytest.raises(ConfigurationError) as exc_info:
        config.validate()
    
    assert "region" in str(exc_info.value).lower()


@given(phone_number=valid_phone_number)
def test_valid_phone_number_passes_validation(phone_number: str) -> None:
    """
    **Feature: nest-thermostat-agent, Property 6: Configuration Validation**
    **Validates: Requirements 5.3, 5.4**
    
    For any phone number in valid format, validation should pass.
    """
    config = Config(google_voice_phone_number=phone_number)
    
    # Should not raise
    config.validate()


def test_invalid_phone_number_fails_validation() -> None:
    """
    **Feature: nest-thermostat-agent, Property 6: Configuration Validation**
    **Validates: Requirements 5.3, 5.4**
    
    For phone numbers with invalid format, validation should fail.
    """
    invalid_phones = ["abc", "12345", "phone-number", "!@#$%^&*"]
    
    for phone in invalid_phones:
        config = Config(google_voice_phone_number=phone)
        
        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()
        
        assert "phone" in str(exc_info.value).lower()


def test_cloudwatch_log_group_must_start_with_slash() -> None:
    """
    **Feature: nest-thermostat-agent, Property 6: Configuration Validation**
    **Validates: Requirements 5.3, 5.4**
    
    CloudWatch log group must start with '/'.
    """
    config = Config(cloudwatch_log_group="vaspNestAgent/logs")  # Missing leading /
    
    with pytest.raises(ConfigurationError) as exc_info:
        config.validate()
    
    assert "cloudwatch_log_group" in str(exc_info.value)


def test_empty_phone_number_passes_validation() -> None:
    """
    **Feature: nest-thermostat-agent, Property 6: Configuration Validation**
    **Validates: Requirements 5.3, 5.4**
    
    Empty phone number should pass validation (optional field).
    """
    config = Config(google_voice_phone_number="")
    
    # Should not raise
    config.validate()


def test_phone_masking() -> None:
    """Test that phone numbers are properly masked for logging."""
    config = Config(google_voice_phone_number="480-442-0574")
    
    masked = config.get_masked_phone()
    
    assert masked == "***-***-0574"
    assert "480" not in masked
    assert "442" not in masked
