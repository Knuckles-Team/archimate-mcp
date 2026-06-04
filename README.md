# archi-mcp

A self-contained **ArchiMate model engine** exposed as a Model Context
Protocol (MCP) server and an A2A agent. It gives AI agents full ArchiMate 3.x
authoring capabilities — create/load/save models, full CRUD on elements,
relationships, folders, and views (diagrams), query/traverse the model, and
import/export the **Open Group Model Exchange File Format** so the models open
directly in [Archi](https://www.archimatetool.com/).

Archi has no native server API, so `archi-mcp` ships its own dependency-light
engine built on the Python standard library (`xml.etree.ElementTree`).

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)
- [Deployment](#deployment)
- [Environment Variables](#environment-variables)
- [MCP Tools](#mcp-tools)

## Overview
`archi-mcp` exposes a standardized interface for authoring ArchiMate models via
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
archi-mcp
```

Or run the agent server:
```bash
archi-agent
```

## Architecture
See `/docs` for architectural diagrams and further documentation. The model
engine lives in `archi_mcp/api/` (`archimate_model.py`, `api_client_archi.py`),
the MCP tools in `archi_mcp/mcp/mcp_archi.py`.

## Deployment
### Bare-metal
```bash
archi-agent
```

### Docker
```bash
docker build -f docker/Dockerfile -t archi-mcp .
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
