# Installation

`archimate-mcp` is a standard Python package and a prebuilt container image. Pick
the path that matches how you want to run it.

## Requirements

- **Python 3.11 – 3.14**.
- No external services. The model engine is self-contained (Python standard-library
  XML); models are read from and written to a local Open Exchange Format file.

## From PyPI (recommended)

```bash
pip install archimate-mcp
```

### Optional extras

The base install is intentionally minimal. Install the extra for what you need:

| Extra | Install | Pulls in |
|---|---|---|
| `mcp` | `pip install "archimate-mcp[mcp]"` | FastMCP MCP-server runtime (`agent-utilities[mcp]`) |
| `agent` | `pip install "archimate-mcp[agent]"` | Pydantic-AI agent + Logfire tracing (`agent-utilities[agent,logfire]`) |
| `all` | `pip install "archimate-mcp[all]"` | Everything above |
| `test` | `pip install "archimate-mcp[test]"` | `pytest`, `pytest-asyncio`, `pytest-cov`, `pytest-xdist` |

```bash
# Typical: run the MCP server and the A2A agent
pip install "archimate-mcp[all]"
```

## From source

```bash
git clone https://github.com/Knuckles-Team/archimate-mcp.git
cd archimate-mcp
pip install -e ".[all]"          # editable install with every extra
```

With [`uv`](https://docs.astral.sh/uv/):

```bash
uv pip install -e ".[all]"
uv run archimate-mcp
```

## Prebuilt Docker image

A multi-stage, slim image is published on every release (installs
`archimate-mcp[all]`, entrypoint `archimate-mcp`):

```bash
docker pull knucklessg1/archimate-mcp:latest

docker run --rm -i \
  -e ARCHI_MODEL_PATH=/data/model.archimate \
  -v "$PWD:/data" \
  knucklessg1/archimate-mcp:latest        # stdio transport (default)
```

For an HTTP server with a published port and the A2A agent, see
[Deployment](deployment.md).

## Verify the install

```bash
archimate-mcp --help
python -c "import archimate_mcp; print(archimate_mcp.__version__)"
```

## Next steps

- **[Deployment](deployment.md)** — run it as a long-lived MCP or agent server behind Caddy + DNS.
- **[Usage](usage.md)** — call the tools, the `ArchiApi` client, and the CLI.
- **[Configuration](deployment.md#configuration-environment)** — every environment variable.
