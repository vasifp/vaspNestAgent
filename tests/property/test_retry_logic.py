"""Property-based tests for retry limit compliance.

**Feature: nest-thermostat-agent, Property 3: Retry Limit Compliance**
**Validates: Requirements 1.4, 2.3, 3.3**
"""

import asyncio
import contextlib
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from src.services.nest_api import NestAPIClient, NestAPIError, NestAuthenticationError


class RetryCounter:
    """Helper class to count retry attempts."""

    def __init__(self, fail_count: int = 0):
        self.attempts = 0
        self.fail_count = fail_count

    def should_fail(self) -> bool:
        """Check if this attempt should fail."""
        self.attempts += 1
        return self.attempts <= self.fail_count


@pytest.fixture
def nest_client():
    """Create a NestAPIClient for testing."""
    return NestAPIClient(
        client_id="test_client_id",
        client_secret="test_client_secret",
        refresh_token="test_refresh_token",
        project_id="test_project_id",
    )


@given(fail_count=st.integers(min_value=0, max_value=10))
@settings(max_examples=20, deadline=None)
def test_authentication_retry_limit_compliance(fail_count: int) -> None:
    """
    **Feature: nest-thermostat-agent, Property 3: Retry Limit Compliance**
    **Validates: Requirements 1.4**

    For any sequence of authentication failures, the retry count SHALL NOT
    exceed MAX_CONNECTION_RETRIES (5).
    """
    client = NestAPIClient(
        client_id="test",
        client_secret="test",
        refresh_token="test",
        project_id="test",
    )

    counter = RetryCounter(fail_count)

    async def mock_refresh():
        if counter.should_fail():
            raise Exception("Simulated auth failure")

    async def run_test():
        with (
            patch.object(client, '_refresh_access_token', side_effect=mock_refresh),
            patch('asyncio.sleep', new_callable=AsyncMock),
            contextlib.suppress(NestAuthenticationError),
        ):
            await client.authenticate()

    asyncio.run(run_test())

    # Verify retry count does not exceed limit
    max_retries = NestAPIClient.MAX_CONNECTION_RETRIES
    assert counter.attempts <= max_retries, (
        f"Retry count {counter.attempts} exceeded max {max_retries}"
    )


@given(fail_count=st.integers(min_value=0, max_value=10))
@settings(max_examples=20, deadline=None)
def test_get_thermostat_retry_limit_compliance(fail_count: int) -> None:
    """
    **Feature: nest-thermostat-agent, Property 3: Retry Limit Compliance**
    **Validates: Requirements 1.4**

    For any sequence of API failures when getting thermostat data,
    the retry count SHALL NOT exceed MAX_CONNECTION_RETRIES (5).
    """
    client = NestAPIClient(
        client_id="test",
        client_secret="test",
        refresh_token="test",
        project_id="test",
    )

    counter = RetryCounter(fail_count)

    async def mock_fetch():
        if counter.should_fail():
            raise NestAPIError("Simulated API failure")
        # Return mock data on success
        from src.models.data import TemperatureData
        return TemperatureData(
            ambient_temperature=72.0,
            target_temperature=75.0,
            thermostat_id="test-id",
            timestamp=datetime.now(),
        )

    async def run_test():
        with (
            patch.object(client, '_fetch_thermostat_data', side_effect=mock_fetch),
            patch('asyncio.sleep', new_callable=AsyncMock),
            contextlib.suppress(NestAPIError),
        ):
            await client.get_thermostat_data()

    asyncio.run(run_test())

    # Verify retry count does not exceed limit
    max_retries = NestAPIClient.MAX_CONNECTION_RETRIES
    assert counter.attempts <= max_retries, (
        f"Retry count {counter.attempts} exceeded max {max_retries}"
    )


@given(fail_count=st.integers(min_value=0, max_value=10))
@settings(max_examples=20, deadline=None)
def test_set_temperature_retry_limit_compliance(fail_count: int) -> None:
    """
    **Feature: nest-thermostat-agent, Property 3: Retry Limit Compliance**
    **Validates: Requirements 2.3**

    For any sequence of API failures when setting temperature,
    the retry count SHALL NOT exceed MAX_ADJUSTMENT_RETRIES (3).
    """
    client = NestAPIClient(
        client_id="test",
        client_secret="test",
        refresh_token="test",
        project_id="test",
    )

    counter = RetryCounter(fail_count)

    async def mock_set_temp(_target: float):
        if counter.should_fail():
            raise NestAPIError("Simulated API failure")

    async def mock_get_data():
        from src.models.data import TemperatureData
        return TemperatureData(
            ambient_temperature=72.0,
            target_temperature=75.0,
            thermostat_id="test-id",
            timestamp=datetime.now(),
        )

    async def run_test():
        with (
            patch.object(client, '_set_temperature_api', side_effect=mock_set_temp),
            patch.object(client, 'get_thermostat_data', side_effect=mock_get_data),
            patch('asyncio.sleep', new_callable=AsyncMock),
        ):
            await client.set_temperature(70.0)

    asyncio.run(run_test())

    # Verify retry count does not exceed limit
    max_retries = NestAPIClient.MAX_ADJUSTMENT_RETRIES
    assert counter.attempts <= max_retries, (
        f"Retry count {counter.attempts} exceeded max {max_retries}"
    )


