"""MCP tools that are not ArchiMate model-engine operations.

Every model operation is one typed tool served from ``ArchiApi`` by the SDK tool
surface. The knowledge-graph ingest below needs the client and the graph
transport together, so it is registered here with typed inputs.
"""

from typing import Any

from fastmcp import FastMCP
from pydantic import Field

from archimate_mcp.auth import get_client


def register_archi_tools(mcp: FastMCP) -> None:
    """Register the knowledge-graph ingest tool."""

    @mcp.tool(tags={"kg"})
    async def archimate_ingest_model(
        path: str | None = Field(
            default=None,
            description=(
                "Open Exchange or Archi model file to load before ingesting. "
                "Omit to ingest the model that is currently loaded."
            ),
        ),
    ) -> Any:
        """Natively ingest the ArchiMate model into epistemic-graph as typed nodes.

        Lists the model's elements, relationships and views via the model engine and
        pushes them into the knowledge graph as ``:ArchimateElement`` subclass nodes
        (``:ApplicationComponent``, ``:BusinessProcess``, ...), reified
        ``:ArchimateRelationship`` nodes + direct edges, and ``:ArchimateView`` nodes.
        Best-effort: returns ``{"ingested": None}`` when no engine is reachable.
        CONCEPT:AU-KG.ingest.enterprise-source-extractor.
        """
        from archimate_mcp import kg_ingest

        client = get_client()
        if path:
            await client.load(path)
        result = await kg_ingest.ingest_from_api(client)
        summary = client.model_summary()
        return {"model": summary.get("counts"), "ingested": result}
