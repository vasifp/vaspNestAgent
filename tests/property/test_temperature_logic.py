"""Property tests for temperature adjustment logic.

Tests Property 1 (Temperature Adjustment Logic) and Property 2 (Cooldown Period Enforcement).
"""

from datetime import datetime, timedelta

import pytest
from hypothesis import given, strategies as st, assume, settings

from src.agents.orchestration import (
    AdjustmentState,
    should_adjust_temperature,
    calculate_new_target,
    is_in_cooldown,
    get_cooldown_remaining,
    should_adjust_with_cooldown,
    record_adjustment,
)


# =============================================================================
# Property 1: Temperature Adjustment Logic
# =============================================================================

class TestTemperatureAdjustmentLogic:
    """
    Property 1: Temperature Adjustment Logic
    
    For any ambient temperature and target temperature pair where 
    (target - ambient) < 5°F, the system SHALL compute a new target 
    of (target - 5)°F. For any pair where (target - ambient) >= 5°F, 
    no adjustment SHALL be made.
    
    Validates: Requirements 2.1
    """

    @given(
        ambient=st.floats(min_value=-50, max_value=120, allow_nan=False, allow_infinity=False),
        target=st.floats(min_value=50, max_value=90, allow_nan=False, allow_infinity=False),
    )
    def test_adjustment_needed_when_differential_below_threshold(
        self, ambient: float, target: float
    ):
        """When (target - ambient) < 5, adjustment should be needed."""
        threshold = 5.0
        differential = target - ambient
        
        result = should_adjust_temperature(ambient, target, threshold)
        
        if differential < threshold:
            assert result is True, (
                f"Expected adjustment needed when differential ({differential:.2f}) "
                f"< threshold ({threshold})"
            )
        else:
            assert result is False, (
                f"Expected no adjustment when differential ({differential:.2f}) "
                f">= threshold ({threshold})"
            )

    @given(
        ambient=st.floats(min_value=-50, max_value=120, allow_nan=False, allow_infinity=False),
        target=st.floats(min_value=50, max_value=90, allow_nan=False, allow_infinity=False),
    )
    def test_new_target_calculation(self, ambient: float, target: float):
        """New target should be (target - 5) when adjustment needed, unchanged otherwise."""
        threshold = 5.0
        adjustment = 5.0
        differential = target - ambient
        
        new_target = calculate_new_target(ambient, target, threshold, adjustment)
        
        if differential < threshold:
            expected = target - adjustment
            assert abs(new_target - expected) < 0.001, (
                f"Expected new target {expected:.2f}, got {new_target:.2f}"
            )
        else:
            assert abs(new_target - target) < 0.001, (
                f"Expected target unchanged ({target:.2f}), got {new_target:.2f}"
            )

    @given(
        threshold=st.floats(min_value=1.0, max_value=20.0, allow_nan=False, allow_infinity=False),
        adjustment=st.floats(min_value=1.0, max_value=20.0, allow_nan=False, allow_infinity=False),
    )
    def test_configurable_threshold_and_adjustment(
        self, threshold: float, adjustment: float
    ):
        """Threshold and adjustment values should be configurable."""
        # Test case where adjustment is definitely needed
        target = 75.0
        ambient = target - (threshold / 2)  # Differential is half the threshold
        
        result = should_adjust_temperature(ambient, target, threshold)
        new_target = calculate_new_target(ambient, target, threshold, adjustment)
        
        assert result is True
        assert abs(new_target - (target - adjustment)) < 0.001

    @given(
        target=st.floats(min_value=50, max_value=90, allow_nan=False, allow_infinity=False),
    )
    def test_boundary_condition_exactly_at_threshold(self, target: float):
        """When differential equals threshold exactly, no adjustment should be made."""
        threshold = 5.0
        ambient = target - threshold  # Differential exactly equals threshold
        
        result = should_adjust_temperature(ambient, target, threshold)
        
        assert result is False, (
            f"Expected no adjustment when differential equals threshold exactly"
        )

    @given(
        target=st.floats(min_value=50, max_value=90, allow_nan=False, allow_infinity=False),
        epsilon=st.floats(min_value=0.001, max_value=0.1, allow_nan=False, allow_infinity=False),
    )
    def test_boundary_condition_just_below_threshold(self, target: float, epsilon: float):
        """When differential is just below threshold, adjustment should be made."""
        threshold = 5.0
        ambient = target - threshold + epsilon  # Differential just below threshold
        
        result = should_adjust_temperature(ambient, target, threshold)
        
        assert result is True, (
            f"Expected adjustment when differential ({threshold - epsilon:.4f}) "
            f"is just below threshold ({threshold})"
        )


