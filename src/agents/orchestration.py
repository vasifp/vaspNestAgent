"""Orchestration Agent - Main coordinator for vaspNestAgent.

Implements temperature monitoring logic, adjustment decisions, cooldown tracking,
notification rate limiting, error handling, and graceful shutdown.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

import structlog

from src.config import Config
from src.services.google_voice import (
    GoogleVoiceClient,
    SMSResult,
    format_adjustment_notification,
    format_error_alert,
)

logger = structlog.get_logger(__name__)


@dataclass
class AdjustmentState:
    """Tracks the state of temperature adjustments for cooldown enforcement."""

    last_adjustment_time: datetime | None = None
    last_adjustment_ambient: float | None = None
    last_adjustment_target: float | None = None
    adjustment_count: int = 0


@dataclass
class NotificationState:
    """Tracks the state of notifications for rate limiting.

    Property 5: Rate Limiting Enforcement
    For any sequence of temperature adjustments within a one-hour window,
    at most one notification SHALL be sent when rate limiting is enabled.
    """

    last_notification_time: datetime | None = None
    notification_count: int = 0
    notifications_suppressed: int = 0


@dataclass
class ErrorState:
    """Tracks error counts for threshold alerting.

    Property 11: Error Threshold Alerting
    For any error count exceeding the configured threshold, exactly one
    alert notification SHALL be sent to the configured phone number.
    """

    error_count: int = 0
    last_error: str | None = None
    last_error_time: datetime | None = None
    alert_sent: bool = False
    consecutive_errors: int = 0


def record_error(
    state: ErrorState,
    error_message: str,
    timestamp: datetime,
) -> ErrorState:
    """Record an error occurrence.

    Args:
        state: Current error state.
        error_message: Description of the error.
        timestamp: Time of error.

    Returns:
        Updated error state.
    """
    return ErrorState(
        error_count=state.error_count + 1,
        last_error=error_message,
        last_error_time=timestamp,
        alert_sent=state.alert_sent,
        consecutive_errors=state.consecutive_errors + 1,
    )


def record_success(state: ErrorState) -> ErrorState:
    """Record a successful operation, resetting consecutive error count.

    Args:
        state: Current error state.

    Returns:
        Updated error state with reset consecutive errors.
    """
    return ErrorState(
        error_count=state.error_count,
        last_error=state.last_error,
        last_error_time=state.last_error_time,
        alert_sent=state.alert_sent,
        consecutive_errors=0,
    )


def should_send_error_alert(
    state: ErrorState,
    threshold: int,
) -> bool:
    """Check if an error alert should be sent.

    Property 11: Error Threshold Alerting
    Alert should be sent when error count exceeds threshold AND
    no alert has been sent yet.

    Args:
        state: Current error state.
        threshold: Error threshold for alerting.

    Returns:
        True if alert should be sent.
    """
    return state.error_count >= threshold and not state.alert_sent


def mark_alert_sent(state: ErrorState) -> ErrorState:
    """Mark that an error alert has been sent.

    Args:
        state: Current error state.

    Returns:
        Updated error state with alert_sent=True.
    """
    return ErrorState(
        error_count=state.error_count,
        last_error=state.last_error,
        last_error_time=state.last_error_time,
        alert_sent=True,
        consecutive_errors=state.consecutive_errors,
    )


def reset_error_state() -> ErrorState:
    """Reset error state (e.g., after recovery or manual reset).

    Returns:
        Fresh error state.
    """
    return ErrorState()


def should_adjust_temperature(
    ambient: float,
    target: float,
    threshold: float = 5.0,
) -> bool:
    """Determine if temperature adjustment is needed.

    Property 1: Temperature Adjustment Logic
    For any ambient temperature and target temperature pair where
    (target - ambient) < threshold, the system SHALL return True.
    For any pair where (target - ambient) >= threshold, no adjustment
    SHALL be made (return False).

    Args:
        ambient: Current ambient temperature in Fahrenheit.
        target: Current target temperature setting in Fahrenheit.
        threshold: Temperature differential threshold (default 5.0°F).

    Returns:
        True if adjustment is needed, False otherwise.
    """
    differential = target - ambient
    return differential < threshold


def calculate_new_target(
    ambient: float,
    target: float,
    threshold: float = 5.0,
    adjustment: float = 5.0,
) -> float:
    """Calculate the new target temperature after adjustment.

    If adjustment is needed (differential < threshold), returns target - adjustment.
    Otherwise, returns the current target unchanged.

    Args:
        ambient: Current ambient temperature in Fahrenheit.
        target: Current target temperature setting in Fahrenheit.
        threshold: Temperature differential threshold (default 5.0°F).
        adjustment: Amount to lower target by (default 5.0°F).

    Returns:
        New target temperature (adjusted or unchanged).
    """
    if should_adjust_temperature(ambient, target, threshold):
        return target - adjustment
    return target


def is_in_cooldown(
    state: AdjustmentState,
    current_time: datetime,
    cooldown_period: int = 1800,
) -> bool:
    """Check if the system is currently in cooldown period.

    Property 2: Cooldown Period Enforcement
    For any sequence of temperature readings within the cooldown period
    after an adjustment, the system SHALL NOT make additional adjustments.

    Args:
        state: Current adjustment state tracking last adjustment time.
        current_time: Current timestamp.
        cooldown_period: Cooldown period in seconds (default 1800 = 30 minutes).

    Returns:
        True if in cooldown period, False otherwise.
    """
    if state.last_adjustment_time is None:
        return False

    cooldown_end = state.last_adjustment_time + timedelta(seconds=cooldown_period)
    return current_time < cooldown_end


def get_cooldown_remaining(
    state: AdjustmentState,
    current_time: datetime,
    cooldown_period: int = 1800,
) -> int:
    """Get remaining cooldown time in seconds.

    Args:
        state: Current adjustment state.
        current_time: Current timestamp.
        cooldown_period: Cooldown period in seconds.

    Returns:
        Remaining seconds in cooldown, or 0 if not in cooldown.
    """
    if state.last_adjustment_time is None:
        return 0

    cooldown_end = state.last_adjustment_time + timedelta(seconds=cooldown_period)
    if current_time >= cooldown_end:
        return 0

    remaining = cooldown_end - current_time
    return int(remaining.total_seconds())


def should_adjust_with_cooldown(
    ambient: float,
    target: float,
    state: AdjustmentState,
    current_time: datetime,
    threshold: float = 5.0,
    cooldown_period: int = 1800,
) -> bool:
    """Determine if adjustment is needed, respecting cooldown period.

    Combines Property 1 (temperature logic) and Property 2 (cooldown enforcement).

    Args:
        ambient: Current ambient temperature in Fahrenheit.
        target: Current target temperature setting in Fahrenheit.
        state: Current adjustment state.
        current_time: Current timestamp.
        threshold: Temperature differential threshold.
        cooldown_period: Cooldown period in seconds.

    Returns:
        True if adjustment is needed AND not in cooldown, False otherwise.
    """
    # Check cooldown first
    if is_in_cooldown(state, current_time, cooldown_period):
        return False

    # Then check temperature logic
    return should_adjust_temperature(ambient, target, threshold)


def record_adjustment(
    state: AdjustmentState,
    ambient: float,
    target: float,
    timestamp: datetime,
) -> AdjustmentState:
    """Record an adjustment in the state.

    Args:
        state: Current adjustment state.
        ambient: Ambient temperature at time of adjustment.
        target: New target temperature after adjustment.
        timestamp: Time of adjustment.

    Returns:
        Updated adjustment state.
    """
    return AdjustmentState(
        last_adjustment_time=timestamp,
        last_adjustment_ambient=ambient,
        last_adjustment_target=target,
        adjustment_count=state.adjustment_count + 1,
    )


def is_notification_rate_limited(
    state: NotificationState,
    current_time: datetime,
    rate_limit_seconds: int = 3600,
) -> bool:
    """Check if notifications are currently rate limited.

    Property 5: Rate Limiting Enforcement
    For any sequence of temperature adjustments within a one-hour window,
    at most one notification SHALL be sent when rate limiting is enabled.

    Args:
        state: Current notification state.
        current_time: Current timestamp.
        rate_limit_seconds: Rate limit window in seconds (default 3600 = 1 hour).

    Returns:
        True if rate limited, False if notification can be sent.
    """
    if state.last_notification_time is None:
        return False

    rate_limit_end = state.last_notification_time + timedelta(seconds=rate_limit_seconds)
    return current_time < rate_limit_end


def get_rate_limit_remaining(
    state: NotificationState,
    current_time: datetime,
    rate_limit_seconds: int = 3600,
) -> int:
    """Get remaining rate limit time in seconds.

    Args:
        state: Current notification state.
        current_time: Current timestamp.
        rate_limit_seconds: Rate limit window in seconds.

    Returns:
        Remaining seconds in rate limit, or 0 if not rate limited.
    """
    if state.last_notification_time is None:
        return 0

    rate_limit_end = state.last_notification_time + timedelta(seconds=rate_limit_seconds)
    if current_time >= rate_limit_end:
        return 0

    remaining = rate_limit_end - current_time
    return int(remaining.total_seconds())


def record_notification_sent(
    state: NotificationState,
    timestamp: datetime,
) -> NotificationState:
    """Record that a notification was sent.

    Args:
        state: Current notification state.
        timestamp: Time notification was sent.

    Returns:
        Updated notification state.
    """
    return NotificationState(
        last_notification_time=timestamp,
        notification_count=state.notification_count + 1,
        notifications_suppressed=state.notifications_suppressed,
    )


def record_notification_suppressed(
    state: NotificationState,
) -> NotificationState:
    """Record that a notification was suppressed due to rate limiting.

    Args:
        state: Current notification state.

    Returns:
        Updated notification state with incremented suppressed count.
    """
    return NotificationState(
        last_notification_time=state.last_notification_time,
        notification_count=state.notification_count,
        notifications_suppressed=state.notifications_suppressed + 1,
    )


class OrchestrationAgent:
    """Main agent coordinating NestAgent and LoggingAgent.

    Implements the monitoring loop, temperature adjustment decision logic,
    error handling, and graceful shutdown.

    Property 9: Error Recovery
    For any unhandled exception during the monitoring loop, the agent
    SHALL log the error and continue operation without terminating.

    Property 10: Duplicate Adjustment Prevention
    For any restart scenario, the system SHALL NOT make duplicate adjustments
    for the same temperature condition that was already adjusted before restart.
    """

    def __init__(self, config: Config):
        """Initialize the orchestration agent.

        Args:
            config: Application configuration.
        """
        self.config = config
        self.adjustment_state = AdjustmentState()
        self.notification_state = NotificationState()
        self.error_state = ErrorState()
        self.running = False
        self._start_time: datetime | None = None
        self._current_cycle: asyncio.Task | None = None
        self._shutdown_event = asyncio.Event()

        # Sub-agents - will be set externally or via set_agents()
        self.nest_agent = None
        self.logging_agent = None

        # Google Voice client for notifications
        self._google_voice_client: GoogleVoiceClient | None = None
        if config.google_voice_credentials and config.google_voice_phone_number:
            self._google_voice_client = GoogleVoiceClient(
                credentials=config.google_voice_credentials,
                phone_number=config.google_voice_phone_number,
            )

        # Latest temperature data for GraphQL queries
        self._latest_temperature: dict | None = None
        self._temperature_history: list[dict] = []
        self._adjustment_history: list[dict] = []

    def set_agents(self, nest_agent: Any, logging_agent: Any) -> None:
        """Set the sub-agents for this orchestration agent.

        Args:
            nest_agent: NestAgent instance for thermostat interactions.
            logging_agent: LoggingAgent instance for CloudWatch logging.
        """
        self.nest_agent = nest_agent
        self.logging_agent = logging_agent

    def should_adjust(self, ambient: float, target: float) -> bool:
        """Check if temperature adjustment is needed.

        Uses configured threshold and respects cooldown period.

        Args:
            ambient: Current ambient temperature.
            target: Current target temperature.

        Returns:
            True if adjustment should be made.
        """
        return should_adjust_with_cooldown(
            ambient=ambient,
            target=target,
            state=self.adjustment_state,
            current_time=datetime.now(),
            threshold=self.config.temperature_threshold,
            cooldown_period=self.config.cooldown_period,
        )

    def calculate_adjustment(self, target: float) -> float:
        """Calculate the new target temperature.

        Args:
            target: Current target temperature.

        Returns:
            New target temperature (lowered by configured adjustment amount).
        """
        return target - self.config.temperature_adjustment

    def record_adjustment_made(self, ambient: float, new_target: float) -> None:
        """Record that an adjustment was made.

        Updates internal state for cooldown tracking.

        Args:
            ambient: Ambient temperature at time of adjustment.
            new_target: New target temperature after adjustment.
        """
        self.adjustment_state = record_adjustment(
            state=self.adjustment_state,
            ambient=ambient,
            target=new_target,
            timestamp=datetime.now(),
        )

    def get_cooldown_remaining_seconds(self) -> int:
        """Get remaining cooldown time in seconds.

        Returns:
            Seconds remaining in cooldown, or 0 if not in cooldown.
        """
        return get_cooldown_remaining(
            state=self.adjustment_state,
            current_time=datetime.now(),
            cooldown_period=self.config.cooldown_period,
        )

    def is_in_cooldown(self) -> bool:
        """Check if currently in cooldown period.

        Returns:
            True if in cooldown period.
        """
        return is_in_cooldown(
            state=self.adjustment_state,
            current_time=datetime.now(),
            cooldown_period=self.config.cooldown_period,
        )

    def can_send_notification(self) -> bool:
        """Check if a notification can be sent (not rate limited).

        Returns:
            True if notification can be sent.
        """
        if not self.config.notification_rate_limit_enabled:
            return True

        return not is_notification_rate_limited(
            state=self.notification_state,
            current_time=datetime.now(),
            rate_limit_seconds=self.config.notification_rate_limit_seconds,
        )

    def get_notification_rate_limit_remaining(self) -> int:
        """Get remaining rate limit time in seconds.

        Returns:
            Seconds remaining in rate limit, or 0 if not rate limited.
        """
        return get_rate_limit_remaining(
            state=self.notification_state,
            current_time=datetime.now(),
            rate_limit_seconds=self.config.notification_rate_limit_seconds,
        )

    async def send_adjustment_notification(
        self,
        previous_target: float,
        new_target: float,
        ambient: float,
    ) -> SMSResult | None:
        """Send a notification about a temperature adjustment.

        Respects rate limiting configuration.

        Args:
            previous_target: Previous target temperature.
            new_target: New target temperature.
            ambient: Current ambient temperature.

        Returns:
            SMSResult if notification was sent, None if rate limited or no client.
        """
        if self._google_voice_client is None:
            return None

        # Check rate limiting
        if not self.can_send_notification():
            self.notification_state = record_notification_suppressed(
                self.notification_state
            )
            return None

        # Format and send notification
        message = format_adjustment_notification(
            previous_target=previous_target,
            new_target=new_target,
            ambient=ambient,
        )

        result = await self._google_voice_client.send_sms(message)

        if result.success:
            self.notification_state = record_notification_sent(
                self.notification_state,
                timestamp=datetime.now(),
            )

        return result

    async def send_error_alert(
        self,
        error_count: int,
        threshold: int,
        last_error: str,
    ) -> SMSResult | None:
        """Send an error threshold alert.

        Args:
            error_count: Current error count.
            threshold: Error threshold that was exceeded.
            last_error: Description of the last error.

        Returns:
            SMSResult if alert was sent, None if no client configured.
        """
        if self._google_voice_client is None:
            return None

        message = format_error_alert(
            error_count=error_count,
            threshold=threshold,
            last_error=last_error,
        )

        return await self._google_voice_client.send_sms(message)

    async def start(self) -> None:
        """Start the monitoring loop.

        Runs continuously until stop() is called or a shutdown signal is received.
        """
        self.running = True
        self._start_time = datetime.now()
        self._shutdown_event.clear()

        logger.info(
            "Orchestration agent starting",
            polling_interval=self.config.polling_interval,
            temperature_threshold=self.config.temperature_threshold,
        )

        # Log agent started event
        if self.logging_agent:
            await self._log_agent_event("agent_started")

        try:
            while self.running:
                # Execute monitoring cycle
                self._current_cycle = asyncio.create_task(self.monitor_cycle())
                try:
                    await self._current_cycle
                except asyncio.CancelledError:
                    logger.info("Monitoring cycle cancelled")
                    break

                # Wait for next polling interval or shutdown
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=self.config.polling_interval,
                    )
                    # Shutdown event was set
                    break
                except TimeoutError:
                    # Normal timeout, continue to next cycle
                    pass
        finally:
            self.running = False
            logger.info("Orchestration agent stopped")

    async def stop(self) -> None:
        """Graceful shutdown.

        Signals the monitoring loop to stop and waits for the current cycle
        to complete (with timeout).
        """
        logger.info("Initiating graceful shutdown")
        self.running = False
        self._shutdown_event.set()

        # Wait for current cycle to complete (max 30 seconds)
        if self._current_cycle and not self._current_cycle.done():
            try:
                await asyncio.wait_for(self._current_cycle, timeout=30.0)
            except TimeoutError:
                logger.warning("Current cycle did not complete within timeout, cancelling")
                self._current_cycle.cancel()
            except asyncio.CancelledError:
                pass

        # Flush pending logs
        if self.logging_agent:
            await self._log_agent_event("agent_stopped")
            try:
                await self.logging_agent.flush()
            except Exception as e:
                logger.error("Error flushing logs", error=str(e))

        # Close Google Voice client
        if self._google_voice_client:
            await self._google_voice_client.close()

        logger.info("Graceful shutdown complete")

    async def monitor_cycle(self) -> None:
        """Execute one monitoring cycle.

        Property 9: Error Recovery
        For any unhandled exception during the monitoring loop, the agent
        SHALL log the error and continue operation without terminating.
        """
        try:
            # Get current temperature
            if self.nest_agent is None:
                logger.warning("NestAgent not configured, skipping cycle")
                return

            temperature_data = await self.nest_agent.get_temperature()

            if temperature_data is None:
                self._handle_error("Failed to get temperature data")
                return

            # Record success and reset consecutive errors
            self.error_state = record_success(self.error_state)

            # Store for GraphQL queries
            self._update_temperature_history(temperature_data)

            # Log temperature reading
            if self.logging_agent:
                await self.logging_agent.log_temperature_reading(temperature_data)

            ambient = temperature_data.ambient_temperature
            target = temperature_data.target_temperature

            logger.debug(
                "Temperature reading",
                ambient=ambient,
                target=target,
                differential=target - ambient,
            )

            # Check if adjustment is needed
            if self.should_adjust(ambient, target):
                await self._perform_adjustment(temperature_data)

        except Exception as e:
            # Property 9: Log error and continue
            self._handle_error(str(e))
            logger.exception("Error in monitoring cycle", error=str(e))

    async def _perform_adjustment(self, temperature_data: Any) -> None:
        """Perform a temperature adjustment.

        Args:
            temperature_data: Current temperature data from Nest.
        """
        ambient = temperature_data.ambient_temperature
        previous_target = temperature_data.target_temperature
        new_target = self.calculate_adjustment(previous_target)

        logger.info(
            "Adjusting temperature",
            previous_target=previous_target,
            new_target=new_target,
            ambient=ambient,
        )

        # Set new temperature
        result = await self.nest_agent.set_temperature(new_target)

        if result and result.success:
            # Record adjustment
            self.record_adjustment_made(ambient, new_target)

            # Store for GraphQL queries
            self._record_adjustment_event(
                previous_target=previous_target,
                new_target=new_target,
                ambient=ambient,
            )

            # Log adjustment
            if self.logging_agent:
                await self.logging_agent.log_adjustment(
                    previous_setting=previous_target,
                    new_setting=new_target,
                    ambient_temperature=ambient,
                    trigger_reason=f"Differential ({previous_target - ambient:.1f}°F) below threshold",
                )

            # Send notification
            notification_result = await self.send_adjustment_notification(
                previous_target=previous_target,
                new_target=new_target,
                ambient=ambient,
            )

            if notification_result and self.logging_agent:
                await self.logging_agent.log_notification(
                    success=notification_result.success,
                    message_summary=f"Adjustment: {previous_target}°F -> {new_target}°F",
                )
        else:
            error_msg = result.error_message if result else "Unknown error"
            self._handle_error(f"Failed to set temperature: {error_msg}")

    def _handle_error(self, error_message: str) -> None:
        """Handle an error occurrence.

        Property 11: Error Threshold Alerting
        For any error count exceeding the configured threshold, exactly one
        alert notification SHALL be sent.

        Args:
            error_message: Description of the error.
        """
        self.error_state = record_error(
            self.error_state,
            error_message,
            datetime.now(),
        )

        logger.error(
            "Error occurred",
            error=error_message,
            error_count=self.error_state.error_count,
            consecutive_errors=self.error_state.consecutive_errors,
        )

        # Check if we should send an alert
        if should_send_error_alert(self.error_state, self.config.error_threshold):
            # Schedule alert sending (don't await to avoid blocking)
            asyncio.create_task(self._send_error_alert_async())

    async def _send_error_alert_async(self) -> None:
        """Send error alert asynchronously."""
        try:
            result = await self.send_error_alert(
                error_count=self.error_state.error_count,
                threshold=self.config.error_threshold,
                last_error=self.error_state.last_error or "Unknown error",
            )

            if result and result.success:
                self.error_state = mark_alert_sent(self.error_state)
                logger.info("Error alert sent successfully")
            else:
                logger.warning("Failed to send error alert")
        except Exception as e:
            logger.error("Exception sending error alert", error=str(e))

    async def _log_agent_event(self, event_type: str) -> None:
        """Log an agent lifecycle event.

        Args:
            event_type: Type of event (agent_started, agent_stopped).
        """
        if self.logging_agent:
            try:
                await self.logging_agent.log_event(
                    event_type=event_type,
                    data={
                        "timestamp": datetime.now().isoformat(),
                        "config": {
                            "polling_interval": self.config.polling_interval,
                            "temperature_threshold": self.config.temperature_threshold,
                        },
                    },
                )
            except Exception as e:
                logger.error("Failed to log agent event", error=str(e))

    def _update_temperature_history(self, temperature_data: Any) -> None:
        """Update temperature history for GraphQL queries.

        Args:
            temperature_data: Temperature data to record.
        """
        entry = {
            "ambient_temperature": temperature_data.ambient_temperature,
            "target_temperature": temperature_data.target_temperature,
            "thermostat_id": temperature_data.thermostat_id,
            "timestamp": temperature_data.timestamp.isoformat(),
            "humidity": temperature_data.humidity,
            "hvac_mode": temperature_data.hvac_mode,
        }

        self._latest_temperature = entry
        self._temperature_history.append(entry)

        # Keep only last 24 hours of data (assuming 60s intervals = 1440 entries)
        max_entries = 1440
        if len(self._temperature_history) > max_entries:
            self._temperature_history = self._temperature_history[-max_entries:]

    def _record_adjustment_event(
        self,
        previous_target: float,
        new_target: float,
        ambient: float,
    ) -> None:
        """Record an adjustment event for GraphQL queries.

        Args:
            previous_target: Previous target temperature.
            new_target: New target temperature.
            ambient: Ambient temperature at time of adjustment.
        """
        event = {
            "id": f"adj_{datetime.now().timestamp()}",
            "previous_setting": previous_target,
            "new_setting": new_target,
            "ambient_temperature": ambient,
            "trigger_reason": f"Differential below {self.config.temperature_threshold}°F",
            "timestamp": datetime.now().isoformat(),
            "notification_sent": self.can_send_notification(),
        }

        self._adjustment_history.append(event)

        # Keep only last 100 adjustments
        if len(self._adjustment_history) > 100:
            self._adjustment_history = self._adjustment_history[-100:]

    def get_latest_temperature(self) -> dict | None:
        """Get the latest temperature reading for GraphQL.

        Returns:
            Latest temperature data or None.
        """
        return self._latest_temperature

    def get_temperature_history(self, hours: int = 24) -> list[dict]:
        """Get temperature history for GraphQL.

        Args:
            hours: Number of hours of history to return.

        Returns:
            List of temperature readings.
        """
        if not self._temperature_history:
            return []

        # Calculate cutoff time
        cutoff = datetime.now() - timedelta(hours=hours)
        cutoff_str = cutoff.isoformat()

        return [
            entry for entry in self._temperature_history
            if entry["timestamp"] >= cutoff_str
        ]

    def get_adjustment_history(self, limit: int = 10) -> list[dict]:
        """Get adjustment history for GraphQL.

        Args:
            limit: Maximum number of adjustments to return.

        Returns:
            List of adjustment events (most recent first).
        """
        return list(reversed(self._adjustment_history[-limit:]))

    def get_uptime_seconds(self) -> float:
        """Get agent uptime in seconds.

        Returns:
            Uptime in seconds, or 0 if not started.
        """
        if self._start_time is None:
            return 0.0
        return (datetime.now() - self._start_time).total_seconds()

    def get_health_status(self) -> dict:
        """Get health status for health endpoint.

        Returns:
            Health status dictionary.
        """
        is_healthy = (
            self.running and
            self.error_state.consecutive_errors < self.config.error_threshold
        )

        return {
            "status": "healthy" if is_healthy else "degraded",
            "running": self.running,
            "uptime_seconds": self.get_uptime_seconds(),
            "error_count": self.error_state.error_count,
            "consecutive_errors": self.error_state.consecutive_errors,
            "last_error": self.error_state.last_error,
            "adjustment_count": self.adjustment_state.adjustment_count,
            "notification_count": self.notification_state.notification_count,
            "in_cooldown": self.is_in_cooldown(),
        }

    def get_readiness_status(self) -> dict:
        """Get readiness status for readiness endpoint.

        Returns:
            Readiness status dictionary.
        """
        is_ready = (
            self.nest_agent is not None and
            self.config is not None
        )

        return {
            "ready": is_ready,
            "nest_agent_configured": self.nest_agent is not None,
            "logging_agent_configured": self.logging_agent is not None,
            "config_loaded": self.config is not None,
        }
