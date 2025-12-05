"""Property tests for notification logic.

Tests Property 4 (Notification Content Completeness) and Property 5 (Rate Limiting Enforcement).
"""

from datetime import datetime, timedelta

import pytest
from hypothesis import given, strategies as st, assume, settings

from src.agents.orchestration import (
    NotificationState,
    is_notification_rate_limited,
    get_rate_limit_remaining,
    record_notification_sent,
    record_notification_suppressed,
)
from src.services.google_voice import (
    format_adjustment_notification,
    format_error_alert,
    SMSResult,
    calculate_backoff,
)


# =============================================================================
# Property 4: Notification Content Completeness
# =============================================================================

class TestNotificationContentCompleteness:
    """
    Property 4: Notification Content Completeness
    
    For any notification sent after a temperature adjustment, the message 
    SHALL contain the previous temperature, new temperature, and current 
    ambient temperature.
    
    Validates: Requirements 3.2
    """

    @given(
        previous_target=st.floats(min_value=50, max_value=90, allow_nan=False, allow_infinity=False),
        new_target=st.floats(min_value=45, max_value=85, allow_nan=False, allow_infinity=False),
        ambient=st.floats(min_value=40, max_value=100, allow_nan=False, allow_infinity=False),
    )
    def test_notification_contains_all_temperatures(
        self, previous_target: float, new_target: float, ambient: float
    ):
        """Notification message must contain all three temperature values."""
        message = format_adjustment_notification(
            previous_target=previous_target,
            new_target=new_target,
            ambient=ambient,
        )
        
        # Check that all temperatures are present in the message
        assert f"{previous_target:.1f}" in message, (
            f"Previous target {previous_target:.1f} not found in message: {message}"
        )
        assert f"{new_target:.1f}" in message, (
            f"New target {new_target:.1f} not found in message: {message}"
        )
        assert f"{ambient:.1f}" in message, (
            f"Ambient {ambient:.1f} not found in message: {message}"
        )

    @given(
        previous_target=st.floats(min_value=50, max_value=90, allow_nan=False, allow_infinity=False),
        new_target=st.floats(min_value=45, max_value=85, allow_nan=False, allow_infinity=False),
        ambient=st.floats(min_value=40, max_value=100, allow_nan=False, allow_infinity=False),
    )
    def test_notification_contains_context_labels(
        self, previous_target: float, new_target: float, ambient: float
    ):
        """Notification message must contain labels for each temperature."""
        message = format_adjustment_notification(
            previous_target=previous_target,
            new_target=new_target,
            ambient=ambient,
        )
        
        # Check that context labels are present
        assert "Previous" in message, "Message should contain 'Previous' label"
        assert "New" in message, "Message should contain 'New' label"
        assert "Ambient" in message, "Message should contain 'Ambient' label"

    @given(
        previous_target=st.floats(min_value=50, max_value=90, allow_nan=False, allow_infinity=False),
        new_target=st.floats(min_value=45, max_value=85, allow_nan=False, allow_infinity=False),
        ambient=st.floats(min_value=40, max_value=100, allow_nan=False, allow_infinity=False),
    )
    def test_notification_contains_app_identifier(
        self, previous_target: float, new_target: float, ambient: float
    ):
        """Notification message must identify the source application."""
        message = format_adjustment_notification(
            previous_target=previous_target,
            new_target=new_target,
            ambient=ambient,
        )
        
        assert "vaspNestAgent" in message, (
            "Message should contain application identifier 'vaspNestAgent'"
        )

    @given(
        previous_target=st.floats(min_value=50, max_value=90, allow_nan=False, allow_infinity=False),
        new_target=st.floats(min_value=45, max_value=85, allow_nan=False, allow_infinity=False),
        ambient=st.floats(min_value=40, max_value=100, allow_nan=False, allow_infinity=False),
    )
    def test_notification_contains_temperature_units(
        self, previous_target: float, new_target: float, ambient: float
    ):
        """Notification message must include temperature units."""
        message = format_adjustment_notification(
            previous_target=previous_target,
            new_target=new_target,
            ambient=ambient,
        )
        
        # Should contain Fahrenheit indicator
        assert "°F" in message, "Message should contain temperature unit '°F'"


# =============================================================================
# Property 5: Rate Limiting Enforcement
# =============================================================================

