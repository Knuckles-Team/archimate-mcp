# archimate-mcp

A Model Context Protocol (MCP) server for Archimate integration.

## Table of Contents
- [Overview](#overview)
- [Installation](#installation)
- [Usage](#usage)
- [Architecture](#architecture)
- [Deployment](#deployment)
- [Environment Variables](#environment-variables)
- [MCP Tools](#mcp-tools)

## Overview
archimate-mcp exposes a standardized interface to interact with Archimate using the Model Context Protocol.

## Installation
```bash
pip install -e .
```

## Usage
Run the MCP server directly:
```bash
python -m archimate_mcp
```

## Architecture
See `/docs` for architectural diagrams and further documentation.

## Deployment
### Bare-metal
```bash
python -m archimate_mcp.agent_server
```

### Docker
```bash
docker compose -f docker/agent.compose.yml up -d
```

## Environment Variables
| Variable | Description |
|----------|-------------|
| `ARCHI_WORKSPACE` | Path to models workspace |
| `ARCHI_LOG_LEVEL` | Logging level |

## MCP Tools
| Tool | Description |
|------|-------------|
| `get_archimate_info` | Retrieve basic information from Archimate |
| `query_archimate` | Run a query against the Archimate instance |
