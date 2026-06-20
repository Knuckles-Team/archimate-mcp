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
```bash
pip install -e .
```

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
| Variable | Description |
|----------|-------------|
| `ARCHI_MODEL_PATH` | Path to the working model file (Open Exchange Format). Default `./model.archimate`. |
| `ARCHITOOL` | Enable/disable the ArchiMate tool registration. Default `True`. |

## MCP Tools

The table below is auto-generated from the live server — do not edit by hand.

<!-- MCP-TOOLS-TABLE:START -->

| MCP Tool | Toggle Env Var | Description |
|----------|----------------|-------------|
| `archi_element` | `ARCHITOOL` | Create, read, update, delete, list, or search elements. |
| `archi_folder` | `ARCHITOOL` | Manage organizations (folders) and place items in them. |
| `archi_model` | `ARCHITOOL` | Manage the model lifecycle and Open Exchange import/export. |
| `archi_query` | `ARCHITOOL` | Traverse and introspect the model and its vocabulary. |
| `archi_relationship` | `ARCHITOOL` | Create, read, update, delete, list, or validate relationships. |
| `archi_view` | `ARCHITOOL` | Create views (diagrams) and place elements/connections on them. |

_6 action-routed tools (default `MCP_TOOL_MODE=condensed`). Each is enabled unless its toggle is set false; set `MCP_TOOL_MODE=verbose` (or `both`) for the 1:1 per-operation surface. Auto-generated — do not edit._
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
