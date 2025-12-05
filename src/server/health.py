"""HTTP Health Server for vaspNestAgent.

Provides health, readiness, and metrics endpoints for Kubernetes probes
and monitoring systems.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING

from fastapi import FastAPI, Response
from fastapi.responses import PlainTextResponse
import structlog

if TYPE_CHECKING:
    from src.agents.orchestration import OrchestrationAgent

logger = structlog.get_logger(__name__)


def create_health_app(agent: Optional["OrchestrationAgent"] = None) -> FastAPI:
    """Create the FastAPI health server application.
    
    Args:
        agent: OrchestrationAgent instance for health checks.
        
    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title="vaspNestAgent Health Server",
        description="Health, readiness, and metrics endpoints",
        version="1.0.0",
    )
    
    # Store agent reference
    app.state.agent = agent
    
    @app.get("/health")
    async def health_check(response: Response) -> dict:
        """Health check endpoint.
        
        Returns 200 if healthy, 503 if degraded.
        
        Requirements: 6.1
        """
        if app.state.agent is None:
            response.status_code = 503
            return {
                "status": "degraded",
                "reason": "Agent not configured",
                "timestamp": datetime.now().isoformat(),
            }
        
        health = app.state.agent.get_health_status()
        
        if health["status"] != "healthy":
            response.status_code = 503
        
        return {
            **health,
            "timestamp": datetime.now().isoformat(),
        }
    
    @app.get("/ready")
    async def readiness_check(response: Response) -> dict:
        """Readiness check endpoint.
        
        Returns 200 if ready to process requests, 503 if not ready.
        
        Requirements: 6.2
        """
        if app.state.agent is None:
            response.status_code = 503
            return {
                "ready": False,
                "reason": "Agent not configured",
                "timestamp": datetime.now().isoformat(),
            }
        
        readiness = app.state.agent.get_readiness_status()
        
        if not readiness["ready"]:
            response.status_code = 503
        
        return {
            **readiness,
            "timestamp": datetime.now().isoformat(),
        }
    
    @app.get("/metrics", response_class=PlainTextResponse)
    async def metrics() -> str:
        """Prometheus-compatible metrics endpoint.
        
        Returns metrics in Prometheus text format.
        
        Requirements: 6.3, 6.4
        """
        if app.state.agent is None:
            return "# No agent configured\n"
        
        health = app.state.agent.get_health_status()
        
        lines = [
            "# HELP vaspnestagent_up Whether the agent is running",
            "# TYPE vaspnestagent_up gauge",
            f"vaspnestagent_up {1 if health['running'] else 0}",
            "",
            "# HELP vaspnestagent_uptime_seconds Agent uptime in seconds",
            "# TYPE vaspnestagent_uptime_seconds counter",
            f"vaspnestagent_uptime_seconds {health['uptime_seconds']:.2f}",
            "",
            "# HELP vaspnestagent_error_count_total Total number of errors",
            "# TYPE vaspnestagent_error_count_total counter",
            f"vaspnestagent_error_count_total {health['error_count']}",
            "",
            "# HELP vaspnestagent_consecutive_errors Current consecutive error count",
            "# TYPE vaspnestagent_consecutive_errors gauge",
            f"vaspnestagent_consecutive_errors {health['consecutive_errors']}",
            "",
            "# HELP vaspnestagent_adjustment_count_total Total temperature adjustments",
            "# TYPE vaspnestagent_adjustment_count_total counter",
            f"vaspnestagent_adjustment_count_total {health['adjustment_count']}",
            "",
            "# HELP vaspnestagent_notification_count_total Total notifications sent",
            "# TYPE vaspnestagent_notification_count_total counter",
            f"vaspnestagent_notification_count_total {health['notification_count']}",
            "",
            "# HELP vaspnestagent_in_cooldown Whether agent is in cooldown period",
            "# TYPE vaspnestagent_in_cooldown gauge",
            f"vaspnestagent_in_cooldown {1 if health['in_cooldown'] else 0}",
            "",
            "# HELP vaspnestagent_health_status Health status (1=healthy, 0=degraded)",
            "# TYPE vaspnestagent_health_status gauge",
            f"vaspnestagent_health_status {1 if health['status'] == 'healthy' else 0}",
            "",
        ]
        
        # Add temperature metrics if available
        latest_temp = app.state.agent.get_latest_temperature()
        if latest_temp:
            lines.extend([
                "# HELP vaspnestagent_ambient_temperature Current ambient temperature (F)",
                "# TYPE vaspnestagent_ambient_temperature gauge",
                f"vaspnestagent_ambient_temperature {latest_temp['ambient_temperature']:.1f}",
                "",
                "# HELP vaspnestagent_target_temperature Current target temperature (F)",
                "# TYPE vaspnestagent_target_temperature gauge",
                f"vaspnestagent_target_temperature {latest_temp['target_temperature']:.1f}",
                "",
            ])
        
        return "\n".join(lines)
    
    @app.get("/")
    async def root() -> dict:
        """Root endpoint with basic info."""
        return {
            "service": "vaspNestAgent",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "ready": "/ready",
                "metrics": "/metrics",
            },
        }
    
    return app


class HealthServer:
    """HTTP server for health and metrics endpoints.
    
    Requirements: 6.1, 6.2, 6.3, 6.5
    """
    
    def __init__(
        self,
        agent: Optional["OrchestrationAgent"] = None,
        port: int = 8080,
        host: str = "0.0.0.0",
    ):
        """Initialize the health server.
        
        Args:
            agent: OrchestrationAgent instance for health checks.
            port: Port to listen on.
            host: Host to bind to.
        """
        self.agent = agent
        self.port = port
        self.host = host
        self.app = create_health_app(agent)
        self._server = None
    
    def set_agent(self, agent: "OrchestrationAgent") -> None:
        """Set the agent reference.
        
        Args:
            agent: OrchestrationAgent instance.
        """
        self.agent = agent
        self.app.state.agent = agent
    
    async def start(self) -> None:
        """Start the HTTP server."""
        import uvicorn
        
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="warning",
        )
        self._server = uvicorn.Server(config)
        
        logger.info(
            "Starting health server",
            host=self.host,
            port=self.port,
        )
        
        await self._server.serve()
    
    async def stop(self) -> None:
        """Stop the HTTP server."""
        if self._server:
            self._server.should_exit = True
            logger.info("Health server stopped")
