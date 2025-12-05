"""GraphQL Server for vaspNestAgent.

Integrates GraphQL API with FastAPI and WebSocket support for subscriptions.
"""

from typing import TYPE_CHECKING, Optional

import structlog
from ariadne import make_executable_schema
from ariadne.asgi import GraphQL
from ariadne.asgi.handlers import GraphQLTransportWSHandler
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.graphql.resolvers import get_resolvers
from src.graphql.schema import get_type_defs

if TYPE_CHECKING:
    from src.agents.orchestration import OrchestrationAgent

logger = structlog.get_logger(__name__)


def create_graphql_app(agent: Optional["OrchestrationAgent"] = None) -> FastAPI:
    """Create the FastAPI application with GraphQL endpoint.

    Args:
        agent: OrchestrationAgent instance for resolvers.

    Returns:
        Configured FastAPI application.
    """
    app = FastAPI(
        title="vaspNestAgent GraphQL API",
        description="GraphQL API for temperature monitoring",
        version="1.0.0",
    )

    # Add CORS middleware for frontend access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Create GraphQL schema
    type_defs = get_type_defs()
    resolvers = get_resolvers()
    schema = make_executable_schema(type_defs, *resolvers)

    # Create GraphQL ASGI app with WebSocket support
    graphql_app = GraphQL(
        schema,
        debug=True,
        websocket_handler=GraphQLTransportWSHandler(),
        context_value=lambda _request: {"agent": agent},
    )

    # Mount GraphQL endpoint
    app.mount("/graphql", graphql_app)

    # Store agent reference for updates
    app.state.agent = agent

    @app.get("/")
    async def root():
        """Root endpoint with API info."""
        return {
            "service": "vaspNestAgent GraphQL API",
            "version": "1.0.0",
            "graphql_endpoint": "/graphql",
            "subscriptions": "ws://host/graphql",
        }

    return app


class GraphQLServer:
    """GraphQL server with WebSocket subscription support.

    Requirements: 17.1, 17.2
    """

    def __init__(
        self,
        agent: Optional["OrchestrationAgent"] = None,
        port: int = 8080,
        host: str = "0.0.0.0",
    ):
        """Initialize the GraphQL server.

        Args:
            agent: OrchestrationAgent instance for resolvers.
            port: Port to listen on.
            host: Host to bind to.
        """
        self.agent = agent
        self.port = port
        self.host = host
        self.app = create_graphql_app(agent)
        self._server = None

    def set_agent(self, agent: "OrchestrationAgent") -> None:
        """Set the agent reference.

        Args:
            agent: OrchestrationAgent instance.
        """
        self.agent = agent
        self.app.state.agent = agent
        # Note: The GraphQL context is created per-request, so we need to
        # recreate the app to update the context factory
        self.app = create_graphql_app(agent)

    async def start(self) -> None:
        """Start the GraphQL server."""
        import uvicorn

        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="warning",
        )
        self._server = uvicorn.Server(config)  # type: ignore[assignment]

        logger.info(
            "Starting GraphQL server",
            host=self.host,
            port=self.port,
        )

        await self._server.serve()  # type: ignore[attr-defined]

    async def stop(self) -> None:
        """Stop the GraphQL server."""
        if self._server:
            self._server.should_exit = True
            logger.info("GraphQL server stopped")