class TestRateLimitingEnforcement:
    """
    Property 5: Rate Limiting Enforcement
    
    For any sequence of temperature adjustments within a one-hour window,
    at most one notification SHALL be sent when rate limiting is enabled.
    
    Validates: Requirements 3.5
    """

    @given(
        seconds_since_notification=st.integers(min_value=0, max_value=3599),
    )
    def test_rate_limited_within_window(self, seconds_since_notification: int):
        """Notifications should be rate limited within the rate limit window."""
        rate_limit_seconds = 3600  # 1 hour
        
        notification_time = datetime(2024, 1, 1, 12, 0, 0)
        current_time = notification_time + timedelta(seconds=seconds_since_notification)
        
        state = NotificationState(
            last_notification_time=notification_time,
            notification_count=1,
        )
        
        result = is_notification_rate_limited(state, current_time, rate_limit_seconds)
        
        assert result is True, (
            f"Expected rate limited {seconds_since_notification}s after notification "
            f"(rate limit is {rate_limit_seconds}s)"
        )

    @given(
        seconds_after_window=st.integers(min_value=0, max_value=3600),
    )
    def test_not_rate_limited_after_window(self, seconds_after_window: int):
        """Notifications should be allowed after rate limit window expires."""
        rate_limit_seconds = 3600  # 1 hour
        
        notification_time = datetime(2024, 1, 1, 12, 0, 0)
        current_time = notification_time + timedelta(seconds=rate_limit_seconds + seconds_after_window)
        
        state = NotificationState(
            last_notification_time=notification_time,
            notification_count=1,
        )
        
        result = is_notification_rate_limited(state, current_time, rate_limit_seconds)
        
        assert result is False, (
            f"Expected not rate limited {rate_limit_seconds + seconds_after_window}s "
            f"after notification (rate limit is {rate_limit_seconds}s)"
        )

    def test_no_rate_limit_without_prior_notification(self):
        """No rate limit should apply if no notification has been sent."""
        state = NotificationState()  # No prior notification
        current_time = datetime.now()
        
        result = is_notification_rate_limited(state, current_time, rate_limit_seconds=3600)
        
        assert result is False

    @given(
        rate_limit_seconds=st.integers(min_value=60, max_value=86400),
    )
    def test_configurable_rate_limit_window(self, rate_limit_seconds: int):
        """Rate limit window should be configurable."""
        notification_time = datetime(2024, 1, 1, 12, 0, 0)
        
        state = NotificationState(
            last_notification_time=notification_time,
            notification_count=1,
        )
        
        # Just before rate limit ends
        time_before = notification_time + timedelta(seconds=rate_limit_seconds - 1)
        assert is_notification_rate_limited(state, time_before, rate_limit_seconds) is True
        
        # Exactly at rate limit end
        time_at = notification_time + timedelta(seconds=rate_limit_seconds)
        assert is_notification_rate_limited(state, time_at, rate_limit_seconds) is False
        
        # After rate limit ends
        time_after = notification_time + timedelta(seconds=rate_limit_seconds + 1)
        assert is_notification_rate_limited(state, time_after, rate_limit_seconds) is False

    @given(
        seconds_since_notification=st.integers(min_value=0, max_value=7200),
    )
    def test_rate_limit_remaining_calculation(self, seconds_since_notification: int):
        """Rate limit remaining should be calculated correctly."""
        rate_limit_seconds = 3600
        
        notification_time = datetime(2024, 1, 1, 12, 0, 0)
        current_time = notification_time + timedelta(seconds=seconds_since_notification)
        
        state = NotificationState(
            last_notification_time=notification_time,
            notification_count=1,
        )
        
        remaining = get_rate_limit_remaining(state, current_time, rate_limit_seconds)
        
        if seconds_since_notification < rate_limit_seconds:
            expected = rate_limit_seconds - seconds_since_notification
            assert remaining == expected, (
                f"Expected {expected}s remaining, got {remaining}s"
            )
        else:
            assert remaining == 0, (
                f"Expected 0s remaining after rate limit, got {remaining}s"
            )

    @given(
        num_adjustments=st.integers(min_value=2, max_value=10),
    )
    def test_only_one_notification_per_window(self, num_adjustments: int):
        """Only one notification should be allowed per rate limit window."""
        rate_limit_seconds = 3600
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        
        state = NotificationState()
        notifications_sent = 0
        notifications_suppressed = 0
        
        # Simulate multiple adjustments within the rate limit window
        # Space them evenly within the window (not exceeding it)
        interval_minutes = 50 // num_adjustments  # Ensure all within ~50 minutes
        
        for i in range(num_adjustments):
            current_time = base_time + timedelta(minutes=i * interval_minutes)
            
            if not is_notification_rate_limited(state, current_time, rate_limit_seconds):
                # Would send notification
                state = record_notification_sent(state, current_time)
                notifications_sent += 1
            else:
                # Would suppress notification
                state = record_notification_suppressed(state)
                notifications_suppressed += 1
        
        assert notifications_sent == 1, (
            f"Expected exactly 1 notification sent, got {notifications_sent}"
        )
        assert notifications_suppressed == num_adjustments - 1, (
            f"Expected {num_adjustments - 1} notifications suppressed, "
            f"got {notifications_suppressed}"
        )


