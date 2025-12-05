"""Property tests for metrics consistency.

Tests Property 8 (Metrics Consistency).
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock

from hypothesis import given
from hypothesis import strategies as st

from src.agents.orchestration import (
    AdjustmentState,
    ErrorState,
    NotificationState,
    OrchestrationAgent,
    record_adjustment,
    record_error,
    record_notification_sent,
)
from src.config import Config

# =============================================================================
# Property 8: Metrics Consistency
# =============================================================================

class TestMetricsConsistency:
    """
    Property 8: Metrics Consistency

    For any operation (temperature reading, adjustment, notification, API call),
    the corresponding metric counter SHALL be incremented exactly once.

    Validates: Requirements 6.4
    """

    @given(
        num_adjustments=st.integers(min_value=0, max_value=20),
    )
    def test_adjustment_count_matches_adjustments(self, num_adjustments: int):
        """Adjustment count metric should match number of adjustments made."""
        state = AdjustmentState()
        base_time = datetime(2024, 1, 1, 12, 0, 0)

        for i in range(num_adjustments):
            # Each adjustment is 2 hours apart (outside cooldown)
            timestamp = base_time + timedelta(hours=i * 2)
            state = record_adjustment(state, 72.0, 70.0, timestamp)

        assert state.adjustment_count == num_adjustments

    @given(
        num_notifications=st.integers(min_value=0, max_value=20),
    )
    def test_notification_count_matches_notifications(self, num_notifications: int):
        """Notification count metric should match number of notifications sent."""
        state = NotificationState()
        base_time = datetime(2024, 1, 1, 12, 0, 0)

        for i in range(num_notifications):
            # Each notification is 2 hours apart (outside rate limit)
            timestamp = base_time + timedelta(hours=i * 2)
            state = record_notification_sent(state, timestamp)

        assert state.notification_count == num_notifications

    @given(
        num_errors=st.integers(min_value=0, max_value=50),
    )
    def test_error_count_matches_errors(self, num_errors: int):
        """Error count metric should match number of errors recorded."""
        state = ErrorState()
        base_time = datetime(2024, 1, 1, 12, 0, 0)

        for i in range(num_errors):
            timestamp = base_time + timedelta(minutes=i)
            state = record_error(state, f"Error {i}", timestamp)

        assert state.error_count == num_errors

    @given(
        adjustments=st.integers(min_value=0, max_value=10),
        notifications=st.integers(min_value=0, max_value=10),
        errors=st.integers(min_value=0, max_value=10),
    )
    def test_all_metrics_independent(
        self, adjustments: int, notifications: int, errors: int
    ):
        """Each metric should be tracked independently."""
        adj_state = AdjustmentState()
        notif_state = NotificationState()
        error_state = ErrorState()
        base_time = datetime(2024, 1, 1, 12, 0, 0)

        # Record adjustments
        for i in range(adjustments):
            timestamp = base_time + timedelta(hours=i * 2)
            adj_state = record_adjustment(adj_state, 72.0, 70.0, timestamp)

        # Record notifications
        for i in range(notifications):
            timestamp = base_time + timedelta(hours=i * 2)
            notif_state = record_notification_sent(notif_state, timestamp)

        # Record errors
        for i in range(errors):
            timestamp = base_time + timedelta(minutes=i)
            error_state = record_error(error_state, f"Error {i}", timestamp)

        # Verify each metric is independent
        assert adj_state.adjustment_count == adjustments
        assert notif_state.notification_count == notifications
        assert error_state.error_count == errors


class TestHealthStatusMetrics:
    """Tests for health status metrics."""

    def test_health_status_reflects_running_state(self):
        """Health status should reflect running state."""
        config = Config()
        agent = OrchestrationAgent(config)

        # Not running initially
        health = agent.get_health_status()
        assert health["running"] is False

        # Simulate running
        agent.running = True
        agent._start_time = datetime.now()

        health = agent.get_health_status()
        assert health["running"] is True

    @given(
        error_threshold=st.integers(min_value=1, max_value=20),
        consecutive_errors=st.integers(min_value=0, max_value=30),
    )
    def test_health_status_reflects_error_state(
        self, error_threshold: int, consecutive_errors: int
    ):
        """Health status should reflect error state."""
        config = Config()
        config.error_threshold = error_threshold
        agent = OrchestrationAgent(config)
        agent.running = True
        agent._start_time = datetime.now()

        # Set error state
        agent.error_state = ErrorState(
            error_count=consecutive_errors,
            consecutive_errors=consecutive_errors,
        )

        health = agent.get_health_status()

        # Should be degraded if consecutive errors >= threshold
        if consecutive_errors >= error_threshold:
            assert health["status"] == "degraded"
        else:
            assert health["status"] == "healthy"

    def test_uptime_increases_over_time(self):
        """Uptime metric should increase over time."""
        config = Config()
        agent = OrchestrationAgent(config)

        # Not started
        assert agent.get_uptime_seconds() == 0.0

        # Simulate started 60 seconds ago
        agent._start_time = datetime.now() - timedelta(seconds=60)

        uptime = agent.get_uptime_seconds()
        assert uptime >= 60.0
        assert uptime < 62.0  # Allow small margin

    @given(
        adjustment_count=st.integers(min_value=0, max_value=100),
        notification_count=st.integers(min_value=0, max_value=100),
        error_count=st.integers(min_value=0, max_value=100),
    )
    def test_health_status_includes_all_counts(
        self, adjustment_count: int, notification_count: int, error_count: int
    ):
        """Health status should include all metric counts."""
        config = Config()
        agent = OrchestrationAgent(config)
        agent.running = True
        agent._start_time = datetime.now()

        # Set states
        agent.adjustment_state = AdjustmentState(adjustment_count=adjustment_count)
        agent.notification_state = NotificationState(notification_count=notification_count)
        agent.error_state = ErrorState(error_count=error_count)

        health = agent.get_health_status()

        assert health["adjustment_count"] == adjustment_count
        assert health["notification_count"] == notification_count
        assert health["error_count"] == error_count


class TestReadinessStatus:
    """Tests for readiness status."""

    def test_readiness_requires_nest_agent(self):
        """Readiness should require NestAgent to be configured."""
        config = Config()
        agent = OrchestrationAgent(config)

        # No nest agent
        readiness = agent.get_readiness_status()
        assert readiness["ready"] is False
        assert readiness["nest_agent_configured"] is False

        # With nest agent
        agent.nest_agent = MagicMock()
        readiness = agent.get_readiness_status()
        assert readiness["ready"] is True
        assert readiness["nest_agent_configured"] is True

    def test_readiness_status_fields(self):
        """Readiness status should include all required fields."""
        config = Config()
        agent = OrchestrationAgent(config)
        agent.nest_agent = MagicMock()
        agent.logging_agent = MagicMock()

        readiness = agent.get_readiness_status()

        assert "ready" in readiness
        assert "nest_agent_configured" in readiness
        assert "logging_agent_configured" in readiness
        assert "config_loaded" in readiness


class TestTemperatureHistoryMetrics:
    """Tests for temperature history tracking."""

    @given(
        num_readings=st.integers(min_value=1, max_value=50),
    )
    def test_temperature_history_tracked(self, num_readings: int):
        """Temperature history should track all readings."""
        config = Config()
        agent = OrchestrationAgent(config)

        # Simulate temperature readings
        for i in range(num_readings):
            temp_data = MagicMock()
            temp_data.ambient_temperature = 70.0 + i * 0.1
            temp_data.target_temperature = 72.0
            temp_data.thermostat_id = "test-thermostat"
            temp_data.timestamp = datetime.now() - timedelta(minutes=num_readings - i)
            temp_data.humidity = 50.0
            temp_data.hvac_mode = "heat"

            agent._update_temperature_history(temp_data)

        history = agent.get_temperature_history(hours=24)
        assert len(history) == num_readings

    def test_temperature_history_limited(self):
        """Temperature history should be limited to prevent memory issues."""
        config = Config()
        agent = OrchestrationAgent(config)

        # Add more than max entries
        max_entries = 1440
        for i in range(max_entries + 100):
            temp_data = MagicMock()
            temp_data.ambient_temperature = 70.0
            temp_data.target_temperature = 72.0
            temp_data.thermostat_id = "test-thermostat"
            temp_data.timestamp = datetime.now() - timedelta(minutes=max_entries + 100 - i)
            temp_data.humidity = 50.0
            temp_data.hvac_mode = "heat"

            agent._update_temperature_history(temp_data)

        # Should be limited to max_entries
        assert len(agent._temperature_history) == max_entries

    @given(
        num_adjustments=st.integers(min_value=1, max_value=50),
    )
    def test_adjustment_history_tracked(self, num_adjustments: int):
        """Adjustment history should track all adjustments."""
        config = Config()
        agent = OrchestrationAgent(config)

        for _i in range(num_adjustments):
            agent._record_adjustment_event(
                previous_target=75.0,
                new_target=70.0,
                ambient=73.0,
            )

        history = agent.get_adjustment_history(limit=100)
        assert len(history) == num_adjustments

    def test_adjustment_history_limited(self):
        """Adjustment history should be limited."""
        config = Config()
        agent = OrchestrationAgent(config)

        # Add more than max entries
        for _i in range(150):
            agent._record_adjustment_event(
                previous_target=75.0,
                new_target=70.0,
                ambient=73.0,
            )

        # Should be limited to 100
        assert len(agent._adjustment_history) == 100
