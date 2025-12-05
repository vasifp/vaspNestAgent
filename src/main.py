"""Main entry point for vaspNestAgent.

Initializes configuration, agents, and servers, then starts the monitoring loop.
"""

import asyncio
import signal
import sys
from typing import Optional

import structlog

from src.config import Config, ConfigurationError
from src.agents.orchestration import OrchestrationAgent
from src.agents.nest import NestAgent
from src.agents.logging import LoggingAgent
from src.server.health import HealthServer

logger = structlog.get_logger(__name__)


class Application:
    """Main application class coordinating all components."""

    def __init__(self):
        self.config: Optional[Config] = None
        self.orchestration_agent: Optional[OrchestrationAgent] = None
        self.nest_agent: Optional[NestAgent] = None
        self.logging_agent: Optional[LoggingAgent] = None
        self.health_server: Optional[HealthServer] = None
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

        try:
            await asyncio.gather(health_task, agent_task, return_exceptions=True)
        except asyncio.CancelledError:
            pass

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
        loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))


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
