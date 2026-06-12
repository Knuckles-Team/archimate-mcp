# Deployment

<!-- BEGIN GENERATED: deployment-options -->
## Deployment Options

`archimate-mcp` exposes its MCP server (console script `archimate-mcp`) four ways. Pick the row that
matches where the server runs relative to your MCP client, then copy the matching
`mcp_config.json` below. Add the service-connection environment variables documented in the **Configuration** section.

| # | Option | Transport | Where it runs | `mcp_config.json` key |
|---|--------|-----------|---------------|------------------------|
| 1 | stdio | `stdio` | client launches a subprocess | `command` |
| 2 | Streamable-HTTP (local) | `streamable-http` | a local network port | `command` or `url` |
| 3 | Local container / uv | `stdio` or `streamable-http` | Docker / Podman / uv on this host | `command` or `url` |
| 4 | Remote URL | `streamable-http` | a remote host behind Caddy | `url` |

### 1. stdio (local subprocess)

The client launches the server over stdio via `uvx` — best for local IDEs
(Cursor, Claude Desktop, VS Code):

```json
{
  "mcpServers": {
    "archimate-mcp": {
      "command": "uvx",
      "args": ["--from", "archimate-mcp", "archimate-mcp"]
    }
  }
}
```

### 2. Streamable-HTTP (local process)

Run the server as a long-lived HTTP process:

```bash
uvx --from archimate-mcp archimate-mcp --transport streamable-http --host 0.0.0.0 --port 8000
curl -s http://localhost:8000/health        # {"status":"OK"}
```

Then either let the client launch it:

```json
{
  "mcpServers": {
    "archimate-mcp": {
      "command": "uvx",
      "args": ["--from", "archimate-mcp", "archimate-mcp", "--transport", "streamable-http", "--port", "8000"],
      "env": {
        "TRANSPORT": "streamable-http",
        "HOST": "0.0.0.0",
        "PORT": "8000"
      }
    }
  }
}
```

…or connect to the already-running process by URL:

```json
{
  "mcpServers": {
    "archimate-mcp": { "url": "http://localhost:8000/mcp" }
  }
}
```

### 3. Local container / uv

**(a) Launch a container directly from `mcp_config.json`** (stdio over the container —
no ports to manage). Swap `docker` for `podman` for a daemonless runtime:

```json
{
  "mcpServers": {
    "archimate-mcp": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "TRANSPORT=stdio",
        "knucklessg1/archimate-mcp:latest"
      ]
    }
  }
}
```

**(b) Run a local streamable-http container, then connect by URL:**

```bash
docker run -d --name archimate-mcp -p 8000:8000 \
  -e TRANSPORT=streamable-http \
  -e PORT=8000 \
  knucklessg1/archimate-mcp:latest
# or, from a clone of this repo:
docker compose -f docker/mcp.compose.yml up -d
```

```json
{
  "mcpServers": {
    "archimate-mcp": { "url": "http://localhost:8000/mcp" }
  }
}
```

**(c) From a local checkout with `uv`:**

```bash
uv run archimate-mcp --transport streamable-http --port 8000
```

### 4. Remote URL (deployed behind Caddy)

When the server is deployed remotely (e.g. as a Docker service) and published through
Caddy on the internal `*.arpa` zone, connect with the `"url"` key — no local process or
image required:

```json
{
  "mcpServers": {
    "archimate-mcp": { "url": "http://archimate-mcp.arpa/mcp" }
  }
}
```

Caddy reverse-proxies `http://archimate-mcp.arpa` to the container's `:8000`
streamable-http listener; `http://archimate-mcp.arpa/health` returns
`{"status":"OK"}` when the service is live.
<!-- END GENERATED: deployment-options -->

This page covers running `archimate-mcp` as a long-lived server: the transports, a
Docker Compose stack, the companion A2A agent server, putting it behind a Caddy
reverse proxy, and giving it a DNS name with Technitium.

> `archimate-mcp` ships **two** entry points: an **MCP server** (console script
> `archimate-mcp`) and an **A2A agent server** (console script `archimate-agent`).
> The MCP server is a typed, deterministic tool surface a policy router or agent
> calls; the agent server wraps that surface as a Pydantic-AI agent for
> graph-orchestrated workflows.

## Run the MCP server

The transport is selected with `--transport` (or the `TRANSPORT` env var):

=== "stdio (default)"

    ```bash
    archimate-mcp
    ```
    For IDE / desktop MCP clients that launch the server as a subprocess.

=== "streamable-http"

    ```bash
    archimate-mcp --transport streamable-http --host 0.0.0.0 --port 8000
    ```
    A network server with a `/health` endpoint and `/mcp` route.

=== "sse"

    ```bash
    archimate-mcp --transport sse --host 0.0.0.0 --port 8000
    ```

Health check (HTTP transports):

```bash
curl -s http://localhost:8000/health        # {"status":"OK"}
```

## Configuration (environment)

`archimate-mcp` is configured entirely from the environment. The **required** set:

