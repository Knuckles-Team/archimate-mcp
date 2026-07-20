# Deployment

<!-- BEGIN GENERATED: deployment-options -->
## Deployment Options

`archimate-mcp` supports local stdio, a loopback-only development listener, a
least-privilege stdio container, and a remote authenticated HTTPS boundary.
Provider endpoint, credential, selector, identity, and trust material are supplied
at runtime through `AgentConfig`; none is stored in this repository.

### Installed stdio process

```json
{
  "mcpServers": {
    "archimate": {
      "command": "archimate-mcp",
      "args": [],
      "env": {"MCP_TOOL_MODE": "intent"}
    }
  }
}
```

### Loopback development listener

```bash
archimate-mcp --transport streamable-http --host 127.0.0.1 --port 8000
```

Do not expose this listener beyond loopback. Network deployments require direct TLS
or an explicitly trusted TLS-terminating ingress, configured authentication, exact
`MCP_ALLOWED_HOSTS`, and an exact trusted-proxy CIDR policy.

### Least-privilege local container

```bash
docker run -i --rm \
  --read-only \
  --cap-drop=ALL \
  --security-opt=no-new-privileges \
  --pids-limit=256 \
  --tmpfs /tmp:rw,noexec,nosuid,nodev,size=64m \
  -e TRANSPORT=stdio \
  registry.example.invalid/archimate-mcp@sha256:<digest> archimate-mcp
```

The operator projects the selected AgentConfig profile into the process at runtime;
the image remains immutable and contains no environment connection profile.

### Remote authenticated HTTPS endpoint

```json
{
  "mcpServers": {
    "archimate": {"url": "https://service.example.invalid/mcp"}
  }
}
```

Store the real remote URL, outbound identity reference, and TLS-profile reference in
`AgentConfig`, not in MCP client JSON or documentation.
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
| `ARCHI_KG_INGEST` | `1` | Ingest loaded/imported models through the governed ChangeEnvelope path |
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
    image: example/archimate-mcp@sha256:<digest>
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
    image: example/archimate-mcp@sha256:<digest>
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
    image: example/archimate-mcp@sha256:<digest>
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
# Internal (self-signed) — homelab .example.invalid zone
archimate-mcp.example.invalid {
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
curl -s "http://technitium.example.invalid:5380/api/zones/records/add" \
  --data-urlencode "token=$TECHNITIUM_DNS_TOKEN" \
  --data-urlencode "domain=archimate-mcp.example.invalid" \
  --data-urlencode "zone=arpa" \
  --data-urlencode "type=A" \
  --data-urlencode "ipAddress=192.0.2.10" \
  --data-urlencode "ttl=3600"
```

…or add an **A record** `archimate-mcp.example.invalid → <caddy-host-ip>` in the Technitium web
console (`http://technitium.example.invalid:5380`). The ecosystem
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
        "ARCHI_KG_INGEST": "1",
        "ARCHITOOL": "True"
      }
    }
  }
}
```

For a remote HTTP server, point the client at `http://archimate-mcp.example.invalid/mcp` instead.
