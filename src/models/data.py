"""Data models for vaspNestAgent."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional, Any
import json


class EventType(Enum):
    """Event types for logging."""

    TEMPERATURE_READING = "temperature_reading"
    TEMPERATURE_ADJUSTMENT = "temperature_adjustment"
    NOTIFICATION_SENT = "notification_sent"
    NOTIFICATION_FAILED = "notification_failed"
    API_ERROR = "api_error"
    AGENT_STARTED = "agent_started"
    AGENT_STOPPED = "agent_stopped"
    CONFIG_LOADED = "config_loaded"
    HEALTH_CHECK = "health_check"


class Severity(Enum):
    """Log severity levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class TemperatureData:
    """Temperature reading from Nest thermostat."""

    ambient_temperature: float  # Fahrenheit
    target_temperature: float  # Fahrenheit
    thermostat_id: str
    timestamp: datetime
    humidity: Optional[float] = None
    hvac_mode: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "ambient_temperature": self.ambient_temperature,
            "target_temperature": self.target_temperature,
            "thermostat_id": self.thermostat_id,
            "timestamp": self.timestamp.isoformat(),
            "humidity": self.humidity,
            "hvac_mode": self.hvac_mode,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TemperatureData":
        """Create from dictionary."""
        return cls(
            ambient_temperature=float(data["ambient_temperature"]),
            target_temperature=float(data["target_temperature"]),
            thermostat_id=str(data["thermostat_id"]),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if isinstance(data["timestamp"], str)
            else data["timestamp"],
            humidity=float(data["humidity"]) if data.get("humidity") is not None else None,
            hvac_mode=data.get("hvac_mode"),
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "TemperatureData":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class AdjustmentResult:
    """Result of temperature adjustment operation."""

    success: bool
    previous_target: float
    new_target: float
    timestamp: datetime
    error_message: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "previous_target": self.previous_target,
            "new_target": self.new_target,
            "timestamp": self.timestamp.isoformat(),
            "error_message": self.error_message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AdjustmentResult":
        """Create from dictionary."""
        return cls(
            success=bool(data["success"]),
            previous_target=float(data["previous_target"]),
            new_target=float(data["new_target"]),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if isinstance(data["timestamp"], str)
            else data["timestamp"],
            error_message=data.get("error_message"),
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "AdjustmentResult":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class AdjustmentEvent:
    """Event logged when temperature is adjusted."""

    previous_setting: float
    new_setting: float
    ambient_temperature: float
    trigger_reason: str
    timestamp: datetime
    thermostat_id: str
    event_type: EventType = field(default=EventType.TEMPERATURE_ADJUSTMENT)
    notification_sent: bool = False
    id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "previous_setting": self.previous_setting,
            "new_setting": self.new_setting,
            "ambient_temperature": self.ambient_temperature,
            "trigger_reason": self.trigger_reason,
            "timestamp": self.timestamp.isoformat(),
            "thermostat_id": self.thermostat_id,
            "event_type": self.event_type.value,
            "notification_sent": self.notification_sent,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AdjustmentEvent":
        """Create from dictionary."""
        return cls(
            id=data.get("id"),
            previous_setting=float(data["previous_setting"]),
            new_setting=float(data["new_setting"]),
            ambient_temperature=float(data["ambient_temperature"]),
            trigger_reason=str(data["trigger_reason"]),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if isinstance(data["timestamp"], str)
            else data["timestamp"],
            thermostat_id=str(data["thermostat_id"]),
            event_type=EventType(data.get("event_type", EventType.TEMPERATURE_ADJUSTMENT.value)),
            notification_sent=bool(data.get("notification_sent", False)),
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "AdjustmentEvent":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class NotificationEvent:
    """Event logged when notification is sent."""

    phone_number_masked: str  # Masked for logging (e.g., "***-***-0574")
    message_summary: str
    success: bool
    timestamp: datetime
    event_type: EventType = field(default=EventType.NOTIFICATION_SENT)
    error_message: Optional[str] = None
    previous_temperature: Optional[float] = None
    new_temperature: Optional[float] = None
    ambient_temperature: Optional[float] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "phone_number_masked": self.phone_number_masked,
            "message_summary": self.message_summary,
            "success": self.success,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "error_message": self.error_message,
            "previous_temperature": self.previous_temperature,
            "new_temperature": self.new_temperature,
            "ambient_temperature": self.ambient_temperature,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NotificationEvent":
        """Create from dictionary."""
        event_type_value = data.get("event_type", EventType.NOTIFICATION_SENT.value)
        return cls(
            phone_number_masked=str(data["phone_number_masked"]),
            message_summary=str(data["message_summary"]),
            success=bool(data["success"]),
            timestamp=datetime.fromisoformat(data["timestamp"])
            if isinstance(data["timestamp"], str)
            else data["timestamp"],
            event_type=EventType(event_type_value),
            error_message=data.get("error_message"),
            previous_temperature=float(data["previous_temperature"])
            if data.get("previous_temperature") is not None
            else None,
            new_temperature=float(data["new_temperature"])
            if data.get("new_temperature") is not None
            else None,
            ambient_temperature=float(data["ambient_temperature"])
            if data.get("ambient_temperature") is not None
            else None,
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "NotificationEvent":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class LogEvent:
    """Structured log event for CloudWatch."""

    timestamp: datetime
    event_type: EventType
    severity: Severity
    data: dict[str, Any]
    message: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "data": self.data,
            "message": self.message,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LogEvent":
        """Create from dictionary."""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"])
            if isinstance(data["timestamp"], str)
            else data["timestamp"],
            event_type=EventType(data["event_type"]),
            severity=Severity(data["severity"]),
            data=data["data"],
            message=data.get("message"),
        )

    def to_json(self) -> str:
        """Serialize to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, json_str: str) -> "LogEvent":
        """Deserialize from JSON string."""
        return cls.from_dict(json.loads(json_str))


@dataclass
class HealthResponse:
    """Health check response."""

    status: str  # "healthy" or "degraded"
    nest_api_connected: bool
    last_temperature_reading: Optional[datetime]
    uptime_seconds: float
    error_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "status": self.status,
            "nest_api_connected": self.nest_api_connected,
            "last_temperature_reading": self.last_temperature_reading.isoformat()
            if self.last_temperature_reading
            else None,
            "uptime_seconds": self.uptime_seconds,
            "error_count": self.error_count,
        }


@dataclass
class ReadinessResponse:
    """Readiness check response."""

    ready: bool
    config_loaded: bool
    agents_initialized: bool
    details: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "ready": self.ready,
            "config_loaded": self.config_loaded,
            "agents_initialized": self.agents_initialized,
            "details": self.details,
        }
