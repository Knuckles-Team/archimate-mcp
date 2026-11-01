# CONN-ARCHIMATE-MCP-CONNECTOR-CONTENT — Implementation plan

Governing spec: [spec.md](spec.md). Rows: [requirements.md](requirements.md).

## Summary

`pyproject.toml` declares `archimate-mcp` as the connector identity. `create_mcp_server` resolves the packaged content of `archimate_mcp` from it.

## Technical Context

- **Language/Version**: Python 3.14 (floor 3.12)
- **Primary Dependencies**: scion-sdk, fastmcp
- **Storage**: N/A; the connector stores nothing
- **Testing**: pytest; the proof level each row names
- **Target Platform**: Linux containers
- **Project Type**: connector (MCP server)
- **Performance Goals**: N/A
- **Constraints**: one tool per API operation; shared capabilities come from the SDK
- **Scale/Scope**: 2 rows

## Constitution Check

- One owner per concept: pass. The connector owns one external system's calls, mappings and tools only.
- Connectors depend on the SDK and are called through arbora: pass.
- No ratchets: pass. The rows add no suppression.

## Project Structure

```text
pyproject.toml  existing
archimate_mcp/connector_sources.py  existing
```

## Phase 0: Research

No unknowns. Each row names the code it touches.

## Phase 1: Design

The rows are delivered in place; the design is the caller chain below.

## Phase 2: Task approach

`tasks.md` holds one task line per row, producer first.

## Complexity Tracking

None. The constitution check passed.

## Build contract

The repository pre-commit hooks apply: `ruff-format`, `connector-standard`, `secrets`, `tests-fast`. Each row names its proving test. No suppression and no duplicate implementation.

## Production caller chain

1. `CONN-ARCHIMATE-MCP-CONNECTOR-CONTENT-R001`: the `archimate-mcp` console script (`scion_sdk.cli:serve`) loads the `scion_sdk.connector` entry point `archimate_mcp:connector` (`archimate_mcp/__init__.py:83`), which the SDK `build_server` turns into the served MCP server and its resources and prompts.
2. `CONN-ARCHIMATE-MCP-CONNECTOR-CONTENT-R002`: arbora calls `fleet.call` for the existing read tool `archimate_list_elements and archimate_list_relationships` (`register_archi_tools` at `archimate_mcp/mcp/mcp_archi.py:28`; client methods `list_elements` at `archimate_mcp/api/api_client_archi.py:177` and `list_relationships` at line 305) -> the connector source in `archimate_mcp/connector_sources.py` -> the packaged `archimate_mcp/ontology/access_contracts.ttl` (planned, not yet present).

## Cross-repo seams

none. The cited owner rows are library capabilities the connector calls in process; spec.md names them.
