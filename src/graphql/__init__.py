"""GraphQL schema and resolvers for vaspNestAgent."""

# Lazy imports to avoid import errors when ariadne is not installed
__all__ = ["get_type_defs", "get_resolvers", "create_graphql_app"]


def get_type_defs():
    """Get GraphQL type definitions."""
    from src.graphql.schema import get_type_defs as _get_type_defs
    return _get_type_defs()


def get_resolvers():
    """Get GraphQL resolvers."""
    from src.graphql.resolvers import get_resolvers as _get_resolvers
    return _get_resolvers()


def create_graphql_app(agent=None):
    """Create GraphQL FastAPI app."""
    from src.server.graphql import create_graphql_app as _create_graphql_app
    return _create_graphql_app(agent)
