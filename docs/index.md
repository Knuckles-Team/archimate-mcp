# archimate-mcp

A self-contained **ArchiMate model engine** exposed as an **MCP server and A2A
agent** — full ArchiMate 3.x authoring for AI agents, with round-trip Open Group
Model Exchange File Format so models open directly in
[Archi](https://www.archimatetool.com/).

!!! info "Official documentation"
    This site is the canonical reference for `archimate-mcp`, maintained alongside
    every release.

[![PyPI](https://img.shields.io/pypi/v/archimate-mcp)](https://pypi.org/project/archimate-mcp/)
![MCP Server](https://badge.mcpx.dev?type=server 'MCP Server')
[![License](https://img.shields.io/pypi/l/archimate-mcp)](https://github.com/Knuckles-Team/archimate-mcp/blob/main/LICENSE)
[![GitHub](https://img.shields.io/badge/source-GitHub-181717?logo=github)](https://github.com/Knuckles-Team/archimate-mcp)

## Overview

`archimate-mcp` gives AI agents the full ArchiMate 3.x authoring surface through
typed, deterministic MCP tools. Archi has no native server API, so this package
ships its own dependency-light engine built on the Python standard library
(`xml.etree.ElementTree`). It provides:

- **`ArchiApi`** — a stateful façade over a single ArchiMate model file: model
  lifecycle, full CRUD on elements, relationships, folders, and views (diagrams),
  query/traversal, and Open Exchange Format import/export.
- **Six MCP tools** — `archi_model`, `archi_element`, `archi_relationship`,
  `archi_view`, `archi_folder`, and `archi_query`, spanning the complete ArchiMate
  vocabulary (Strategy, Business, Application, Technology, Physical, Motivation, and
  Implementation layers) with structural validation.
- **An A2A agent server** — the `archimate-agent` console script wraps the same
  tool surface as a Pydantic-AI agent for graph-orchestrated workflows.

Models authored through `archimate-mcp` round-trip the Open Group Model Exchange
File Format, so they open directly in Archi and any conformant ArchiMate tool.

## Explore the documentation

<div class="grid cards" markdown>

- :material-rocket-launch: **[Installation](installation.md)** — pip, source, extras, and the prebuilt Docker image.
- :material-server-network: **[Deployment](deployment.md)** — run the MCP and agent servers, Docker Compose, Caddy + Technitium.
- :material-console: **[Usage](usage.md)** — the MCP tools, the `ArchiApi` client, and the CLI entry points.
- :material-sitemap: **[Overview](overview.md)** — the model engine, layered façade, and MCP/A2A surface.
- :material-tag-multiple: **[Concepts](concepts.md)** — the `CONCEPT:ARCHI-*` registry.

</div>

## Quick start

```bash
pip install "archimate-mcp[mcp]"
archimate-mcp                       # stdio MCP server (default transport)
```

Point it at a working model file and run an HTTP server:

```bash
export ARCHI_MODEL_PATH=./model.archimate
archimate-mcp --transport http --host 0.0.0.0 --port 8000
```

See **[Installation](installation.md)** and **[Deployment](deployment.md)** for the
full matrix (PyPI extras, Docker image, all transports, the A2A agent server,
reverse proxy, and DNS).