| Var | Default | Meaning |
|---|---|---|
| `ARCHI_MODEL_PATH` | `./model.archimate` | Working model file (Open Exchange Format) |
| `ARCHITOOL` | `True` | Register the ArchiMate tool set |

Plus `HOST` / `PORT` / `TRANSPORT` for HTTP transports. Copy
[`.env.example`](https://github.com/Knuckles-Team/archimate-mcp/blob/main/.env.example)
to `.env` and adjust the values you need.

## Docker Compose

The repo ships [`docker/mcp.compose.yml`](https://github.com/Knuckles-Team/archimate-mcp/blob/main/docker/mcp.compose.yml).
A production stack reads a sibling `.env`, persists the model file on a volume, and
publishes the HTTP server on `:8000`:

```yaml
services:
  archimate-mcp:
    image: knucklessg1/archimate-mcp:latest
    container_name: archimate-mcp
    hostname: archimate-mcp
    restart: always
    env_file:
      - .env
    environment:
      - PYTHONUNBUFFERED=1
      - HOST=0.0.0.0
      - PORT=8000
      - TRANSPORT=streamable-http
      - ARCHI_MODEL_PATH=/data/model.archimate
    volumes:
      - archimate_data:/data
    ports:
      - "8000:8000"
    healthcheck:
      test: ["CMD", "python3", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  archimate_data:
```

```bash
cp .env.example .env          # then edit ARCHI_MODEL_PATH if needed
docker compose -f docker/mcp.compose.yml up -d
docker compose -f docker/mcp.compose.yml logs -f
```

## A2A agent server

The companion agent server (console script `archimate-agent`) wraps the same tool
surface as a Pydantic-AI agent. It connects to a running MCP server via `MCP_URL`
and exposes the agent capabilities declared in
[`a2a.json`](https://github.com/Knuckles-Team/archimate-mcp/blob/main/a2a.json).

```bash
# Point the agent at the MCP server and serve it on :8001
export MCP_URL=http://archimate-mcp:8000/mcp
archimate-agent --host 0.0.0.0 --port 8001
```

A combined stack from
[`docker/agent.compose.yml`](https://github.com/Knuckles-Team/archimate-mcp/blob/main/docker/agent.compose.yml)
runs the MCP server and wires the agent to it by container name:

```yaml
services:
  archimate-mcp:
    image: knucklessg1/archimate-mcp:latest
    hostname: archimate-mcp
    environment:
      - TRANSPORT=streamable-http
      - HOST=0.0.0.0
      - PORT=8000
      - ARCHI_MODEL_PATH=/data/model.archimate
    volumes:
      - archimate_data:/data
    ports:
      - "8000:8000"

  archimate-agent:
    image: knucklessg1/archimate-mcp:latest
    command: ["archimate-agent", "--host", "0.0.0.0", "--port", "8001"]
    depends_on: [archimate-mcp]
    environment:
      - MCP_URL=http://archimate-mcp:8000/mcp
      - HOST=0.0.0.0
      - PORT=8001
    ports:
      - "8001:8001"

volumes:
  archimate_data:
```

```bash
docker compose -f docker/agent.compose.yml up -d
```

## Behind a Caddy reverse proxy

Expose the HTTP server on a hostname with automatic TLS. Add to your `Caddyfile`:

```caddy
# Internal (self-signed) — homelab .arpa zone
archimate-mcp.arpa {
    tls internal
    reverse_proxy archimate-mcp:8000
}
```

```caddy
# Public — automatic Let's Encrypt
archimate-mcp.example.com {
    reverse_proxy archimate-mcp:8000
}
```

Reload Caddy:

```bash
docker compose -f services/caddy/compose.yml exec caddy caddy reload --config /etc/caddy/Caddyfile
```

## DNS with Technitium

Point the hostname at the host running Caddy. Via the Technitium API:

```bash
curl -s "http://technitium.arpa:5380/api/zones/records/add" \
  --data-urlencode "token=$TECHNITIUM_DNS_TOKEN" \
  --data-urlencode "domain=archimate-mcp.arpa" \
  --data-urlencode "zone=arpa" \
  --data-urlencode "type=A" \
  --data-urlencode "ipAddress=10.0.0.10" \
  --data-urlencode "ttl=3600"
```

…or add an **A record** `archimate-mcp.arpa → <caddy-host-ip>` in the Technitium web
console (`http://technitium.arpa:5380`). The ecosystem
[`technitium-dns-mcp`](https://knuckles-team.github.io/technitium-dns-mcp/) automates
this as a tool.

## Register with an MCP client

Add to your client's `mcp_config.json` (multiplexer nickname `archi`):

```json
{
  "mcpServers": {
    "archimate-mcp": {
      "command": "uv",
      "args": ["run", "archimate-mcp"],
      "env": {
        "ARCHI_MODEL_PATH": "./model.archimate",
        "ARCHITOOL": "True"
      }
    }
  }
}
```

For a remote HTTP server, point the client at `http://archimate-mcp.arpa/mcp` instead.
