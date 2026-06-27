# archimate-mcp

A self-contained **ArchiMate model engine** exposed as a Model Context
Protocol (MCP) server and an A2A agent. It gives AI agents full ArchiMate 3.x
authoring capabilities — create/load/save models, full CRUD on elements,
relationships, folders, and views (diagrams), query/traverse the model, and
import/export the **Open Group Model Exchange File Format** so the models open
directly in [Archi](https://www.archimatetool.com/).

Archi has no native server API, so `archimate-mcp` ships its own dependency-light
engine built on the Python standard library (`xml.etree.ElementTree`).

> **Documentation** — Installation, deployment, usage across the API, CLI, and MCP
> interfaces, and the A2A agent server are maintained in the
> [official documentation](https://knuckles-team.github.io/archimate-mcp/).

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)
- [Deployment](#deployment)
- [Environment Variables](#environment-variables)
- [MCP Tools](#mcp-tools)

## Overview
`archimate-mcp` exposes a standardized interface for authoring ArchiMate models via
the Model Context Protocol. The full ArchiMate vocabulary (Strategy, Business,
Application, Technology, Physical, Motivation, Implementation layers) and all
relationship types are supported, with structural validation and round-trip
Open Exchange Format serialization.

## Installation

Pick the extra that matches what you want to run:

| Extra | Installs | Use when |
|-------|----------|----------|
| `archimate-mcp[mcp]` | Slim MCP server only (`agent-utilities[mcp]` — FastMCP/FastAPI) | You only run the **MCP server** (smallest install / image) |
| `archimate-mcp[agent]` | Full agent runtime (`agent-utilities[agent,logfire]` — Pydantic AI + the epistemic-graph engine) | You run the **integrated agent** |
| `archimate-mcp[all]` | Everything (`mcp` + `agent` + `logfire`) | Development / both surfaces |

```bash
# MCP server only (recommended for tool hosting — slim deps)
uv pip install "archimate-mcp[mcp]"

# Full agent runtime (Pydantic AI + epistemic-graph engine)
uv pip install "archimate-mcp[agent]"

# Everything (development)
uv pip install "archimate-mcp[all]"      # or: python -m pip install "archimate-mcp[all]"
```

### Container images (`:mcp` vs `:agent`)

One multi-stage `docker/Dockerfile` builds two right-sized images, selected by `--target`:

| Image tag | Build target | Contents | Entrypoint |
|-----------|--------------|----------|------------|
| `knucklessg1/archimate-mcp:mcp` | `--target mcp` | `archimate-mcp[mcp]` — **slim**, no engine/`pydantic-ai`/`dspy`/`llama-index`/`tree-sitter` | `archimate-mcp` |
| `knucklessg1/archimate-mcp:latest` | `--target agent` (default) | `archimate-mcp[agent]` — **full** agent runtime + epistemic-graph engine | `archimate-agent` |

```bash
docker build --target mcp   -t knucklessg1/archimate-mcp:mcp    docker/   # slim MCP server
docker build --target agent -t knucklessg1/archimate-mcp:latest docker/   # full agent
```

`docker/mcp.compose.yml` runs the slim `:mcp` server; `docker/agent.compose.yml` runs the
agent (`:latest`) with a co-located `:mcp` sidecar.

### Knowledge-graph database (`epistemic-graph`)

The **full agent** (`[agent]` / `:latest`) embeds the **epistemic-graph** engine (pulled in
transitively via `agent-utilities[agent]`). For production — or to share one knowledge graph
across multiple agents — run **epistemic-graph as its own database container** and point the
agent at it instead of embedding it. Deployment recipes (single-node + Raft HA), connection
config, and the full database architecture (with diagrams) are documented in the
[epistemic-graph deployment guide](https://knuckles-team.github.io/epistemic-graph/deployment/).
The slim `[mcp]` server does **not** require the database.

## Usage
Run the MCP server directly:
```bash
archimate-mcp
```

Or run the agent server:
```bash
archimate-agent
```

## Architecture
See `/docs` for architectural diagrams and further documentation. The model
engine lives in `archimate_mcp/api/` (`archimate_model.py`, `api_client_archi.py`),
the MCP tools in `archimate_mcp/mcp/mcp_archi.py`.

## Deployment
### Bare-metal
```bash
archimate-agent
```

### Docker
```bash
docker build -f docker/Dockerfile -t archimate-mcp .
```

<!-- BEGIN GENERATED: additional-deployment-options -->
### Additional Deployment Options

`archimate-mcp` can also run as a **local container** (Docker / Podman / `uv`) or be
consumed from a **remote deployment**. The
[Deployment guide](https://knuckles-team.github.io/archimate-mcp/deployment/) has full, copy-paste
`mcp_config.json` for all four transports — **stdio**, **streamable-http**,
**local container / uv**, and **remote URL**:

- **Local container / uv** — launch the server from `mcp_config.json` via `uvx`,
  `docker run`, or `podman run`, or point at a local streamable-http container by `url`.
- **Remote URL** — connect to a server deployed behind Caddy at
  `http://archimate-mcp.arpa/mcp` using the `"url"` key.
<!-- END GENERATED: additional-deployment-options -->

## Environment Variables

<!-- ENV-VARS-TABLE:START -->

#### Package environment variables

| Variable | Example | Description |
|----------|---------|-------------|
| `ARCHI_MODEL_PATH` | `./model.archimate` |  |
| `ARCHITOOL` | `True` |  |

#### Inherited agent-utilities variables (apply to every connector)

| Variable | Example | Description |
|----------|---------|-------------|
| `TRANSPORT` | `stdio` | MCP transport: `stdio` | `streamable-http` | `sse` |
| `HOST` | `0.0.0.0` | Bind host (HTTP transports) |
| `PORT` | `8000` | Bind port (HTTP transports) |
| `MCP_TOOL_MODE` | `condensed` | Tool surface: `condensed` | `verbose` | `both` |
| `MCP_ENABLED_TOOLS` | — | Comma-separated tool allow-list |
| `MCP_DISABLED_TOOLS` | — | Comma-separated tool deny-list |
| `MCP_ENABLED_TAGS` | — | Comma-separated tag allow-list |
| `MCP_DISABLED_TAGS` | — | Comma-separated tag deny-list |
| `EUNOMIA_TYPE` | `none` | Authorization mode: `none` | `embedded` | `remote` |
| `EUNOMIA_POLICY_FILE` | `mcp_policies.json` | Embedded Eunomia policy file |
| `EUNOMIA_REMOTE_URL` | — | Remote Eunomia authorization server URL |
| `ENABLE_OTEL` | `False` | Enable OpenTelemetry export |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | — | OTLP collector endpoint |
| `MCP_CLIENT_AUTH` | — | Outbound MCP auth (`oidc-client-credentials` for fleet calls) |
| `OIDC_CLIENT_ID` | — | OIDC client id (service-account auth) |
| `OIDC_CLIENT_SECRET` | — | OIDC client secret (service-account auth) |
| `DEBUG` | `False` | Verbose logging |
| `PYTHONUNBUFFERED` | `1` | Unbuffered stdout (recommended in containers) |
| `MCP_URL` | `http://localhost:8000/mcp` | URL of the MCP server the agent connects to |
| `PROVIDER` | `openai` | LLM provider for the agent |
| `MODEL_ID` | `gpt-4o` | Model id for the agent |
| `ENABLE_WEB_UI` | `True` | Serve the AG-UI web interface |

_2 package + 22 inherited variable(s). Auto-generated from `.env.example` + the shared agent-utilities set — do not edit._
<!-- ENV-VARS-TABLE:END -->


Every variable the server reads, grouped by concern.

### Model & engine
| Variable | Description | Default |
|----------|-------------|---------|
| `ARCHI_MODEL_PATH` | Path to the working model file (Open Exchange Format) | `./model.archimate` |

### MCP server / transport
| Variable | Description | Default |
|----------|-------------|---------|
| `TRANSPORT` | `stdio`, `streamable-http`, or `sse` | `stdio` |
| `HOST` | Bind host (HTTP transports) | `0.0.0.0` |
| `PORT` | Bind port (HTTP transports) | `8000` |
| `MCP_TOOL_MODE` | Tool surface: `condensed`, `verbose`, or `both` | `condensed` |
| `MCP_ENABLED_TOOLS` / `MCP_DISABLED_TOOLS` | Comma-separated tool allow/deny list | — |
| `MCP_ENABLED_TAGS` / `MCP_DISABLED_TAGS` | Comma-separated tag allow/deny list | — |
| `DEBUG` | Verbose logging | `False` |
| `PYTHONUNBUFFERED` | Unbuffered stdout (recommended in containers) | `1` |

### Tool toggles
The single action-routed tool family can be disabled via its toggle env var (set to `false`).
The toggle is in the [MCP Tools](#mcp-tools) table below (`ARCHITOOL`).

### Telemetry & governance
| Variable | Description | Default |
|----------|-------------|---------|
| `ENABLE_OTEL` | Enable OpenTelemetry export | `True` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP collector endpoint | — |
| `OTEL_EXPORTER_OTLP_PUBLIC_KEY` / `OTEL_EXPORTER_OTLP_SECRET_KEY` | OTLP auth keys | — |
| `OTEL_EXPORTER_OTLP_PROTOCOL` | OTLP protocol (e.g. `http/protobuf`) | — |
| `EUNOMIA_TYPE` | Authorization mode: `none`, `embedded`, `remote` | `none` |
| `EUNOMIA_POLICY_FILE` | Embedded policy file | `mcp_policies.json` |
| `EUNOMIA_REMOTE_URL` | Remote Eunomia server URL | — |

### Agent CLI (full `[agent]` runtime only)
| Variable | Description | Default |
|----------|-------------|---------|
| `MCP_URL` | URL of the MCP server the agent connects to | `http://localhost:8000/mcp` |
| `PROVIDER` | LLM provider (e.g. `openai`) | `openai` |
| `MODEL_ID` | Model id (e.g. `gpt-4o`) | `gpt-4o` |
| `ENABLE_WEB_UI` | Serve the AG-UI web interface | `True` |

## MCP Tools

The table below is auto-generated from the live server — do not edit by hand.

<!-- MCP-TOOLS-TABLE:START -->

#### Condensed action-routed tools (default — `MCP_TOOL_MODE=condensed`)

| MCP Tool | Toggle Env Var | Description |
|----------|----------------|-------------|
| `archi_element` | `ARCHITOOL` | Create, read, update, delete, list, or search elements. |
| `archi_folder` | `ARCHITOOL` | Manage organizations (folders) and place items in them. |
| `archi_model` | `ARCHITOOL` | Manage the model lifecycle and Open Exchange import/export. |
| `archi_query` | `ARCHITOOL` | Traverse and introspect the model and its vocabulary. |
| `archi_relationship` | `ARCHITOOL` | Create, read, update, delete, list, or validate relationships. |
| `archi_view` | `ARCHITOOL` | Create views (diagrams) and place elements/connections on them. |

#### Verbose 1:1 API-mapped tools (`MCP_TOOL_MODE=verbose` or `both`)

<details>
<summary>31 per-operation tools — one per public API method (click to expand)</summary>

| MCP Tool | Toggle Env Var | Description |
|----------|----------------|-------------|
| `archimate_add_connection_to_view` | `ARCHI_APITOOL` | Invoke the add_connection_to_view operation. |
| `archimate_add_element` | `ARCHI_APITOOL` | Invoke the add_element operation. |
| `archimate_add_element_to_view` | `ARCHI_APITOOL` | Invoke the add_element_to_view operation. |
| `archimate_add_folder` | `ARCHI_APITOOL` | Invoke the add_folder operation. |
| `archimate_add_relationship` | `ARCHI_APITOOL` | Invoke the add_relationship operation. |
| `archimate_create_view` | `ARCHI_APITOOL` | Invoke the create_view operation. |
| `archimate_delete_element` | `ARCHI_APITOOL` | Invoke the delete_element operation. |
| `archimate_delete_relationship` | `ARCHI_APITOOL` | Invoke the delete_relationship operation. |
| `archimate_element_types` | `ARCHI_APITOOL` | Invoke the element_types operation. |
| `archimate_elements_by_type` | `ARCHI_APITOOL` | Invoke the elements_by_type operation. |
| `archimate_export_open_exchange` | `ARCHI_APITOOL` | Invoke the export_open_exchange operation. |
| `archimate_find_elements` | `ARCHI_APITOOL` | Invoke the find_elements operation. |
| `archimate_get_element` | `ARCHI_APITOOL` | Invoke the get_element operation. |
| `archimate_get_relationship` | `ARCHI_APITOOL` | Invoke the get_relationship operation. |
| `archimate_get_view` | `ARCHI_APITOOL` | Invoke the get_view operation. |
| `archimate_import_open_exchange` | `ARCHI_APITOOL` | Invoke the import_open_exchange operation. |
| `archimate_list_elements` | `ARCHI_APITOOL` | Invoke the list_elements operation. |
| `archimate_list_folders` | `ARCHI_APITOOL` | Invoke the list_folders operation. |
| `archimate_list_relationships` | `ARCHI_APITOOL` | Invoke the list_relationships operation. |
| `archimate_list_views` | `ARCHI_APITOOL` | Invoke the list_views operation. |
| `archimate_load` | `ARCHI_APITOOL` | Invoke the load operation. |
| `archimate_model_summary` | `ARCHI_APITOOL` | Invoke the model_summary operation. |
| `archimate_move_to_folder` | `ARCHI_APITOOL` | Invoke the move_to_folder operation. |
| `archimate_neighbors` | `ARCHI_APITOOL` | Invoke the neighbors operation. |
| `archimate_new_model` | `ARCHI_APITOOL` | Invoke the new_model operation. |
| `archimate_relationship_types` | `ARCHI_APITOOL` | Invoke the relationship_types operation. |
| `archimate_relationships_of` | `ARCHI_APITOOL` | Invoke the relationships_of operation. |
| `archimate_save` | `ARCHI_APITOOL` | Invoke the save operation. |
| `archimate_update_element` | `ARCHI_APITOOL` | Invoke the update_element operation. |
| `archimate_update_relationship` | `ARCHI_APITOOL` | Invoke the update_relationship operation. |
| `archimate_validate_relationship` | `ARCHI_APITOOL` | Return True if ``type`` is plausible between the given endpoints. |

</details>

_6 action-routed tool(s) (default) · 31 verbose 1:1 tool(s). Each is enabled unless its `<DOMAIN>TOOL` toggle is set false; `MCP_TOOL_MODE` selects the surface (`condensed` default · `verbose` 1:1 · `both`). Auto-generated — do not edit._
<!-- MCP-TOOLS-TABLE:END -->

## Documentation

The complete documentation is published as the
[official documentation site](https://knuckles-team.github.io/archimate-mcp/) and is
the recommended reference for installation, deployment, and day-to-day operation.

| Page | Contents |
|---|---|
| [Installation](https://knuckles-team.github.io/archimate-mcp/installation/) | pip, source, extras, prebuilt Docker image |
| [Deployment](https://knuckles-team.github.io/archimate-mcp/deployment/) | run the MCP and agent servers, Compose, Caddy + Technitium, env config |
| [Usage](https://knuckles-team.github.io/archimate-mcp/usage/) | the MCP tools, the `ArchiApi` client, the CLI |
| [Overview](https://knuckles-team.github.io/archimate-mcp/overview/) | the model engine, layered façade, MCP/A2A surface |
| [Concepts](https://knuckles-team.github.io/archimate-mcp/concepts/) | concept registry (`CONCEPT:ARCHI-*`) |

`AGENTS.md` is the canonical contributor/agent guidance.


<!-- BEGIN agent-os-genesis-deploy (generated; do not edit between markers) -->

## Deploy with `agent-os-genesis`

This package can be provisioned for you — skill-guided — by the **`agent-os-genesis`**
universal skill (its *single-package deploy mode*): it picks your install method, seeds
secrets to OpenBao/Vault (or `.env`), trusts your enterprise CA, registers the MCP
server, and verifies it — the same machinery that stands up the whole Agent OS, narrowed
to just this package. Ask your agent to **"deploy `archimate-mcp` with agent-os-genesis"**.

| Install mode | Command |
|------|---------|
| Bare-metal, prod (PyPI) | `uvx archimate-mcp` · or `uv tool install archimate-mcp` |
| Bare-metal, dev (editable) | `uv pip install -e ".[all]"` · or `pip install -e ".[all]"` |
| Container, prod | deploy `knucklessg1/archimate-mcp:latest` via docker-compose / swarm / podman / podman-compose / kubernetes |
| Container, dev (editable) | deploy `docker/compose.dev.yml` (source-mounted at `/src`; edits live on restart) |

Secrets are read-existing + seeded via `vault_sync` — you are only prompted for what's missing.

<!-- END agent-os-genesis-deploy -->
