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

## Environment Variables
| Variable | Description |
|----------|-------------|
| `ARCHI_MODEL_PATH` | Path to the working model file (Open Exchange Format). Default `./model.archimate`. |
| `ARCHITOOL` | Enable/disable the ArchiMate tool registration. Default `True`. |

## MCP Tools
| Tool | Description |
|------|-------------|
| `archi_model` | Model lifecycle: new/load/save/export_exchange/import_exchange/summary |
| `archi_element` | Element CRUD: add/get/update/delete/list/find |
| `archi_relationship` | Relationship CRUD + validate: add/get/update/delete/list/validate |
| `archi_view` | Views (diagrams): create/add_element/add_connection/list/get |
| `archi_folder` | Organizations (folders): add/move/list |
| `archi_query` | Query/traversal: neighbors/relationships_of/by_type + vocabulary |

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
