"""Public client facade for archimate_mcp.

Mirrors the ``Api`` facade pattern used across the ``*-mcp`` packages. Here the
underlying client is the self-contained ArchiMate model engine rather than an
HTTP client, since Archi has no remote API.
"""

from archimate_mcp.api.api_client_archi import ArchiApi

__version__ = "0.2.0"


class Api(ArchiApi):
    """ArchiMate model engine — full authoring capabilities for agents."""

    pass
