"""Property tests for error handling logic.

Tests Property 9 (Error Recovery), Property 10 (Duplicate Adjustment Prevention),
and Property 11 (Error Threshold Alerting).
"""

from datetime import datetime, timedelta

import pytest
from hypothesis import given, strategies as st, assume, settings

from src.agents.orchestration import (
    ErrorState,
    AdjustmentState,
    record_error,
    record_success,
    should_send_error_alert,
    mark_alert_sent,
    reset_error_state,
    should_adjust_with_cooldown,
    record_adjustment,
)


# =============================================================================
# Property 9: Error Recovery
# =============================================================================

class TestErrorRecovery:
    """
    Property 9: Error Recovery
    
    For any unhandled exception during the monitoring loop, the agent 
    SHALL log the error and continue operation without terminating.
    
    Validates: Requirements 7.1
    """

    @given(
        num_errors=st.integers(min_value=1, max_value=50),
    )
    def test_error_count_increments(self, num_errors: int):
        """Error count should increment with each error."""
        state = ErrorState()
        
        for i in range(num_errors):
            timestamp = datetime(2024, 1, 1, 12, 0, 0) + timedelta(minutes=i)
            state = record_error(state, f"Error {i}", timestamp)
        
        assert state.error_count == num_errors

    @given(
        num_errors=st.integers(min_value=1, max_value=20),
    )
    def test_consecutive_errors_tracked(self, num_errors: int):
        """Consecutive errors should be tracked."""
        state = ErrorState()
        
        for i in range(num_errors):
            timestamp = datetime(2024, 1, 1, 12, 0, 0) + timedelta(minutes=i)
            state = record_error(state, f"Error {i}", timestamp)
        
        assert state.consecutive_errors == num_errors

    @given(
        errors_before=st.integers(min_value=1, max_value=10),
        errors_after=st.integers(min_value=1, max_value=10),
    )
    def test_success_resets_consecutive_errors(
        self, errors_before: int, errors_after: int
    ):
        """Success should reset consecutive error count but not total."""
        state = ErrorState()
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        
        # Record some errors
        for i in range(errors_before):
            state = record_error(state, f"Error {i}", base_time + timedelta(minutes=i))
        
        assert state.consecutive_errors == errors_before
        
        # Record success
        state = record_success(state)
        
        assert state.consecutive_errors == 0
        assert state.error_count == errors_before  # Total unchanged
        
        # Record more errors
        for i in range(errors_after):
            state = record_error(
                state, f"Error {i}", 
                base_time + timedelta(minutes=errors_before + i + 1)
            )
        
        assert state.consecutive_errors == errors_after
        assert state.error_count == errors_before + errors_after

    @given(
        error_message=st.text(min_size=1, max_size=200).filter(lambda x: x.strip()),
    )
    def test_last_error_recorded(self, error_message: str):
        """Last error message should be recorded."""
        state = ErrorState()
        timestamp = datetime.now()
        
        state = record_error(state, error_message, timestamp)
        
        assert state.last_error == error_message
        assert state.last_error_time == timestamp


# =============================================================================
# Property 10: Duplicate Adjustment Prevention
# =============================================================================

class TestDuplicateAdjustmentPrevention:
    """
    Property 10: Duplicate Adjustment Prevention
    
    For any restart scenario, the system SHALL NOT make duplicate adjustments 
    for the same temperature condition that was already adjusted before restart.
    
    Validates: Requirements 7.3
    """

    @given(
        ambient=st.floats(min_value=60, max_value=80, allow_nan=False, allow_infinity=False),
        target=st.floats(min_value=70, max_value=85, allow_nan=False, allow_infinity=False),
    )
    def test_cooldown_prevents_duplicate_adjustment(
        self, ambient: float, target: float
    ):
        """Cooldown should prevent duplicate adjustments."""
        threshold = 5.0
        cooldown_period = 1800
        
        # Simulate an adjustment was made
        adjustment_time = datetime(2024, 1, 1, 12, 0, 0)
        state = AdjustmentState(
            last_adjustment_time=adjustment_time,
            last_adjustment_ambient=ambient,
            last_adjustment_target=target - 5,  # Adjusted target
            adjustment_count=1,
        )
        
        # Check if adjustment would be made shortly after (simulating restart)
        restart_time = adjustment_time + timedelta(minutes=5)
        
        result = should_adjust_with_cooldown(
            ambient=ambient,
            target=target,
            state=state,
            current_time=restart_time,
            threshold=threshold,
            cooldown_period=cooldown_period,
        )
        
        # Should not adjust during cooldown
        assert result is False

    @given(
        num_restarts=st.integers(min_value=1, max_value=5),
    )
    def test_state_persistence_prevents_duplicates(self, num_restarts: int):
        """Persisted state should prevent duplicate adjustments across restarts."""
        threshold = 5.0
        cooldown_period = 1800
        
        # Initial adjustment
        adjustment_time = datetime(2024, 1, 1, 12, 0, 0)
        state = AdjustmentState(
            last_adjustment_time=adjustment_time,
            adjustment_count=1,
        )
        
        # Simulate multiple "restarts" within cooldown
        adjustments_attempted = 0
        for i in range(num_restarts):
            restart_time = adjustment_time + timedelta(minutes=5 * (i + 1))
            
            # Temperature that would trigger adjustment
            ambient = 73.0
            target = 75.0  # Differential = 2, which is < 5
            
            if should_adjust_with_cooldown(
                ambient=ambient,
                target=target,
                state=state,
                current_time=restart_time,
                threshold=threshold,
                cooldown_period=cooldown_period,
            ):
                adjustments_attempted += 1
        
        # No adjustments should be made during cooldown
        assert adjustments_attempted == 0