# =============================================================================
# Property 2: Cooldown Period Enforcement
# =============================================================================

class TestCooldownPeriodEnforcement:
    """
    Property 2: Cooldown Period Enforcement
    
    For any sequence of temperature readings within the cooldown period 
    after an adjustment, the system SHALL NOT make additional adjustments 
    regardless of temperature differential.
    
    Validates: Requirements 2.5
    """

    @given(
        seconds_since_adjustment=st.integers(min_value=0, max_value=1799),
    )
    def test_no_adjustment_during_cooldown(self, seconds_since_adjustment: int):
        """No adjustment should be allowed during cooldown period."""
        cooldown_period = 1800  # 30 minutes
        
        adjustment_time = datetime(2024, 1, 1, 12, 0, 0)
        current_time = adjustment_time + timedelta(seconds=seconds_since_adjustment)
        
        state = AdjustmentState(
            last_adjustment_time=adjustment_time,
            last_adjustment_ambient=72.0,
            last_adjustment_target=70.0,
            adjustment_count=1,
        )
        
        result = is_in_cooldown(state, current_time, cooldown_period)
        
        assert result is True, (
            f"Expected to be in cooldown {seconds_since_adjustment}s after adjustment "
            f"(cooldown period is {cooldown_period}s)"
        )

    @given(
        seconds_after_cooldown=st.integers(min_value=0, max_value=3600),
    )
    def test_adjustment_allowed_after_cooldown(self, seconds_after_cooldown: int):
        """Adjustment should be allowed after cooldown period expires."""
        cooldown_period = 1800  # 30 minutes
        
        adjustment_time = datetime(2024, 1, 1, 12, 0, 0)
        current_time = adjustment_time + timedelta(seconds=cooldown_period + seconds_after_cooldown)
        
        state = AdjustmentState(
            last_adjustment_time=adjustment_time,
            last_adjustment_ambient=72.0,
            last_adjustment_target=70.0,
            adjustment_count=1,
        )
        
        result = is_in_cooldown(state, current_time, cooldown_period)
        
        assert result is False, (
            f"Expected cooldown to be over {cooldown_period + seconds_after_cooldown}s "
            f"after adjustment (cooldown period is {cooldown_period}s)"
        )

    def test_no_cooldown_without_prior_adjustment(self):
        """No cooldown should apply if no adjustment has been made."""
        state = AdjustmentState()  # No prior adjustment
        current_time = datetime.now()
        
        result = is_in_cooldown(state, current_time, cooldown_period=1800)
        
        assert result is False

    @given(
        cooldown_period=st.integers(min_value=60, max_value=86400),
    )
    def test_configurable_cooldown_period(self, cooldown_period: int):
        """Cooldown period should be configurable."""
        adjustment_time = datetime(2024, 1, 1, 12, 0, 0)
        
        state = AdjustmentState(
            last_adjustment_time=adjustment_time,
            adjustment_count=1,
        )
        
        # Just before cooldown ends
        time_before = adjustment_time + timedelta(seconds=cooldown_period - 1)
        assert is_in_cooldown(state, time_before, cooldown_period) is True
        
        # Exactly at cooldown end
        time_at = adjustment_time + timedelta(seconds=cooldown_period)
        assert is_in_cooldown(state, time_at, cooldown_period) is False
        
        # After cooldown ends
        time_after = adjustment_time + timedelta(seconds=cooldown_period + 1)
        assert is_in_cooldown(state, time_after, cooldown_period) is False

    @given(
        seconds_since_adjustment=st.integers(min_value=0, max_value=3600),
    )
    def test_cooldown_remaining_calculation(self, seconds_since_adjustment: int):
        """Cooldown remaining should be calculated correctly."""
        cooldown_period = 1800
        
        adjustment_time = datetime(2024, 1, 1, 12, 0, 0)
        current_time = adjustment_time + timedelta(seconds=seconds_since_adjustment)
        
        state = AdjustmentState(
            last_adjustment_time=adjustment_time,
            adjustment_count=1,
        )
        
        remaining = get_cooldown_remaining(state, current_time, cooldown_period)
        
        if seconds_since_adjustment < cooldown_period:
            expected = cooldown_period - seconds_since_adjustment
            assert remaining == expected, (
                f"Expected {expected}s remaining, got {remaining}s"
            )
        else:
            assert remaining == 0, (
                f"Expected 0s remaining after cooldown, got {remaining}s"
            )