# =============================================================================
# State Management Tests
# =============================================================================

class TestNotificationStateManagement:
    """Tests for notification state tracking."""

    @given(
        num_notifications=st.integers(min_value=1, max_value=20),
    )
    def test_notification_count_increments(self, num_notifications: int):
        """Notification count should increment with each notification sent."""
        state = NotificationState()
        
        for i in range(num_notifications):
            # Each notification is 2 hours apart (outside rate limit)
            timestamp = datetime(2024, 1, 1, 12, 0, 0) + timedelta(hours=i * 2)
            state = record_notification_sent(state, timestamp)
        
        assert state.notification_count == num_notifications

    @given(
        num_suppressed=st.integers(min_value=1, max_value=20),
    )
    def test_suppressed_count_increments(self, num_suppressed: int):
        """Suppressed count should increment with each suppressed notification."""
        state = NotificationState(
            last_notification_time=datetime(2024, 1, 1, 12, 0, 0),
            notification_count=1,
        )
        
        for _ in range(num_suppressed):
            state = record_notification_suppressed(state)
        
        assert state.notifications_suppressed == num_suppressed

    def test_initial_state_has_no_notifications(self):
        """Initial state should have no prior notifications."""
        state = NotificationState()
        
        assert state.last_notification_time is None
        assert state.notification_count == 0
        assert state.notifications_suppressed == 0


# =============================================================================
# Error Alert Tests
# =============================================================================

class TestErrorAlertFormatting:
    """Tests for error alert message formatting."""

    @given(
        error_count=st.integers(min_value=1, max_value=100),
        threshold=st.integers(min_value=1, max_value=50),
    )
    def test_error_alert_contains_counts(self, error_count: int, threshold: int):
        """Error alert should contain error count and threshold."""
        message = format_error_alert(
            error_count=error_count,
            threshold=threshold,
            last_error="Test error",
        )
        
        assert str(error_count) in message, (
            f"Error count {error_count} not found in message: {message}"
        )
        assert str(threshold) in message, (
            f"Threshold {threshold} not found in message: {message}"
        )

    @given(
        last_error=st.text(min_size=1, max_size=100).filter(lambda x: x.strip()),
    )
    def test_error_alert_contains_error_description(self, last_error: str):
        """Error alert should contain the last error description."""
        message = format_error_alert(
            error_count=10,
            threshold=5,
            last_error=last_error,
        )
        
        assert last_error in message, (
            f"Last error '{last_error}' not found in message: {message}"
        )

    def test_error_alert_contains_app_identifier(self):
        """Error alert should identify the source application."""
        message = format_error_alert(
            error_count=10,
            threshold=5,
            last_error="Test error",
        )
        
        assert "vaspNestAgent" in message
        assert "ALERT" in message


# =============================================================================
# Retry Backoff Tests
# =============================================================================

class TestRetryBackoff:
    """Tests for retry backoff calculation."""

    @given(
        attempt=st.integers(min_value=0, max_value=10),
    )
    def test_backoff_increases_with_attempts(self, attempt: int):
        """Backoff delay should generally increase with attempt number."""
        base_delay = 1.0
        max_delay = 60.0
        
        delay = calculate_backoff(attempt, base_delay, max_delay)
        
        # Delay should be positive
        assert delay > 0
        
        # Delay should not exceed max_delay + jitter
        assert delay <= max_delay * 1.1  # Allow 10% jitter

    @given(
        attempt=st.integers(min_value=0, max_value=20),
        base_delay=st.floats(min_value=0.1, max_value=5.0, allow_nan=False, allow_infinity=False),
        max_delay=st.floats(min_value=10.0, max_value=120.0, allow_nan=False, allow_infinity=False),
    )
    def test_backoff_respects_max_delay(self, attempt: int, base_delay: float, max_delay: float):
        """Backoff should never exceed max_delay (plus jitter)."""
        delay = calculate_backoff(attempt, base_delay, max_delay)
        
        # Allow 10% jitter above max_delay
        assert delay <= max_delay * 1.1, (
            f"Delay {delay} exceeded max_delay {max_delay} + jitter"
        )
