# CONN-ARCHIMATE-MCP-CONNECTOR-CONTENT — Design and implementation plan

Governing spec: [spec.md](spec.md).

## Architecture

`pyproject.toml` declares `archimate-mcp` as the connector identity. `create_mcp_server` resolves the packaged content of `archimate_mcp` from it.
