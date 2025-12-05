"""LoggingAgent - Specialized agent for CloudWatch logging.

This agent handles all logging to CloudWatch with proper structure
and publishes metrics for the vaspNestAgent dashboard.
"""

from datetime import datetime
from typing import Any

import structlog

from src.config import Config
from src.models.data import (
    AdjustmentEvent,
    EventType,
    LogEvent,
    NotificationEvent,
    Severity,
    TemperatureData,
)
from src.services.cloudwatch import CloudWatchClient

logger = structlog.get_logger(__name__)


class LoggingAgentError(Exception):
    """Base exception for LoggingAgent errors."""

    pass


class LoggingAgent:
    """Agent for CloudWatch logging and metrics.

    Registers Strands tools for logging temperature readings, adjustments,
    and notifications. Formats log events with proper structure.
    """

    def __init__(self, config: Config):
        """Initialize the LoggingAgent.

        Args:
            config: Application configuration with CloudWatch settings.
        """
        self.config = config
        self._client: CloudWatchClient | None = None
        self._initialized = False
        self._event_buffer: list[LogEvent] = []
        self._buffer_size = 10  # Flush after this many events

    async def initialize(self) -> None:
        """Initialize the agent and connect to CloudWatch.

        Raises:
            LoggingAgentError: If initialization fails.
        """
        try:
            self._client = CloudWatchClient(
                log_group=self.config.cloudwatch_log_group,
                region=self.config.aws_region,
            )
            await self._client.initialize()
            self._initialized = True

            # Log agent started event
            await self.log_event(
                event_type=EventType.AGENT_STARTED,
                severity=Severity.INFO,
                data={"message": "LoggingAgent initialized"},
            )

            logger.info("LoggingAgent initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize LoggingAgent", error=str(e))
            raise LoggingAgentError(f"Failed to initialize LoggingAgent: {e}") from e

    async def close(self) -> None:
        """Close the agent and flush pending logs."""
        if self._event_buffer:
            await self.flush()

        # Log agent stopped event
        if self._initialized and self._client:
            await self.log_event(
                event_type=EventType.AGENT_STOPPED,
                severity=Severity.INFO,
                data={"message": "LoggingAgent shutting down"},
            )
            await self.flush()

        self._initialized = False
        logger.info("LoggingAgent closed")

    @property
    def is_initialized(self) -> bool:
        """Check if the agent is initialized."""
        return self._initialized

    async def flush(self) -> bool:
        """Flush buffered log events to CloudWatch.

        Returns:
            True if successful, False otherwise.
        """
        if not self._event_buffer or not self._client:
            return True

        events = [
            {
                "timestamp": int(e.timestamp.timestamp() * 1000),
                "message": e.to_json(),
            }
            for e in self._event_buffer
        ]

        success = await self._client.put_log_events(events)
        if success:
            self._event_buffer.clear()
        return success

    async def log_event(
        self,
        event_type: EventType,
        severity: Severity,
        data: dict[str, Any],
        message: str | None = None,
    ) -> bool:
        """Log a generic event to CloudWatch.

        Args:
            event_type: Type of event
            severity: Severity level
            data: Event data dictionary
            message: Optional human-readable message

        Returns:
            True if successful, False otherwise.
        """
        event = LogEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            severity=severity,
            data=data,
            message=message,
        )

        self._event_buffer.append(event)

        # Flush if buffer is full
        if len(self._event_buffer) >= self._buffer_size:
            return await self.flush()

        return True

    # Strands-compatible tool methods

    async def log_temperature_reading(
        self,
        temperature_data: TemperatureData | dict[str, Any],
    ) -> dict[str, Any]:
        """Log a temperature reading to CloudWatch.

        This is a Strands-compatible tool.

        Args:
            temperature_data: Temperature data to log

        Returns:
            Dictionary with result status.
        """
        if not self._initialized:
            return {
                "success": False,
                "error": "LoggingAgent not initialized",
            }

        try:
            # Convert dict to TemperatureData if needed
            if isinstance(temperature_data, dict):
                temp_data = TemperatureData.from_dict(temperature_data)
            else:
                temp_data = temperature_data

            # Log the event
            await self.log_event(
                event_type=EventType.TEMPERATURE_READING,
                severity=Severity.INFO,
                data={
                    "ambient_temperature": temp_data.ambient_temperature,
                    "target_temperature": temp_data.target_temperature,
                    "thermostat_id": temp_data.thermostat_id,
                    "humidity": temp_data.humidity,
                    "hvac_mode": temp_data.hvac_mode,
                },
                message=f"Temperature: ambient={temp_data.ambient_temperature}°F, target={temp_data.target_temperature}°F",
            )

            # Publish metrics
            if self._client:
                await self._client.publish_temperature_reading(
                    ambient=temp_data.ambient_temperature,
                    target=temp_data.target_temperature,
                    thermostat_id=temp_data.thermostat_id,
                )

            logger.debug(
                "Logged temperature reading",
                ambient=temp_data.ambient_temperature,
                target=temp_data.target_temperature,
            )

            return {"success": True}
        except Exception as e:
            logger.error("Failed to log temperature reading", error=str(e))
            return {"success": False, "error": str(e)}

    async def log_adjustment(
        self,
        adjustment_event: AdjustmentEvent | dict[str, Any],
    ) -> dict[str, Any]:
        """Log a temperature adjustment event to CloudWatch.

        This is a Strands-compatible tool.

        Args:
            adjustment_event: Adjustment event to log

        Returns:
            Dictionary with result status.
        """
        if not self._initialized:
            return {
                "success": False,
                "error": "LoggingAgent not initialized",
            }

        try:
            # Convert dict to AdjustmentEvent if needed
            if isinstance(adjustment_event, dict):
                event = AdjustmentEvent.from_dict(adjustment_event)
            else:
                event = adjustment_event

            # Log the event
            await self.log_event(
                event_type=EventType.TEMPERATURE_ADJUSTMENT,
                severity=Severity.INFO,
                data={
                    "previous_setting": event.previous_setting,
                    "new_setting": event.new_setting,
                    "ambient_temperature": event.ambient_temperature,
                    "trigger_reason": event.trigger_reason,
                    "thermostat_id": event.thermostat_id,
                    "notification_sent": event.notification_sent,
                },
                message=f"Temperature adjusted: {event.previous_setting}°F → {event.new_setting}°F (reason: {event.trigger_reason})",
            )

            # Publish metrics
            if self._client:
                await self._client.publish_adjustment_count()

            logger.info(
                "Logged adjustment event",
                previous=event.previous_setting,
                new=event.new_setting,
            )

            return {"success": True}
        except Exception as e:
            logger.error("Failed to log adjustment event", error=str(e))
            return {"success": False, "error": str(e)}

    async def log_notification(
        self,
        notification_event: NotificationEvent | dict[str, Any],
    ) -> dict[str, Any]:
        """Log a notification event to CloudWatch.

        This is a Strands-compatible tool.

        Args:
            notification_event: Notification event to log

        Returns:
            Dictionary with result status.
        """
        if not self._initialized:
            return {
                "success": False,
                "error": "LoggingAgent not initialized",
            }

        try:
            # Convert dict to NotificationEvent if needed
            if isinstance(notification_event, dict):
                event = NotificationEvent.from_dict(notification_event)
            else:
                event = notification_event

            # Determine event type and severity
            event_type = EventType.NOTIFICATION_SENT if event.success else EventType.NOTIFICATION_FAILED
            severity = Severity.INFO if event.success else Severity.WARNING

            # Log the event
            await self.log_event(
                event_type=event_type,
                severity=severity,
                data={
                    "phone_number_masked": event.phone_number_masked,
                    "message_summary": event.message_summary,
                    "success": event.success,
                    "error_message": event.error_message,
                    "previous_temperature": event.previous_temperature,
                    "new_temperature": event.new_temperature,
                    "ambient_temperature": event.ambient_temperature,
                },
                message=f"Notification {'sent' if event.success else 'failed'}: {event.message_summary}",
            )

            # Publish metrics
            if self._client:
                await self._client.publish_notification_result(event.success)

            logger.info(
                "Logged notification event",
                success=event.success,
                phone=event.phone_number_masked,
            )

            return {"success": True}
        except Exception as e:
            logger.error("Failed to log notification event", error=str(e))
            return {"success": False, "error": str(e)}

    async def log_error(
        self,
        error_message: str,
        error_type: str = "unknown",
        details: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Log an error event to CloudWatch.

        Args:
            error_message: Error message
            error_type: Type of error
            details: Additional error details

        Returns:
            Dictionary with result status.
        """
        if not self._initialized:
            return {
                "success": False,
                "error": "LoggingAgent not initialized",
            }

        try:
            await self.log_event(
                event_type=EventType.API_ERROR,
                severity=Severity.ERROR,
                data={
                    "error_message": error_message,
                    "error_type": error_type,
                    **(details or {}),
                },
                message=f"Error [{error_type}]: {error_message}",
            )

            # Publish error metric
            if self._client:
                await self._client.publish_error_count()

            return {"success": True}
        except Exception as e:
            logger.error("Failed to log error event", error=str(e))
            return {"success": False, "error": str(e)}

    async def publish_health_status(self, healthy: bool) -> dict[str, Any]:
        """Publish health status metric.

        Args:
            healthy: Whether the system is healthy

        Returns:
            Dictionary with result status.
        """
        if not self._client:
            return {"success": False, "error": "CloudWatch client not initialized"}

        try:
            await self._client.publish_health_status(healthy)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def publish_api_latency(
        self,
        api_name: str,
        latency_ms: float,
    ) -> dict[str, Any]:
        """Publish API latency metric.

        Args:
            api_name: Name of the API (e.g., "NestAPI", "GoogleVoice")
            latency_ms: Latency in milliseconds

        Returns:
            Dictionary with result status.
        """
        if not self._client:
            return {"success": False, "error": "CloudWatch client not initialized"}

        try:
            await self._client.publish_api_latency(api_name, latency_ms)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # Tool registration for Strands SDK

    def get_tools(self) -> list[dict[str, Any]]:
        """Get the list of tools provided by this agent.

        Returns:
            List of tool definitions for Strands SDK registration.
        """
        return [
            {
                "name": "log_temperature_reading",
                "description": "Log a temperature reading to CloudWatch",
                "parameters": {
                    "temperature_data": {
                        "type": "object",
                        "description": "Temperature data to log",
                        "required": True,
                    }
                },
                "handler": self.log_temperature_reading,
            },
            {
                "name": "log_adjustment",
                "description": "Log a temperature adjustment event to CloudWatch",
                "parameters": {
                    "adjustment_event": {
                        "type": "object",
                        "description": "Adjustment event to log",
                        "required": True,
                    }
                },
                "handler": self.log_adjustment,
            },
            {
                "name": "log_notification",
                "description": "Log a notification event to CloudWatch",
                "parameters": {
                    "notification_event": {
                        "type": "object",
                        "description": "Notification event to log",
                        "required": True,
                    }
                },
                "handler": self.log_notification,
            },
            {
                "name": "log_error",
                "description": "Log an error event to CloudWatch",
                "parameters": {
                    "error_message": {
                        "type": "string",
                        "description": "Error message",
                        "required": True,
                    },
                    "error_type": {
                        "type": "string",
                        "description": "Type of error",
                        "required": False,
                    },
                },
                "handler": self.log_error,
            },
        ]
