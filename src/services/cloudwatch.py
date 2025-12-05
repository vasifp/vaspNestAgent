"""CloudWatch client for logging and metrics.

Implements connection to CloudWatch Logs and Metrics for observability.
"""

import json
import time
from datetime import datetime
from typing import Any

import boto3
import structlog
from botocore.exceptions import ClientError

logger = structlog.get_logger(__name__)


class CloudWatchError(Exception):
    """Base exception for CloudWatch errors."""

    pass


class CloudWatchClient:
    """Client for AWS CloudWatch Logs and Metrics.

    Handles log event publishing and custom metric publishing
    for the vaspNestAgent dashboard.
    """

    METRIC_NAMESPACE = "vaspNestAgent"

    def __init__(
        self,
        log_group: str,
        region: str = "us-east-1",
        log_stream_prefix: str = "agent",
    ):
        """Initialize the CloudWatch client.

        Args:
            log_group: CloudWatch log group name (e.g., "/vaspNestAgent/logs")
            region: AWS region
            log_stream_prefix: Prefix for log stream names
        """
        self.log_group = log_group
        self.region = region
        self.log_stream_prefix = log_stream_prefix

        self._logs_client = boto3.client("logs", region_name=region)
        self._metrics_client = boto3.client("cloudwatch", region_name=region)

        self._log_stream_name: str | None = None
        self._sequence_token: str | None = None
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize the CloudWatch client.

        Creates log group and log stream if they don't exist.
        """
        try:
            # Ensure log group exists
            await self._ensure_log_group()

            # Create log stream for this session
            self._log_stream_name = f"{self.log_stream_prefix}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            await self._create_log_stream()

            self._initialized = True
            logger.info(
                "CloudWatch client initialized",
                log_group=self.log_group,
                log_stream=self._log_stream_name,
            )
        except Exception as e:
            logger.error("Failed to initialize CloudWatch client", error=str(e))
            raise CloudWatchError(f"Failed to initialize CloudWatch: {e}") from e

    async def _ensure_log_group(self) -> None:
        """Ensure the log group exists, create if not."""
        try:
            self._logs_client.create_log_group(logGroupName=self.log_group)
            logger.info("Created log group", log_group=self.log_group)
        except ClientError as e:
            if e.response["Error"]["Code"] != "ResourceAlreadyExistsException":
                raise

    async def _create_log_stream(self) -> None:
        """Create a new log stream."""
        try:
            self._logs_client.create_log_stream(
                logGroupName=self.log_group,
                logStreamName=self._log_stream_name,
            )
        except ClientError as e:
            if e.response["Error"]["Code"] != "ResourceAlreadyExistsException":
                raise

    async def put_log_events(self, events: list[dict[str, Any]]) -> bool:
        """Write log events to CloudWatch Logs.

        Args:
            events: List of log events, each with 'timestamp' and 'message' keys.

        Returns:
            True if successful, False otherwise.
        """
        if not self._initialized or not self._log_stream_name:
            logger.warning("CloudWatch client not initialized, skipping log events")
            return False

        if not events:
            return True

        try:
            # Format events for CloudWatch
            log_events = [
                {
                    "timestamp": int(event.get("timestamp", time.time() * 1000)),
                    "message": event.get("message", json.dumps(event)),
                }
                for event in events
            ]

            # Sort by timestamp (required by CloudWatch)
            log_events.sort(key=lambda x: x["timestamp"])

            kwargs: dict[str, Any] = {
                "logGroupName": self.log_group,
                "logStreamName": self._log_stream_name,
                "logEvents": log_events,
            }

            if self._sequence_token:
                kwargs["sequenceToken"] = self._sequence_token

            response = self._logs_client.put_log_events(**kwargs)
            self._sequence_token = response.get("nextSequenceToken")

            return True
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "InvalidSequenceTokenException":
                # Get the correct sequence token and retry
                self._sequence_token = e.response["Error"]["Message"].split()[-1]
                return await self.put_log_events(events)
            logger.error("Failed to put log events", error=str(e))
            return False
        except Exception as e:
            logger.error("Unexpected error putting log events", error=str(e))
            return False

    async def put_log_event(self, event: dict[str, Any]) -> bool:
        """Write a single log event to CloudWatch Logs.

        Args:
            event: Log event dictionary.

        Returns:
            True if successful, False otherwise.
        """
        return await self.put_log_events([event])

    async def publish_metric(
        self,
        metric_name: str,
        value: float,
        unit: str = "None",
        dimensions: dict[str, str] | None = None,
    ) -> bool:
        """Publish a custom metric to CloudWatch Metrics.

        Args:
            metric_name: Name of the metric
            value: Metric value
            unit: Unit of measurement (e.g., "Count", "Seconds", "None")
            dimensions: Optional metric dimensions

        Returns:
            True if successful, False otherwise.
        """
        try:
            metric_data: dict[str, Any] = {
                "MetricName": metric_name,
                "Value": value,
                "Unit": unit,
                "Timestamp": datetime.utcnow(),
            }

            if dimensions:
                metric_data["Dimensions"] = [
                    {"Name": k, "Value": v} for k, v in dimensions.items()
                ]

            self._metrics_client.put_metric_data(
                Namespace=self.METRIC_NAMESPACE,
                MetricData=[metric_data],
            )

            logger.debug(
                "Published metric",
                metric_name=metric_name,
                value=value,
                unit=unit,
            )
            return True
        except Exception as e:
            logger.error("Failed to publish metric", metric_name=metric_name, error=str(e))
            return False

    async def publish_metrics(
        self,
        metrics: list[dict[str, Any]],
    ) -> bool:
        """Publish multiple metrics to CloudWatch Metrics.

        Args:
            metrics: List of metric dictionaries with keys:
                - metric_name: str
                - value: float
                - unit: str (optional, default "None")
                - dimensions: dict (optional)

        Returns:
            True if all successful, False otherwise.
        """
        if not metrics:
            return True

        try:
            metric_data = []
            for m in metrics:
                data: dict[str, Any] = {
                    "MetricName": m["metric_name"],
                    "Value": m["value"],
                    "Unit": m.get("unit", "None"),
                    "Timestamp": datetime.utcnow(),
                }
                if m.get("dimensions"):
                    data["Dimensions"] = [
                        {"Name": k, "Value": v} for k, v in m["dimensions"].items()
                    ]
                metric_data.append(data)

            # CloudWatch allows max 20 metrics per call
            for i in range(0, len(metric_data), 20):
                batch = metric_data[i:i + 20]
                self._metrics_client.put_metric_data(
                    Namespace=self.METRIC_NAMESPACE,
                    MetricData=batch,
                )

            return True
        except Exception as e:
            logger.error("Failed to publish metrics", error=str(e))
            return False

    # Convenience methods for common metrics

    async def publish_temperature_reading(
        self,
        ambient: float,
        target: float,
        thermostat_id: str,
    ) -> bool:
        """Publish temperature reading metrics."""
        return await self.publish_metrics([
            {
                "metric_name": "AmbientTemperature",
                "value": ambient,
                "unit": "None",
                "dimensions": {"ThermostatId": thermostat_id},
            },
            {
                "metric_name": "TargetTemperature",
                "value": target,
                "unit": "None",
                "dimensions": {"ThermostatId": thermostat_id},
            },
        ])

    async def publish_adjustment_count(self, count: int = 1) -> bool:
        """Publish temperature adjustment count metric."""
        return await self.publish_metric(
            metric_name="AdjustmentCount",
            value=float(count),
            unit="Count",
        )

    async def publish_notification_result(self, success: bool) -> bool:
        """Publish notification success/failure metric."""
        metric_name = "NotificationSuccess" if success else "NotificationFailure"
        return await self.publish_metric(
            metric_name=metric_name,
            value=1.0,
            unit="Count",
        )

    async def publish_api_latency(
        self,
        api_name: str,
        latency_ms: float,
    ) -> bool:
        """Publish API call latency metric."""
        return await self.publish_metric(
            metric_name=f"{api_name}Latency",
            value=latency_ms,
            unit="Milliseconds",
        )

    async def publish_error_count(self, count: int = 1) -> bool:
        """Publish error count metric."""
        return await self.publish_metric(
            metric_name="ErrorCount",
            value=float(count),
            unit="Count",
        )

    async def publish_health_status(self, healthy: bool) -> bool:
        """Publish health status metric (1 = healthy, 0 = unhealthy)."""
        return await self.publish_metric(
            metric_name="HealthStatus",
            value=1.0 if healthy else 0.0,
            unit="None",
        )

    @property
    def is_initialized(self) -> bool:
        """Check if the client is initialized."""
        return self._initialized
