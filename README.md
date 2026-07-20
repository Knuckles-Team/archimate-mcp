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
| `archimate-mcp[mcp]` | Connector-focused MCP server (`agent-utilities[mcp]` — FastMCP/FastAPI + `epistemic-graph[full]`) | You only run the **MCP server** (smallest install / image) |
| `archimate-mcp[agent]` | Agent runtime (`agent-utilities[agent-runtime,logfire]` — model orchestration + `epistemic-graph[full]`) | You run the **integrated agent** |
| `archimate-mcp[all]` | Everything (`mcp` + `agent` + `logfire`) | Development / both surfaces |

```bash
# Connector-focused MCP server (includes the shared graph engine)
uv pip install "archimate-mcp[mcp]"

# Agent runtime (adds model orchestration to the shared graph engine)
uv pip install "archimate-mcp[agent]"

# Everything (development)
uv pip install "archimate-mcp[all]"      # or: python -m pip install "archimate-mcp[all]"
```

### Container images (`:mcp` vs `:agent`)

One multi-stage `docker/Dockerfile` builds two right-sized images, selected by `--target`:

| Image tag | Build target | Contents | Entrypoint |
|-----------|--------------|----------|------------|
| `example/archimate-mcp:mcp` | `--target mcp` | `archimate-mcp[mcp]` — **connector-focused**, includes `epistemic-graph[full]`; no model-orchestration stack | `archimate-mcp` |
| `example/archimate-mcp@sha256:<digest>` | `--target agent` (default) | `archimate-mcp[agent]` — **agent runtime**, model orchestration + `epistemic-graph[full]` | `archimate-agent` |

```bash
docker build --target mcp   -t example/archimate-mcp:mcp    docker/   # connector-focused MCP server
docker build --target agent -t example/archimate-mcp:agent-local docker/   # agent runtime
```

`docker/mcp.compose.yml` runs the connector-focused `:mcp` server; `docker/agent.compose.yml` runs the
agent (`immutable agent digest`) with a co-located `:mcp` sidecar.

### Knowledge-graph database (`epistemic-graph`)

