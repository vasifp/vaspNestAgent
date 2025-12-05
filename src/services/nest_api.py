"""Nest API client for thermostat interactions.

Implements OAuth2 authentication, temperature reading, and temperature adjustment
with exponential backoff retry logic.
"""

import asyncio
import random
from datetime import datetime, timedelta
from typing import Any, Optional

import httpx
import structlog

from src.models.data import TemperatureData, AdjustmentResult

logger = structlog.get_logger(__name__)


class NestAPIError(Exception):
    """Base exception for Nest API errors."""

    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class NestAuthenticationError(NestAPIError):
    """Raised when authentication fails."""

    pass


class NestRateLimitError(NestAPIError):
    """Raised when rate limited by the API."""

    pass


class NestAPIClient:
    """Client for Google Nest Smart Device Management API.
    
    Handles OAuth2 authentication, token refresh, and API calls with
    exponential backoff retry logic.
    """

    OAUTH_TOKEN_URL = "https://oauth2.googleapis.com/token"
    SDM_API_BASE = "https://smartdevicemanagement.googleapis.com/v1"
    
    # Retry configuration
    MAX_CONNECTION_RETRIES = 5
    MAX_ADJUSTMENT_RETRIES = 3
    BASE_RETRY_DELAY = 1.0  # seconds
    MAX_RETRY_DELAY = 60.0  # seconds

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        refresh_token: str,
        project_id: str,
    ):
        """Initialize the Nest API client.
        
        Args:
            client_id: OAuth2 client ID
            client_secret: OAuth2 client secret
            refresh_token: OAuth2 refresh token
            project_id: Google Cloud project ID for SDM API
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.project_id = project_id
        
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._http_client: Optional[httpx.AsyncClient] = None
        self._thermostat_id: Optional[str] = None

    async def __aenter__(self) -> "NestAPIClient":
        """Async context manager entry."""
        self._http_client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    async def authenticate(self) -> None:
        """Authenticate with Google OAuth2 and obtain access token.
        
        Uses the refresh token to obtain a new access token.
        Implements exponential backoff retry on failure.
        
        Raises:
            NestAuthenticationError: If authentication fails after retries.
        """
        for attempt in range(self.MAX_CONNECTION_RETRIES):
            try:
                await self._refresh_access_token()
                logger.info("Successfully authenticated with Nest API")
                return
            except Exception as e:
                delay = self._calculate_backoff(attempt)
                logger.warning(
                    "Authentication attempt failed",
                    attempt=attempt + 1,
                    max_attempts=self.MAX_CONNECTION_RETRIES,
                    error=str(e),
                    retry_delay=delay,
                )
                if attempt < self.MAX_CONNECTION_RETRIES - 1:
                    await asyncio.sleep(delay)
                else:
                    raise NestAuthenticationError(
                        f"Failed to authenticate after {self.MAX_CONNECTION_RETRIES} attempts: {e}"
                    )

    async def _refresh_access_token(self) -> None:
        """Refresh the OAuth2 access token."""
        if not self._http_client:
            self._http_client = httpx.AsyncClient(timeout=30.0)

        response = await self._http_client.post(
            self.OAUTH_TOKEN_URL,
            data={
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "grant_type": "refresh_token",
            },
        )

        if response.status_code != 200:
            raise NestAuthenticationError(
                f"Token refresh failed: {response.status_code} - {response.text}",
                status_code=response.status_code,
            )

        data = response.json()
        self._access_token = data["access_token"]
        expires_in = data.get("expires_in", 3600)
        self._token_expiry = datetime.now() + timedelta(seconds=expires_in - 60)

    async def _ensure_authenticated(self) -> None:
        """Ensure we have a valid access token."""
        if not self._access_token or (
            self._token_expiry and datetime.now() >= self._token_expiry
        ):
            await self._refresh_access_token()

    def _get_headers(self) -> dict[str, str]:
        """Get HTTP headers with authorization."""
        return {
            "Authorization": f"Bearer {self._access_token}",
            "Content-Type": "application/json",
        }

    async def get_thermostat_data(self) -> TemperatureData:
        """Get current temperature data from the thermostat.
        
        Implements exponential backoff retry on failure.
        
        Returns:
            TemperatureData with current ambient and target temperatures.
            
        Raises:
            NestAPIError: If the API call fails after retries.
        """
        for attempt in range(self.MAX_CONNECTION_RETRIES):
            try:
                return await self._fetch_thermostat_data()
            except NestRateLimitError:
                delay = self._calculate_backoff(attempt, base_delay=5.0)
                logger.warning(
                    "Rate limited, waiting before retry",
                    attempt=attempt + 1,
                    retry_delay=delay,
                )
                if attempt < self.MAX_CONNECTION_RETRIES - 1:
                    await asyncio.sleep(delay)
                else:
                    raise
            except Exception as e:
                delay = self._calculate_backoff(attempt)
                logger.warning(
                    "Failed to get thermostat data",
                    attempt=attempt + 1,
                    max_attempts=self.MAX_CONNECTION_RETRIES,
                    error=str(e),
                    retry_delay=delay,
                )
                if attempt < self.MAX_CONNECTION_RETRIES - 1:
                    await asyncio.sleep(delay)
                else:
                    raise NestAPIError(
                        f"Failed to get thermostat data after {self.MAX_CONNECTION_RETRIES} attempts: {e}"
                    )
        
        # Should never reach here, but satisfy type checker
        raise NestAPIError("Unexpected error in get_thermostat_data")

    async def _fetch_thermostat_data(self) -> TemperatureData:
        """Fetch thermostat data from the API."""
        await self._ensure_authenticated()
        
        if not self._http_client:
            self._http_client = httpx.AsyncClient(timeout=30.0)

        # First, get the list of devices to find the thermostat
        if not self._thermostat_id:
            devices_url = f"{self.SDM_API_BASE}/enterprises/{self.project_id}/devices"
            response = await self._http_client.get(
                devices_url, headers=self._get_headers()
            )
            
            if response.status_code == 429:
                raise NestRateLimitError("Rate limited by Nest API", status_code=429)
            
            if response.status_code != 200:
                raise NestAPIError(
                    f"Failed to list devices: {response.status_code} - {response.text}",
                    status_code=response.status_code,
                )
            
            devices = response.json().get("devices", [])
            for device in devices:
                if "sdm.devices.types.THERMOSTAT" in device.get("type", ""):
                    self._thermostat_id = device["name"]
                    break
            
            if not self._thermostat_id:
                raise NestAPIError("No thermostat found in the account")

        # Get the thermostat details
        response = await self._http_client.get(
            f"{self.SDM_API_BASE}/{self._thermostat_id}",
            headers=self._get_headers(),
        )

        if response.status_code == 429:
            raise NestRateLimitError("Rate limited by Nest API", status_code=429)

        if response.status_code != 200:
            raise NestAPIError(
                f"Failed to get thermostat: {response.status_code} - {response.text}",
                status_code=response.status_code,
            )

        data = response.json()
        traits = data.get("traits", {})
        
        # Extract temperature data
        temperature_trait = traits.get("sdm.devices.traits.Temperature", {})
        thermostat_trait = traits.get("sdm.devices.traits.ThermostatTemperatureSetpoint", {})
        humidity_trait = traits.get("sdm.devices.traits.Humidity", {})
        mode_trait = traits.get("sdm.devices.traits.ThermostatMode", {})

        # Convert from Celsius to Fahrenheit
        ambient_c = temperature_trait.get("ambientTemperatureCelsius", 20.0)
        ambient_f = self._celsius_to_fahrenheit(ambient_c)

        # Get target temperature (heat or cool setpoint)
        target_c = thermostat_trait.get(
            "heatCelsius",
            thermostat_trait.get("coolCelsius", 21.0)
        )
        target_f = self._celsius_to_fahrenheit(target_c)

        humidity = humidity_trait.get("ambientHumidityPercent")
        hvac_mode = mode_trait.get("mode")

        return TemperatureData(
            ambient_temperature=round(ambient_f, 1),
            target_temperature=round(target_f, 1),
            thermostat_id=self._thermostat_id,
            timestamp=datetime.now(),
            humidity=humidity,
            hvac_mode=hvac_mode,
        )

    async def set_temperature(self, target_fahrenheit: float) -> AdjustmentResult:
        """Set the thermostat target temperature.
        
        Implements exponential backoff retry on failure (max 3 attempts).
        
        Args:
            target_fahrenheit: Target temperature in Fahrenheit.
            
        Returns:
            AdjustmentResult indicating success or failure.
        """
        # Get current temperature first
        current_data = await self.get_thermostat_data()
        previous_target = current_data.target_temperature

        for attempt in range(self.MAX_ADJUSTMENT_RETRIES):
            try:
                await self._set_temperature_api(target_fahrenheit)
                logger.info(
                    "Temperature adjustment successful",
                    previous=previous_target,
                    new=target_fahrenheit,
                )
                return AdjustmentResult(
                    success=True,
                    previous_target=previous_target,
                    new_target=target_fahrenheit,
                    timestamp=datetime.now(),
                )
            except Exception as e:
                delay = self._calculate_backoff(attempt)
                logger.warning(
                    "Temperature adjustment failed",
                    attempt=attempt + 1,
                    max_attempts=self.MAX_ADJUSTMENT_RETRIES,
                    error=str(e),
                    retry_delay=delay,
                )
                if attempt < self.MAX_ADJUSTMENT_RETRIES - 1:
                    await asyncio.sleep(delay)
                else:
                    return AdjustmentResult(
                        success=False,
                        previous_target=previous_target,
                        new_target=target_fahrenheit,
                        timestamp=datetime.now(),
                        error_message=f"Failed after {self.MAX_ADJUSTMENT_RETRIES} attempts: {e}",
                    )

        # Should never reach here
        return AdjustmentResult(
            success=False,
            previous_target=previous_target,
            new_target=target_fahrenheit,
            timestamp=datetime.now(),
            error_message="Unexpected error",
        )

    async def _set_temperature_api(self, target_fahrenheit: float) -> None:
        """Make the API call to set temperature."""
        await self._ensure_authenticated()
        
        if not self._http_client:
            self._http_client = httpx.AsyncClient(timeout=30.0)

        if not self._thermostat_id:
            # Fetch thermostat ID if not cached
            await self.get_thermostat_data()

        target_celsius = self._fahrenheit_to_celsius(target_fahrenheit)

        # Execute command to set temperature
        command_url = f"{self.SDM_API_BASE}/{self._thermostat_id}:executeCommand"
        
        # Determine if we're in heat or cool mode
        current_data = await self._fetch_thermostat_data()
        
        if current_data.hvac_mode == "COOL":
            command = "sdm.devices.commands.ThermostatTemperatureSetpoint.SetCool"
            params = {"coolCelsius": target_celsius}
        else:
            command = "sdm.devices.commands.ThermostatTemperatureSetpoint.SetHeat"
            params = {"heatCelsius": target_celsius}

        response = await self._http_client.post(
            command_url,
            headers=self._get_headers(),
            json={
                "command": command,
                "params": params,
            },
        )

        if response.status_code == 429:
            raise NestRateLimitError("Rate limited by Nest API", status_code=429)

        if response.status_code not in (200, 201):
            raise NestAPIError(
                f"Failed to set temperature: {response.status_code} - {response.text}",
                status_code=response.status_code,
            )

    def _calculate_backoff(
        self, attempt: int, base_delay: float | None = None
    ) -> float:
        """Calculate exponential backoff delay with jitter.
        
        Args:
            attempt: Current attempt number (0-indexed).
            base_delay: Base delay in seconds (default: BASE_RETRY_DELAY).
            
        Returns:
            Delay in seconds before next retry.
        """
        base = base_delay or self.BASE_RETRY_DELAY
        delay = min(base * (2 ** attempt), self.MAX_RETRY_DELAY)
        jitter = random.uniform(0, delay * 0.1)
        return delay + jitter

    @staticmethod
    def _celsius_to_fahrenheit(celsius: float) -> float:
        """Convert Celsius to Fahrenheit."""
        return (celsius * 9 / 5) + 32

    @staticmethod
    def _fahrenheit_to_celsius(fahrenheit: float) -> float:
        """Convert Fahrenheit to Celsius."""
        return (fahrenheit - 32) * 5 / 9

    @property
    def is_connected(self) -> bool:
        """Check if the client has a valid access token."""
        return (
            self._access_token is not None
            and self._token_expiry is not None
            and datetime.now() < self._token_expiry
        )
