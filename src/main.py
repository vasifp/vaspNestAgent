"""Main entry point for vaspNestAgent.

This module serves as the application entry point, coordinating the initialization
and lifecycle of all system components including:

- Configuration loading (from environment and/or AWS Secrets Manager)
- Agent initialization (OrchestrationAgent, NestAgent, LoggingAgent)
- HTTP server startup (health endpoints, GraphQL API)
- Signal handling for graceful shutdown

Usage:
    # Production (with AWS Secrets Manager)
    python -m src.main

    # Local development (environment variables only)
    python -m src.main --local

Example:
    >>> import asyncio
    >>> from src.main import Application
    >>>
    >>> async def run():
    ...     app = Application()
    ...     await app.initialize(use_secrets_manager=False)
    ...     # Application is now ready
    ...     await app.stop()
    >>>
    >>> asyncio.run(run())

Attributes:
    logger: Structured logger for this module.

See Also:
    - :mod:`src.config` for configuration management
    - :mod:`src.agents.orchestration` for the main monitoring logic
    - :mod:`src.server.health` for health check endpoints
"""

import asyncio
import contextlib
import signal
import sys

import structlog

from src.agents.logging import LoggingAgent
from src.agents.nest import NestAgent
from src.agents.orchestration import OrchestrationAgent
from src.config import Config, ConfigurationError
from src.server.health import HealthServer

logger = structlog.get_logger(__name__)


class Application:
    """Main application class coordinating all components.

    This class manages the lifecycle of all vaspNestAgent components,
    including initialization, startup, and graceful shutdown.

    The application follows this lifecycle:

    1. **Initialization** (:meth:`initialize`):
       - Load configuration from environment/Secrets Manager
       - Create agent instances (NestAgent, LoggingAgent, OrchestrationAgent)
       - Create health server

    2. **Startup** (:meth:`start`):
       - Start health server (background)
       - Start orchestration agent monitoring loop
       - Wait for shutdown signal

    3. **Shutdown** (:meth:`stop`):
       - Stop orchestration agent gracefully
       - Stop health server
       - Close agent connections

    Attributes:
        config: Application configuration instance.
        orchestration_agent: Main coordinator agent.
        nest_agent: Nest thermostat API agent.
        logging_agent: CloudWatch logging agent.
        health_server: HTTP health check server.

    Example:
        >>> app = Application()
        >>> await app.initialize(use_secrets_manager=False)
        >>> # Start in background or await app.start()
        >>> await app.stop()
    """

    def __init__(self) -> None:
        """Initialize the Application instance.

        Creates an empty application with no components initialized.
        Call :meth:`initialize` to set up components.
        """
        self.config: Config | None = None
        self.orchestration_agent: OrchestrationAgent | None = None
        self.nest_agent: NestAgent | None = None
        self.logging_agent: LoggingAgent | None = None
        self.health_server: HealthServer | None = None
        self._shutdown_event = asyncio.Event()

    async def initialize(self, use_secrets_manager: bool = True) -> None:
        """Initialize all application components.

        Args:
            use_secrets_manager: Whether to load secrets from AWS Secrets Manager.
        """
        logger.info("Initializing vaspNestAgent")

        # Load configuration
        try:
            self.config = await Config.load(use_secrets_manager=use_secrets_manager)
        except ConfigurationError as e:
            logger.error("Configuration error", error=str(e))
            raise

        # Initialize agents
        self.nest_agent = NestAgent(self.config)
        self.logging_agent = LoggingAgent(self.config)
        self.orchestration_agent = OrchestrationAgent(self.config)
        self.orchestration_agent.set_agents(self.nest_agent, self.logging_agent)

        # Initialize health server
        self.health_server = HealthServer(
            agent=self.orchestration_agent,
            port=self.config.http_port,
        )

        logger.info("Initialization complete")

    async def start(self) -> None:
        """Start all application components."""
        if self.orchestration_agent is None or self.health_server is None:
            raise RuntimeError("Application not initialized")

        logger.info("Starting vaspNestAgent")

        # Start health server in background
        health_task = asyncio.create_task(self.health_server.start())

        # Start orchestration agent (monitoring loop)
        agent_task = asyncio.create_task(self.orchestration_agent.start())

        # Wait for shutdown signal
        await self._shutdown_event.wait()

        # Stop components
        await self.stop()

        # Cancel background tasks
        health_task.cancel()
        agent_task.cancel()

        with contextlib.suppress(asyncio.CancelledError):
            await asyncio.gather(health_task, agent_task, return_exceptions=True)

    async def stop(self) -> None:
        """Stop all application components gracefully."""
        logger.info("Stopping vaspNestAgent")

        if self.orchestration_agent:
            await self.orchestration_agent.stop()

        if self.health_server:
            await self.health_server.stop()

        if self.nest_agent:
            await self.nest_agent.close()

        logger.info("vaspNestAgent stopped")

    def request_shutdown(self) -> None:
        """Request application shutdown."""
        self._shutdown_event.set()


def setup_signal_handlers(app: Application) -> None:
    """Set up signal handlers for graceful shutdown.

    Args:
        app: Application instance.
    """
    def signal_handler(sig: signal.Signals) -> None:
        logger.info(f"Received signal {sig.name}, initiating shutdown")
        app.request_shutdown()

    loop = asyncio.get_event_loop()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))  # type: ignore[misc]


async def main(use_secrets_manager: bool = True) -> int:
    """Main entry point.

    Args:
        use_secrets_manager: Whether to load secrets from AWS Secrets Manager.

    Returns:
        Exit code (0 for success, 1 for error).
    """
    app = Application()

    try:
        await app.initialize(use_secrets_manager=use_secrets_manager)
        setup_signal_handlers(app)
        await app.start()
        return 0
    except ConfigurationError as e:
        logger.error("Configuration error", error=str(e))
        return 1
    except Exception as e:
        logger.exception("Unexpected error", error=str(e))
        return 1


def run() -> None:
    """Run the application."""
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Check for --local flag to skip Secrets Manager
    use_secrets_manager = "--local" not in sys.argv

    # Run the application
    exit_code = asyncio.run(main(use_secrets_manager=use_secrets_manager))
    sys.exit(exit_code)


if __name__ == "__main__":
    run()