Both `[mcp]` and `[agent]` carry the **epistemic-graph** engine through the required
Agent Utilities core dependency (`epistemic-graph[full]`). The `[mcp]` extra keeps
the server connector-focused; `[agent]` additionally enables model orchestration. Local
deployments can use the bundled engine. For production or shared state, run
**epistemic-graph as a dedicated database service** and configure the runtime to use it.
Deployment recipes (single-node + Raft HA), connection configuration, and architecture
diagrams are documented in the
[epistemic-graph deployment guide](https://knuckles-team.github.io/epistemic-graph/deployment/).

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

`archimate-mcp` can run as a local stdio process or container, or behind a remote
network boundary. The
[Deployment guide](https://knuckles-team.github.io/archimate-mcp/deployment/) carries
the detailed transport contract.

- **Local container** — launch a reviewed immutable image as a least-privilege
  stdio child with no listener or published port.
- **Remote URL** — connect through an operator-supplied authenticated HTTPS
  ingress. Keep its URL, outbound identity references, trust profile, and exact
  `MCP_ALLOWED_HOSTS` in `AgentConfig`.
<!-- END GENERATED: additional-deployment-options -->

## Environment Variables

<!-- ENV-VARS-TABLE:START -->

#### Package environment variables

| Variable | Example | Description |
|----------|---------|-------------|
| `ARCHI_MODEL_PATH` | `./model.archimate` |  |
| `ARCHI_KG_INGEST` | `1` |  |
| `ARCHITOOL` | `True` |  |

#### Inherited agent-utilities variables (apply to every connector)

| Variable | Example | Description |
|----------|---------|-------------|
| `TRANSPORT` | `stdio` | MCP transport: `stdio` \| `streamable-http` \| `sse` |
| `HOST` | `127.0.0.1` | Loopback bind host (set an authenticated ingress explicitly) |
| `PORT` | `8000` | Bind port (HTTP transports) |
| `MCP_TOOL_MODE` | `intent` | Tool surface: `intent` \| `condensed` \| `verbose` \| `both` |
| `MCP_ENABLED_TOOLS` | — | Comma-separated tool allow-list |
| `MCP_DISABLED_TOOLS` | — | Comma-separated tool deny-list |
| `MCP_ENABLED_TAGS` | — | Comma-separated tag allow-list |
| `MCP_DISABLED_TAGS` | — | Comma-separated tag deny-list |
| `EUNOMIA_TYPE` | `none` | Authorization mode: `none` \| `embedded` \| `remote` |
| `EUNOMIA_POLICY_FILE` | `mcp_policies.json` | Embedded Eunomia policy file |
| `EUNOMIA_REMOTE_URL` | — | Remote Eunomia authorization server URL |
| `ENABLE_OTEL` | `False` | Enable OpenTelemetry export |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | — | OTLP collector endpoint |
| `MCP_CLIENT_AUTH` | — | Outbound MCP child auth: `oidc-client-credentials` \| `basic` \| `none` |
| `OIDC_CLIENT_ID` | — | OIDC client id (service-account auth) |
| `OIDC_CLIENT_SECRET_REF` | `secret://identity/oidc-client-secret` | Runtime secret reference for the OIDC service account |
| `MCP_BASIC_AUTH_USERNAME` | — | HTTP Basic username (`MCP_CLIENT_AUTH=basic`) |
| `MCP_BASIC_AUTH_PASSWORD_REF` | `secret://identity/mcp-basic-password` | Runtime secret reference for HTTP Basic auth (`MCP_CLIENT_AUTH=basic`) |
| `DEBUG` | `False` | Verbose logging |
| `PYTHONUNBUFFERED` | `1` | Unbuffered stdout (recommended in containers) |
| `MCP_URL` | `http://localhost:8000/mcp` | URL of the MCP server the agent connects to |
| `PROVIDER` | `openai` | LLM provider for the agent |
| `MODEL_ID` | `gpt-4o` | Model id for the agent |
| `ENABLE_WEB_UI` | `True` | Serve the AG-UI web interface |

_3 package + 24 inherited variable(s). Auto-generated from `.env.example` + the shared agent-utilities set — do not edit._
<!-- ENV-VARS-TABLE:END -->


Every variable the server reads, grouped by concern.

### Model & engine
| Variable | Description | Default |
|----------|-------------|---------|
| `ARCHI_MODEL_PATH` | Path to the working model file (Open Exchange Format) | `./model.archimate` |
| `ARCHI_KG_INGEST` | Ingest loaded/imported models through the governed ChangeEnvelope path | `1` |

### MCP server / transport
| Variable | Description | Default |
|----------|-------------|---------|
| `TRANSPORT` | `stdio`, `streamable-http`, or `sse` | `stdio` |
| `HOST` | Bind host (HTTP transports) | `127.0.0.1` |
| `PORT` | Bind port (HTTP transports) | `8000` |
| `MCP_TOOL_MODE` | Tool surface: `intent`, `condensed`, `verbose`, or `both` | `intent` |
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
| `ENABLE_OTEL` | Enable OpenTelemetry export | `False` |
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

#### Condensed action-routed tools (`MCP_TOOL_MODE=condensed`)

| MCP Tool | Toggle Env Var | Description |
|----------|----------------|-------------|
| `archi_element` | `ARCHITOOL` | Create, read, update, delete, list, or search elements. |
| `archi_folder` | `ARCHITOOL` | Manage organizations (folders) and place items in them. |
| `archi_model` | `ARCHITOOL` | Manage the model lifecycle and Open Exchange import/export. |
| `archi_query` | `ARCHITOOL` | Traverse and introspect the model and its vocabulary. |
| `archi_relationship` | `ARCHITOOL` | Create, read, update, delete, list, or validate relationships. |
| `archi_view` | `ARCHITOOL` | Create views (diagrams) and place elements/connections on them. |
| `archimate_ingest_model` | `ARCHITOOL` | Natively ingest the ArchiMate model into epistemic-graph as typed nodes. |

#### Verbose 1:1 API-mapped tools (`MCP_TOOL_MODE=verbose` or `both`)

<details>
<summary>32 per-operation tools — one per public API method (click to expand)</summary>

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
| `archimate_ingest_to_kg` | `ARCHI_APITOOL` | Push the current model into epistemic-graph as typed OWL nodes. |
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

_7 action-routed tool(s) · 32 verbose 1:1 tool(s). Each is enabled unless its `<DOMAIN>TOOL` toggle is set false; `MCP_TOOL_MODE` selects the surface (**`intent` default** — the six verb-tools, granular set loaded on demand · `condensed` action-routed · `verbose` 1:1 · `both`). Auto-generated — do not edit._
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


<!-- BEGIN agent-utilities-deployment (generated; do not edit between markers) -->

## Deploy with `agent-utilities-deployment`

Provision this package with the consolidated **`agent-utilities-deployment`**
workflow. It selects an installed-package, editable-source, or immutable-container
path; records only runtime secret and TLS-profile references in `AgentConfig`; and
runs doctor, registration, policy, observability, and rollback gates. Ask your agent
to **"deploy `archimate-mcp` with agent-utilities-deployment"**.

| Install mode | Command |
|------|---------|
| Installed package | `uv tool install "archimate-mcp[mcp]"`, then run `archimate-mcp` |
| Editable source | `uv pip install -e ".[agent]"`, then run `archimate-mcp` |
| Immutable container | deploy `registry.example.invalid/archimate-mcp@sha256:<digest>` through the operator-selected orchestrator |

The repository embeds no deployment profile, credential value, certificate path, or
environment-specific endpoint. Supply those at runtime through `AgentConfig` and the
configured secret provider.

<!-- END agent-utilities-deployment -->

<!-- GOVERNED-CAPABILITY:START -->
## Governed capability contract

This package ships a compact canonical skill surface with specialist procedures
kept as referenced workflows. The current MCP tools, skill metadata,
`connector_manifest.yml`, ontology, mappings, shapes, fixtures, migrations,
tool-schema fingerprints, and certification metadata form one versioned
capability contract. Validate them together; do not rely on stale tool names or
historical per-task skill wrappers.

Runtime endpoints, credentials, certificate trust, tenant identity, retention,
and observability policy are deployment inputs and are never packaged values.
See [Configuration, trust, and privacy](docs/configuration.md) before enabling a
network transport, connector ingestion, GraphOS delegation, or trace export.
<!-- GOVERNED-CAPABILITY:END -->
