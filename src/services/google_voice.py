"""Google Voice client for sending SMS notifications.

Implements SMS sending with retry logic and exponential backoff.
"""

import asyncio
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import httpx
import structlog

logger = structlog.get_logger(__name__)


class GoogleVoiceError(Exception):
    """Base exception for Google Voice API errors."""
    pass


class GoogleVoiceAuthError(GoogleVoiceError):
    """Authentication error with Google Voice."""
    pass


class GoogleVoiceRateLimitError(GoogleVoiceError):
    """Rate limit exceeded for Google Voice API."""
    pass


@dataclass
class SMSResult:
    """Result of an SMS send operation."""
    success: bool
    message_id: Optional[str] = None
    timestamp: datetime = None
    error_message: Optional[str] = None
    retry_count: int = 0

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


def calculate_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
) -> float:
    """Calculate exponential backoff delay with jitter.
    
    Args:
        attempt: Current attempt number (0-indexed).
        base_delay: Base delay in seconds.
        max_delay: Maximum delay in seconds.
        
    Returns:
        Delay in seconds with jitter applied.
    """
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = random.uniform(0, delay * 0.1)
    return delay + jitter


class GoogleVoiceClient:
    """Client for Google Voice SMS API.
    
    Handles authentication and SMS sending with retry logic.
    """

    # API endpoints (Google Voice uses internal APIs)
    BASE_URL = "https://voice.google.com"
    
    # Retry configuration
    MAX_RETRIES = 3
    BASE_DELAY = 1.0
    MAX_DELAY = 30.0

    def __init__(
        self,
        credentials: str,
        phone_number: str,
        max_retries: int = 3,
    ):
        """Initialize the Google Voice client.
        
        Args:
            credentials: Google Voice credentials (OAuth token or service account).
            phone_number: Target phone number for notifications.
            max_retries: Maximum retry attempts for failed requests.
        """
        self.credentials = credentials
        self.phone_number = phone_number
        self.max_retries = max_retries
        self._client: Optional[httpx.AsyncClient] = None
        self._retry_count = 0

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                headers={
                    "Authorization": f"Bearer {self.credentials}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def send_sms(self, message: str) -> SMSResult:
        """Send an SMS message to the configured phone number.
        
        Property 3: Retry Limit Compliance
        The retry count SHALL NOT exceed the configured maximum (3 for notifications).
        
        Args:
            message: Message content to send.
            
        Returns:
            SMSResult with success status and details.
        """
        self._retry_count = 0
        last_error: Optional[str] = None

        for attempt in range(self.max_retries + 1):
            try:
                result = await self._send_sms_attempt(message)
                result.retry_count = self._retry_count
                return result
            except GoogleVoiceAuthError as e:
                # Don't retry auth errors
                logger.error("Google Voice authentication failed", error=str(e))
                return SMSResult(
                    success=False,
                    error_message=f"Authentication failed: {e}",
                    retry_count=self._retry_count,
                )
            except GoogleVoiceRateLimitError as e:
                # Rate limit - wait longer before retry
                last_error = str(e)
                if attempt < self.max_retries:
                    self._retry_count += 1
                    delay = calculate_backoff(attempt, self.BASE_DELAY * 2, self.MAX_DELAY)
                    logger.warning(
                        "Rate limited, retrying",
                        attempt=attempt + 1,
                        delay=delay,
                    )
                    await asyncio.sleep(delay)
            except GoogleVoiceError as e:
                last_error = str(e)
                if attempt < self.max_retries:
                    self._retry_count += 1
                    delay = calculate_backoff(attempt, self.BASE_DELAY, self.MAX_DELAY)
                    logger.warning(
                        "SMS send failed, retrying",
                        attempt=attempt + 1,
                        delay=delay,
                        error=str(e),
                    )
                    await asyncio.sleep(delay)
            except Exception as e:
                last_error = str(e)
                if attempt < self.max_retries:
                    self._retry_count += 1
                    delay = calculate_backoff(attempt, self.BASE_DELAY, self.MAX_DELAY)
                    logger.warning(
                        "Unexpected error, retrying",
                        attempt=attempt + 1,
                        delay=delay,
                        error=str(e),
                    )
                    await asyncio.sleep(delay)

        # All retries exhausted
        logger.error(
            "SMS send failed after all retries",
            max_retries=self.max_retries,
            last_error=last_error,
        )
        return SMSResult(
            success=False,
            error_message=f"Failed after {self.max_retries} retries: {last_error}",
            retry_count=self._retry_count,
        )

    async def _send_sms_attempt(self, message: str) -> SMSResult:
        """Attempt to send an SMS message.
        
        Args:
            message: Message content to send.
            
        Returns:
            SMSResult on success.
            
        Raises:
            GoogleVoiceError: On API errors.
        """
        client = await self._get_client()

        # Google Voice SMS API payload
        payload = {
            "phoneNumber": self.phone_number,
            "text": message,
        }

        try:
            response = await client.post(
                f"{self.BASE_URL}/v1/messages:send",
                json=payload,
            )

            if response.status_code == 401:
                raise GoogleVoiceAuthError("Invalid or expired credentials")
            
            if response.status_code == 429:
                raise GoogleVoiceRateLimitError("Rate limit exceeded")
            
            if response.status_code >= 400:
                raise GoogleVoiceError(
                    f"API error: {response.status_code} - {response.text}"
                )

            # Parse response
            data = response.json()
            message_id = data.get("messageId", "unknown")

            logger.info(
                "SMS sent successfully",
                message_id=message_id,
                phone_number=self._mask_phone(self.phone_number),
            )

            return SMSResult(
                success=True,
                message_id=message_id,
            )

        except httpx.TimeoutException as e:
            raise GoogleVoiceError(f"Request timeout: {e}")
        except httpx.RequestError as e:
            raise GoogleVoiceError(f"Request error: {e}")

    def get_retry_count(self) -> int:
        """Get the number of retries from the last operation."""
        return self._retry_count

    @staticmethod
    def _mask_phone(phone: str) -> str:
        """Mask phone number for logging."""
        if len(phone) >= 4:
            return "***-***-" + phone[-4:]
        return "****"


def format_adjustment_notification(
    previous_target: float,
    new_target: float,
    ambient: float,
) -> str:
    """Format a temperature adjustment notification message.
    
    Property 4: Notification Content Completeness
    The message SHALL contain the previous temperature, new temperature, 
    and current ambient temperature.
    
    Args:
        previous_target: Previous target temperature in Fahrenheit.
        new_target: New target temperature in Fahrenheit.
        ambient: Current ambient temperature in Fahrenheit.
        
    Returns:
        Formatted notification message.
    """
    return (
        f"vaspNestAgent: Temperature adjusted. "
        f"Previous: {previous_target:.1f}°F, "
        f"New: {new_target:.1f}°F, "
        f"Ambient: {ambient:.1f}°F"
    )


def format_error_alert(
    error_count: int,
    threshold: int,
    last_error: str,
) -> str:
    """Format an error threshold alert message.
    
    Args:
        error_count: Current error count.
        threshold: Error threshold that was exceeded.
        last_error: Description of the last error.
        
    Returns:
        Formatted alert message.
    """
    return (
        f"vaspNestAgent ALERT: Error threshold exceeded. "
        f"Errors: {error_count}/{threshold}. "
        f"Last error: {last_error}"
    )