def test_authentication_succeeds_within_retry_limit() -> None:
    """
    **Feature: nest-thermostat-agent, Property 3: Retry Limit Compliance**
    **Validates: Requirements 1.4**

    If authentication succeeds within the retry limit, no error should be raised.
    """
    client = NestAPIClient(
        client_id="test",
        client_secret="test",
        refresh_token="test",
        project_id="test",
    )

    # Fail 3 times, then succeed (within 5 retry limit)
    counter = RetryCounter(3)

    async def mock_refresh():
        if counter.should_fail():
            raise Exception("Simulated auth failure")

    async def run_test():
        with (
            patch.object(client, '_refresh_access_token', side_effect=mock_refresh),
            patch('asyncio.sleep', new_callable=AsyncMock),
        ):
            await client.authenticate()  # Should not raise

    asyncio.run(run_test())
    assert counter.attempts == 4  # 3 failures + 1 success


def test_authentication_fails_after_max_retries() -> None:
    """
    **Feature: nest-thermostat-agent, Property 3: Retry Limit Compliance**
    **Validates: Requirements 1.4**

    If authentication fails for all retries, NestAuthenticationError should be raised.
    """
    client = NestAPIClient(
        client_id="test",
        client_secret="test",
        refresh_token="test",
        project_id="test",
    )

    # Always fail
    counter = RetryCounter(100)

    async def mock_refresh():
        if counter.should_fail():
            raise Exception("Simulated auth failure")

    async def run_test():
        with (
            patch.object(client, '_refresh_access_token', side_effect=mock_refresh),
            patch('asyncio.sleep', new_callable=AsyncMock),
            pytest.raises(NestAuthenticationError),
        ):
            await client.authenticate()

    asyncio.run(run_test())
    assert counter.attempts == NestAPIClient.MAX_CONNECTION_RETRIES


def test_set_temperature_returns_failure_after_max_retries() -> None:
    """
    **Feature: nest-thermostat-agent, Property 3: Retry Limit Compliance**
    **Validates: Requirements 2.3**

    If set_temperature fails for all retries, it should return a failure result
    (not raise an exception).
    """
    client = NestAPIClient(
        client_id="test",
        client_secret="test",
        refresh_token="test",
        project_id="test",
    )

    # Always fail
    counter = RetryCounter(100)

    async def mock_set_temp(_target: float):
        if counter.should_fail():
            raise NestAPIError("Simulated API failure")

    async def mock_get_data():
        from src.models.data import TemperatureData
        return TemperatureData(
            ambient_temperature=72.0,
            target_temperature=75.0,
            thermostat_id="test-id",
            timestamp=datetime.now(),
        )

    async def run_test():
        with (
            patch.object(client, '_set_temperature_api', side_effect=mock_set_temp),
            patch.object(client, 'get_thermostat_data', side_effect=mock_get_data),
            patch('asyncio.sleep', new_callable=AsyncMock),
        ):
            result = await client.set_temperature(70.0)
            return result

    result = asyncio.run(run_test())

    assert result.success is False
    assert result.error_message is not None
    assert counter.attempts == NestAPIClient.MAX_ADJUSTMENT_RETRIES


def test_backoff_calculation() -> None:
    """Test that backoff delay increases exponentially."""
    client = NestAPIClient(
        client_id="test",
        client_secret="test",
        refresh_token="test",
        project_id="test",
    )

    delays = [client._calculate_backoff(i) for i in range(5)]

    # Each delay should be roughly double the previous (with some jitter)
    for i in range(1, len(delays)):
        # Allow for jitter variance
        assert delays[i] >= delays[i-1] * 0.9, (
            f"Delay {i} ({delays[i]}) should be >= delay {i-1} ({delays[i-1]})"
        )

    # Verify max delay is respected
    max_delay = client._calculate_backoff(100)
    assert max_delay <= NestAPIClient.MAX_RETRY_DELAY * 1.1  # Allow 10% jitter
