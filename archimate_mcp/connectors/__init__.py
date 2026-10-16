"""ArchiMate source-connector contribution (CONCEPT:AU-KG.ingest.mcp-tool-connector).

Data-only subpackage: it carries ``mcp_source_presets.json`` (Tier-1 ``mcp_tool``
source presets) which the agent-connector-sdk hub federates via the
``agent_connector_sdk.source_connector_providers`` entry-point. It holds no business
logic and no heavy imports so the hub can resolve it cheaply.
"""
