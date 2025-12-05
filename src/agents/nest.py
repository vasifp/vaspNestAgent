"""NestAgent - Specialized agent for Nest thermostat API interactions.

This agent encapsulates all Nest thermostat interactions and exposes them
as Strands-compatible tools for the Orchestration Agent.
"""

from datetime import datetime
from typing import Any, Optional

import structlog

from src.config import Config
from src.models.data import TemperatureData, AdjustmentResult
from src.services.nest_api import NestAPIClient, NestAPIError

logger = structlog.get_logger(__name__)


class NestAgentError(Exception):
    """Base exception for NestAgent errors."""

    pass


class NestAgent:
    """Agent for Nest thermostat API interactions.
    
    Registers Strands tools for reading thermostat data and adjusting
    temperature settings. Handles API errors and returns structured results.
    """

    def __init__(self, config: Config):
        """Initialize the NestAgent.
        
        Args:
            config: Application configuration with Nest API credentials.
        """
        self.config = config
        self._client: Optional[NestAPIClient] = None
        self._initialized = False
        self._last_temperature: Optional[TemperatureData] = None
        self._last_error: Optional[str] = None

    async def initialize(self) -> None:
        """Initialize the agent and authenticate with Nest API.
        
        Raises:
            NestAgentError: If initialization fails.
        """
        try:
            self._client = NestAPIClient(
                client_id=self.config.nest_client_id,
                client_secret=self.config.nest_client_secret,
                refresh_token=self.config.nest_refresh_token,
                project_id=self.config.nest_project_id,
            )
            await self._client.__aenter__()
            await self._client.authenticate()
            self._initialized = True
            self._last_error = None
            logger.info("NestAgent initialized successfully")
        except Exception as e:
            self._last_error = str(e)
            logger.error("Failed to initialize NestAgent", error=str(e))
            raise NestAgentError(f"Failed to initialize NestAgent: {e}")

    async def close(self) -> None:
        """Close the agent and release resources."""
        if self._client:
            await self._client.__aexit__(None, None, None)
            self._client = None
        self._initialized = False
        logger.info("NestAgent closed")

    @property
    def is_initialized(self) -> bool:
        """Check if the agent is initialized."""
        return self._initialized

    @property
    def is_connected(self) -> bool:
        """Check if the agent has a valid connection to Nest API."""
        return self._client is not None and self._client.is_connected

    @property
    def last_temperature(self) -> Optional[TemperatureData]:
        """Get the last temperature reading."""
        return self._last_temperature

    @property
    def last_error(self) -> Optional[str]:
        """Get the last error message."""
        return self._last_error

    # Strands-compatible tool methods
    
    async def get_temperature(self) -> dict[str, Any]:
        """Get current temperature data from the thermostat.
        
        This is a Strands-compatible tool that returns structured data.
        
        Returns:
            Dictionary with temperature data or error information.
            
        Example return:
            {
                "success": True,
                "data": {
                    "ambient_temperature": 72.0,
                    "target_temperature": 75.0,
                    "thermostat_id": "...",
                    "timestamp": "2024-01-01T12:00:00",
                    "humidity": 45.0,
                    "hvac_mode": "HEAT"
                }
            }
        """
        if not self._initialized or not self._client:
            return {
                "success": False,
                "error": "NestAgent not initialized",
                "error_type": "initialization_error",
            }

        try:
            temperature_data = await self._client.get_thermostat_data()
            self._last_temperature = temperature_data
            self._last_error = None
            
            logger.debug(
                "Temperature reading obtained",
                ambient=temperature_data.ambient_temperature,
                target=temperature_data.target_temperature,
            )
            
            return {
                "success": True,
                "data": temperature_data.to_dict(),
            }
        except NestAPIError as e:
            self._last_error = str(e)
            logger.error("Failed to get temperature", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "error_type": "api_error",
                "status_code": e.status_code,
            }
        except Exception as e:
            self._last_error = str(e)
            logger.error("Unexpected error getting temperature", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected_error",
            }

    async def set_temperature(self, target_fahrenheit: float) -> dict[str, Any]:
        """Set the thermostat target temperature.
        
        This is a Strands-compatible tool that returns structured data.
        
        Args:
            target_fahrenheit: Target temperature in Fahrenheit.
            
        Returns:
            Dictionary with adjustment result or error information.
            
        Example return:
            {
                "success": True,
                "data": {
                    "success": True,
                    "previous_target": 75.0,
                    "new_target": 70.0,
                    "timestamp": "2024-01-01T12:00:00"
                }
            }
        """
        if not self._initialized or not self._client:
            return {
                "success": False,
                "error": "NestAgent not initialized",
                "error_type": "initialization_error",
            }

        # Validate temperature range
        if target_fahrenheit < 50.0 or target_fahrenheit > 90.0:
            return {
                "success": False,
                "error": f"Target temperature {target_fahrenheit}°F is outside valid range (50-90°F)",
                "error_type": "validation_error",
            }

        try:
            result = await self._client.set_temperature(target_fahrenheit)
            self._last_error = None if result.success else result.error_message
            
            if result.success:
                logger.info(
                    "Temperature adjusted",
                    previous=result.previous_target,
                    new=result.new_target,
                )
            else:
                logger.warning(
                    "Temperature adjustment failed",
                    error=result.error_message,
                )
            
            return {
                "success": result.success,
                "data": result.to_dict(),
            }
        except NestAPIError as e:
            self._last_error = str(e)
            logger.error("Failed to set temperature", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "error_type": "api_error",
                "status_code": e.status_code,
            }
        except Exception as e:
            self._last_error = str(e)
            logger.error("Unexpected error setting temperature", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "error_type": "unexpected_error",
            }

    async def get_status(self) -> dict[str, Any]:
        """Get the current status of the NestAgent.
        
        Returns:
            Dictionary with agent status information.
        """
        return {
            "initialized": self._initialized,
            "connected": self.is_connected,
            "last_temperature": self._last_temperature.to_dict() if self._last_temperature else None,
            "last_error": self._last_error,
        }

    # Tool registration for Strands SDK
    
    def get_tools(self) -> list[dict[str, Any]]:
        """Get the list of tools provided by this agent.
        
        Returns:
            List of tool definitions for Strands SDK registration.
        """
        return [
            {
                "name": "get_temperature",
                "description": "Get current ambient and target temperature from the Nest thermostat",
                "parameters": {},
                "handler": self.get_temperature,
            },
            {
                "name": "set_temperature",
                "description": "Set the target temperature on the Nest thermostat",
                "parameters": {
                    "target_fahrenheit": {
                        "type": "number",
                        "description": "Target temperature in Fahrenheit (50-90)",
                        "required": True,
                    }
                },
                "handler": self.set_temperature,
            },
            {
                "name": "get_nest_status",
                "description": "Get the current status of the NestAgent",
                "parameters": {},
                "handler": self.get_status,
            },
        ]