# =============================================================================
# Combined Property Tests
# =============================================================================

class TestCombinedAdjustmentLogic:
    """Tests combining temperature logic and cooldown enforcement."""

    @given(
        ambient=st.floats(min_value=60, max_value=80, allow_nan=False, allow_infinity=False),
        target=st.floats(min_value=70, max_value=85, allow_nan=False, allow_infinity=False),
        seconds_since_adjustment=st.integers(min_value=0, max_value=3600),
    )
    def test_combined_adjustment_decision(
        self, ambient: float, target: float, seconds_since_adjustment: int
    ):
        """Combined logic should respect both temperature and cooldown rules."""
        threshold = 5.0
        cooldown_period = 1800
        
        adjustment_time = datetime(2024, 1, 1, 12, 0, 0)
        current_time = adjustment_time + timedelta(seconds=seconds_since_adjustment)
        
        state = AdjustmentState(
            last_adjustment_time=adjustment_time,
            adjustment_count=1,
        )
        
        result = should_adjust_with_cooldown(
            ambient=ambient,
            target=target,
            state=state,
            current_time=current_time,
            threshold=threshold,
            cooldown_period=cooldown_period,
        )
        
        in_cooldown = seconds_since_adjustment < cooldown_period
        needs_adjustment = (target - ambient) < threshold
        
        if in_cooldown:
            # During cooldown, never adjust regardless of temperature
            assert result is False, (
                f"Expected no adjustment during cooldown "
                f"(even though temperature logic says {needs_adjustment})"
            )
        else:
            # After cooldown, follow temperature logic
            assert result == needs_adjustment, (
                f"Expected adjustment={needs_adjustment} after cooldown, got {result}"
            )

    @given(
        num_readings=st.integers(min_value=1, max_value=10),
    )
    def test_multiple_readings_during_cooldown(self, num_readings: int):
        """Multiple readings during cooldown should all be rejected."""
        threshold = 5.0
        cooldown_period = 1800
        
        adjustment_time = datetime(2024, 1, 1, 12, 0, 0)
        
        state = AdjustmentState(
            last_adjustment_time=adjustment_time,
            adjustment_count=1,
        )
        
        # Generate readings that would normally trigger adjustment
        for i in range(num_readings):
            # Each reading is 60 seconds apart, all within cooldown
            current_time = adjustment_time + timedelta(seconds=60 * (i + 1))
            
            # Temperature that would trigger adjustment
            ambient = 73.0
            target = 75.0  # Differential = 2, which is < 5
            
            result = should_adjust_with_cooldown(
                ambient=ambient,
                target=target,
                state=state,
                current_time=current_time,
                threshold=threshold,
                cooldown_period=cooldown_period,
            )
            
            assert result is False, (
                f"Reading {i+1} at {60 * (i + 1)}s should be rejected during cooldown"
            )


# =============================================================================
# State Management Tests
# =============================================================================

class TestAdjustmentStateManagement:
    """Tests for adjustment state tracking."""

    @given(
        ambient=st.floats(min_value=60, max_value=80, allow_nan=False, allow_infinity=False),
        target=st.floats(min_value=65, max_value=85, allow_nan=False, allow_infinity=False),
    )
    def test_record_adjustment_updates_state(self, ambient: float, target: float):
        """Recording an adjustment should update all state fields."""
        initial_state = AdjustmentState()
        timestamp = datetime(2024, 1, 1, 12, 0, 0)
        
        new_state = record_adjustment(initial_state, ambient, target, timestamp)
        
        assert new_state.last_adjustment_time == timestamp
        assert new_state.last_adjustment_ambient == ambient
        assert new_state.last_adjustment_target == target
        assert new_state.adjustment_count == 1

    @given(
        num_adjustments=st.integers(min_value=1, max_value=20),
    )
    def test_adjustment_count_increments(self, num_adjustments: int):
        """Adjustment count should increment with each adjustment."""
        state = AdjustmentState()
        
        for i in range(num_adjustments):
            timestamp = datetime(2024, 1, 1, 12, 0, 0) + timedelta(hours=i)
            state = record_adjustment(state, 72.0, 70.0, timestamp)
        
        assert state.adjustment_count == num_adjustments

    def test_initial_state_has_no_adjustment(self):
        """Initial state should have no prior adjustment."""
        state = AdjustmentState()
        
        assert state.last_adjustment_time is None
        assert state.last_adjustment_ambient is None
        assert state.last_adjustment_target is None
        assert state.adjustment_count == 0