# =============================================================================
# Property 11: Error Threshold Alerting
# =============================================================================

class TestErrorThresholdAlerting:
    """
    Property 11: Error Threshold Alerting
    
    For any error count exceeding the configured threshold, exactly one 
    alert notification SHALL be sent to the configured phone number.
    
    Validates: Requirements 7.5
    """

    @given(
        threshold=st.integers(min_value=1, max_value=20),
    )
    def test_alert_triggered_at_threshold(self, threshold: int):
        """Alert should be triggered when error count reaches threshold."""
        state = ErrorState()
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        
        # Record errors up to threshold
        for i in range(threshold):
            state = record_error(state, f"Error {i}", base_time + timedelta(minutes=i))
        
        # Should trigger alert at threshold
        assert should_send_error_alert(state, threshold) is True

    @given(
        threshold=st.integers(min_value=2, max_value=20),
    )
    def test_no_alert_below_threshold(self, threshold: int):
        """Alert should not be triggered below threshold."""
        state = ErrorState()
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        
        # Record errors below threshold
        for i in range(threshold - 1):
            state = record_error(state, f"Error {i}", base_time + timedelta(minutes=i))
        
        # Should not trigger alert
        assert should_send_error_alert(state, threshold) is False

    @given(
        threshold=st.integers(min_value=1, max_value=20),
        extra_errors=st.integers(min_value=1, max_value=10),
    )
    def test_only_one_alert_sent(self, threshold: int, extra_errors: int):
        """Only one alert should be sent even with continued errors."""
        state = ErrorState()
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        
        # Record errors to reach threshold
        for i in range(threshold):
            state = record_error(state, f"Error {i}", base_time + timedelta(minutes=i))
        
        # First check should trigger alert
        assert should_send_error_alert(state, threshold) is True
        
        # Mark alert as sent
        state = mark_alert_sent(state)
        
        # Continue recording errors
        for i in range(extra_errors):
            state = record_error(
                state, f"Extra error {i}", 
                base_time + timedelta(minutes=threshold + i)
            )
        
        # Should not trigger another alert
        assert should_send_error_alert(state, threshold) is False
        assert state.alert_sent is True

    @given(
        threshold=st.integers(min_value=1, max_value=20),
    )
    def test_alert_state_preserved_after_marking(self, threshold: int):
        """Alert sent state should be preserved after marking."""
        state = ErrorState()
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        
        # Record errors to reach threshold
        for i in range(threshold):
            state = record_error(state, f"Error {i}", base_time + timedelta(minutes=i))
        
        # Mark alert as sent
        state = mark_alert_sent(state)
        
        # Verify state is preserved
        assert state.alert_sent is True
        assert state.error_count == threshold
        assert state.last_error == f"Error {threshold - 1}"

    def test_reset_clears_alert_state(self):
        """Reset should clear all error state including alert flag."""
        state = ErrorState(
            error_count=10,
            last_error="Some error",
            last_error_time=datetime.now(),
            alert_sent=True,
            consecutive_errors=5,
        )
        
        state = reset_error_state()
        
        assert state.error_count == 0
        assert state.last_error is None
        assert state.last_error_time is None
        assert state.alert_sent is False
        assert state.consecutive_errors == 0


# =============================================================================
# Combined Error Handling Tests
# =============================================================================

class TestCombinedErrorHandling:
    """Tests combining multiple error handling properties."""

    @given(
        threshold=st.integers(min_value=5, max_value=15),
        errors_before_success=st.integers(min_value=1, max_value=4),
        errors_after_success=st.integers(min_value=1, max_value=10),
    )
    def test_error_recovery_with_threshold_alerting(
        self, threshold: int, errors_before_success: int, errors_after_success: int
    ):
        """Error recovery should work alongside threshold alerting."""
        assume(errors_before_success < threshold)
        
        state = ErrorState()
        base_time = datetime(2024, 1, 1, 12, 0, 0)
        
        # Record some errors (below threshold)
        for i in range(errors_before_success):
            state = record_error(state, f"Error {i}", base_time + timedelta(minutes=i))
        
        # Should not trigger alert yet
        assert should_send_error_alert(state, threshold) is False
        
        # Record success (recovery)
        state = record_success(state)
        assert state.consecutive_errors == 0
        
        # Record more errors
        for i in range(errors_after_success):
            state = record_error(
                state, f"Error after {i}", 
                base_time + timedelta(minutes=errors_before_success + i + 1)
            )
        
        total_errors = errors_before_success + errors_after_success
        assert state.error_count == total_errors
        
        # Alert should trigger if total exceeds threshold
        expected_alert = total_errors >= threshold
        assert should_send_error_alert(state, threshold) == expected_alert
