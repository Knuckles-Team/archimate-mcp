"""Main FastMCP server and tool registration for archimate-mcp."""

import sys
from typing import Any

from agent_utilities.mcp_utilities import (
    create_mcp_server,
    load_config,
    register_tool_surface,
)
from fastmcp.utilities.logging import get_logger
from starlette.requests import Request
from starlette.responses import JSONResponse

from archimate_mcp.api_client import Api
from archimate_mcp.auth import get_client
from archimate_mcp.mcp import mcp_archi

__version__ = "0.2.0"
logger = get_logger(name="archimate_mcp")


def get_mcp_instance() -> tuple[Any, ...]:
    load_config()
    args, mcp, middlewares = create_mcp_server(
        name="ArchiMate MCP",
        version=__version__,
        instructions=(
            "ArchiMate MCP Server - a self-contained ArchiMate 3.x model "
            "engine. Author models (elements, relationships, folders, views), "
            "query/traverse them, and import/export the Open Group Model "
            "Exchange File Format so models open directly in Archi."
        ),
    )

    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request: Request) -> JSONResponse:
        return JSONResponse({"status": "OK"})

    registered_tags = register_tool_surface(
        mcp,
        client_cls=Api,
        get_client=get_client,
        service="archimate-mcp",
        tools_module=mcp_archi,
    )
    _ = registered_tags

    for mw in middlewares:
        mcp.add_middleware(mw)
    return mcp, args, middlewares


def mcp_server() -> None:
    mcp, args, middlewares = get_mcp_instance()
    print(f"ArchiMate MCP v{__version__}", file=sys.stderr)
    if args.transport == "stdio":
        mcp.run(transport="stdio")
    elif args.transport == "streamable-http":
        mcp.run(transport="streamable-http", host=args.host, port=args.port)
    elif args.transport == "sse":
        mcp.run(transport="sse", host=args.host, port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    mcp_server()
