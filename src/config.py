"""Configuration management for vaspNestAgent.

Loads configuration from environment variables and AWS Secrets Manager.
Validates all configuration values against expected formats and ranges.
"""

import json
import os
import re
from dataclasses import dataclass, field

import structlog

logger = structlog.get_logger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration is invalid or missing."""

    pass


@dataclass
class Config:
    """Application configuration.

    Non-sensitive settings are loaded from environment variables.
    Sensitive credentials are loaded from AWS Secrets Manager.
    """

    # Non-sensitive settings (from environment variables)
    polling_interval: int = 60  # seconds
    cooldown_period: int = 1800  # 30 minutes in seconds
    temperature_threshold: float = 5.0  # Fahrenheit
    temperature_adjustment: float = 5.0  # Fahrenheit
    cloudwatch_log_group: str = "/vaspNestAgent/logs"
    aws_region: str = "us-east-1"
    http_port: int = 8080
    error_threshold: int = 10  # errors before alerting
    notification_rate_limit_enabled: bool = True
    notification_rate_limit_seconds: int = 3600  # 1 hour

    # Sensitive settings (from Secrets Manager)
    nest_client_id: str = ""
    nest_client_secret: str = ""
    nest_refresh_token: str = ""
    nest_project_id: str = ""
    google_voice_credentials: str = ""
    google_voice_phone_number: str = ""

    # Internal state
    _secrets_loaded: bool = field(default=False, repr=False)

    @classmethod
    def from_environment(cls) -> "Config":
        """Load configuration from environment variables only.

        Use this for local development without AWS Secrets Manager.
        """
        config = cls()
        config._load_from_environment()
        config._load_sensitive_from_environment()
        config.validate()
        return config

    @classmethod
    async def load(cls, use_secrets_manager: bool = True) -> "Config":
        """Load configuration from environment and optionally Secrets Manager.

        Args:
            use_secrets_manager: If True, load sensitive values from AWS Secrets Manager.
                               If False, load from environment variables.

        Returns:
            Configured Config instance.

        Raises:
            ConfigurationError: If required configuration is missing or invalid.
        """
        config = cls()
        config._load_from_environment()

        if use_secrets_manager:
            await config._load_from_secrets_manager()
        else:
            config._load_sensitive_from_environment()

        config.validate()
        config._log_config()
        return config

    def _load_from_environment(self) -> None:
        """Load non-sensitive configuration from environment variables."""
        env_mappings = {
            "POLLING_INTERVAL": ("polling_interval", int),
            "COOLDOWN_PERIOD": ("cooldown_period", int),
            "TEMPERATURE_THRESHOLD": ("temperature_threshold", float),
            "TEMPERATURE_ADJUSTMENT": ("temperature_adjustment", float),
            "CLOUDWATCH_LOG_GROUP": ("cloudwatch_log_group", str),
            "AWS_REGION": ("aws_region", str),
            "HTTP_PORT": ("http_port", int),
            "ERROR_THRESHOLD": ("error_threshold", int),
            "NOTIFICATION_RATE_LIMIT_ENABLED": ("notification_rate_limit_enabled", self._parse_bool),
            "NOTIFICATION_RATE_LIMIT_SECONDS": ("notification_rate_limit_seconds", int),
        }

        for env_var, (attr, converter) in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                try:
                    setattr(self, attr, converter(value))  # type: ignore[operator]
                except (ValueError, TypeError) as e:
                    raise ConfigurationError(
                        f"Invalid value for {env_var}: {value}. Error: {e}"
                    ) from e

    def _load_sensitive_from_environment(self) -> None:
        """Load sensitive configuration from environment variables.

        Used for local development without Secrets Manager.
        """
        sensitive_mappings = {
            "NEST_CLIENT_ID": "nest_client_id",
            "NEST_CLIENT_SECRET": "nest_client_secret",
            "NEST_REFRESH_TOKEN": "nest_refresh_token",
            "NEST_PROJECT_ID": "nest_project_id",
            "GOOGLE_VOICE_CREDENTIALS": "google_voice_credentials",
            "GOOGLE_VOICE_PHONE_NUMBER": "google_voice_phone_number",
        }

        for env_var, attr in sensitive_mappings.items():
            value = os.environ.get(env_var, "")
            setattr(self, attr, value)

        self._secrets_loaded = True

    async def _load_from_secrets_manager(self) -> None:
        """Load sensitive configuration from AWS Secrets Manager."""
        import boto3
        from botocore.exceptions import ClientError

        secrets_client = boto3.client("secretsmanager", region_name=self.aws_region)

        # Load Nest credentials
        try:
            nest_secret = secrets_client.get_secret_value(
                SecretId="vaspnestagent/nest-credentials"
            )
            nest_data = json.loads(nest_secret["SecretString"])
            self.nest_client_id = nest_data.get("client_id", "")
            self.nest_client_secret = nest_data.get("client_secret", "")
            self.nest_refresh_token = nest_data.get("refresh_token", "")
            self.nest_project_id = nest_data.get("project_id", "")
        except ClientError as e:
            raise ConfigurationError(
                f"Failed to load Nest credentials from Secrets Manager: {e}"
            ) from e

        # Load Google Voice credentials
        try:
            gv_secret = secrets_client.get_secret_value(
                SecretId="vaspnestagent/google-voice"
            )
            gv_data = json.loads(gv_secret["SecretString"])
            self.google_voice_credentials = gv_data.get("credentials", "")
            self.google_voice_phone_number = gv_data.get("phone_number", "")
        except ClientError as e:
            raise ConfigurationError(
                f"Failed to load Google Voice credentials from Secrets Manager: {e}"
            ) from e

        self._secrets_loaded = True

    def validate(self) -> None:
        """Validate all configuration values.

        Raises:
            ConfigurationError: If any configuration value is invalid.
        """
        errors: list[str] = []

        # Validate polling interval
        if self.polling_interval < 10:
            errors.append("polling_interval must be at least 10 seconds")
        if self.polling_interval > 3600:
            errors.append("polling_interval must be at most 3600 seconds (1 hour)")

        # Validate cooldown period
        if self.cooldown_period < 60:
            errors.append("cooldown_period must be at least 60 seconds")
        if self.cooldown_period > 86400:
            errors.append("cooldown_period must be at most 86400 seconds (24 hours)")

        # Validate temperature threshold
        if self.temperature_threshold < 1.0:
            errors.append("temperature_threshold must be at least 1.0°F")
        if self.temperature_threshold > 20.0:
            errors.append("temperature_threshold must be at most 20.0°F")

        # Validate temperature adjustment
        if self.temperature_adjustment < 1.0:
            errors.append("temperature_adjustment must be at least 1.0°F")
        if self.temperature_adjustment > 20.0:
            errors.append("temperature_adjustment must be at most 20.0°F")

        # Validate HTTP port
        if self.http_port < 1 or self.http_port > 65535:
            errors.append("http_port must be between 1 and 65535")

        # Validate error threshold
        if self.error_threshold < 1:
            errors.append("error_threshold must be at least 1")

        # Validate AWS region format
        if not re.match(r"^[a-z]{2}-[a-z]+-\d+$", self.aws_region):
            errors.append(f"Invalid AWS region format: {self.aws_region}")

        # Validate phone number format (if provided)
        if self.google_voice_phone_number:
            # Accept formats like: 480-442-0574, (480) 442-0574, 4804420574, +14804420574
            phone_pattern = r"^[\+]?[\d\s\-\(\)]{10,15}$"
            if not re.match(phone_pattern, self.google_voice_phone_number):
                errors.append(
                    f"Invalid phone number format: {self._mask_phone(self.google_voice_phone_number)}"
                )

        # Validate CloudWatch log group format
        if not self.cloudwatch_log_group.startswith("/"):
            errors.append("cloudwatch_log_group must start with '/'")

        if errors:
            raise ConfigurationError(
                "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            )

    def _log_config(self) -> None:
        """Log non-sensitive configuration values for debugging."""
        logger.info(
            "Configuration loaded",
            polling_interval=self.polling_interval,
            cooldown_period=self.cooldown_period,
            temperature_threshold=self.temperature_threshold,
            temperature_adjustment=self.temperature_adjustment,
            cloudwatch_log_group=self.cloudwatch_log_group,
            aws_region=self.aws_region,
            http_port=self.http_port,
            error_threshold=self.error_threshold,
            notification_rate_limit_enabled=self.notification_rate_limit_enabled,
            notification_rate_limit_seconds=self.notification_rate_limit_seconds,
            secrets_loaded=self._secrets_loaded,
            phone_number_configured=bool(self.google_voice_phone_number),
        )

    @staticmethod
    def _parse_bool(value: str) -> bool:
        """Parse boolean from string."""
        return value.lower() in ("true", "1", "yes", "on")

    @staticmethod
    def _mask_phone(phone: str) -> str:
        """Mask phone number for logging."""
        if len(phone) >= 4:
            return "***-***-" + phone[-4:]
        return "****"

    def get_masked_phone(self) -> str:
        """Get masked phone number for logging."""
        return self._mask_phone(self.google_voice_phone_number)
