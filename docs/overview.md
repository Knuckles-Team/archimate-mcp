# Overview

`archimate-mcp` is a self-contained **ArchiMate model engine** exposed as a Model
Context Protocol server and an A2A agent. It gives AI agents the full ArchiMate 3.x
authoring surface — create, load, and save models; full CRUD on elements,
relationships, folders, and views; query and traverse the model; and import/export
the **Open Group Model Exchange File Format** so models open directly in
[Archi](https://www.archimatetool.com/).

Archi has no native server API, so `archimate-mcp` ships its own dependency-light
engine built on the Python standard library (`xml.etree.ElementTree`). No external
service is required: the engine reads and writes a local Open Exchange Format file.

## Layered design

- **`ArchiMateModel`** (`archimate_mcp/api/archimate_model.py`) — the in-memory model
  with the ArchiMate type system and Open Exchange Format serialization.
- **`ArchiApi`** (`archimate_mcp/api/api_client_archi.py`) — a stateful façade over a
  single model file. It is the equivalent of an HTTP API client in the other `*-mcp`
  packages, but drives the local engine rather than a remote server.
- **MCP tools** (`archimate_mcp/mcp/mcp_archi.py`) — thin FastMCP wrappers that add no
  business logic; the entire authoring surface lives in `api/`.
- **A2A agent** (`archimate_mcp/agent_server.py`) — wraps the tool surface as a
  Pydantic-AI agent for graph-orchestrated workflows.

## Tool surface

| Tool | Purpose |
|---|---|
| `archi_model` | Model lifecycle: new / load / save / export_exchange / import_exchange / summary |
| `archi_element` | Element CRUD: add / get / update / delete / list / find |
| `archi_relationship` | Relationship CRUD + validate |
| `archi_view` | Views (diagrams): create / add_element / add_connection / list / get |
| `archi_folder` | Organizations (folders): add / move / list |
| `archi_query` | Query / traversal: neighbors / relationships_of / by_type + vocabulary |

The complete ArchiMate vocabulary — Strategy, Business, Application, Technology,
Physical, Motivation, and Implementation layers, and every relationship type — is
supported, with structural validation and round-trip Open Exchange serialization.

See [Usage](usage.md) for worked examples and [Concepts](concepts.md) for the stable
concept registry.
