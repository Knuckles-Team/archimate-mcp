# Usage — API / CLI / MCP

`archimate-mcp` exposes the same capability three ways: as **MCP tools** an agent
calls, as a **Python API** (`ArchiApi`) you import, and as **CLI** entry points. The
complete tool surface is summarized in [Overview](overview.md).

## As an MCP server

Once [deployed](deployment.md), the server registers six action-dispatch tools that
span the entire ArchiMate authoring surface:

| Tool | Actions |
|---|---|
| `archi_model` | Model lifecycle — `new` / `load` / `save` / `export_exchange` / `import_exchange` / `summary` |
| `archi_element` | Element CRUD — `add` / `get` / `update` / `delete` / `list` / `find` |
| `archi_relationship` | Relationship CRUD + validation — `add` / `get` / `update` / `delete` / `list` / `validate` |
| `archi_view` | Views (diagrams) — `create` / `add_element` / `add_connection` / `list` / `get` |
| `archi_folder` | Organizations (folders) — `add` / `move` / `list` |
| `archi_query` | Query / traversal — `neighbors` / `relationships_of` / `by_type` + vocabulary |

Example agent prompts that map onto these tools:

- *"Create a new model and add a Business Actor named 'Customer'"* → `archi_model`, `archi_element`
- *"List every Application Component in the model"* → `archi_query`
- *"Connect 'Order Service' to 'Payment Service' with a Serving relationship, then validate it"* → `archi_relationship`
- *"Export the model to Open Exchange Format so it opens in Archi"* → `archi_model`

## As a Python API

`ArchiApi` is a stateful façade over a single ArchiMate model file. It drives a
local engine — no external server is required.

```python
from archimate_mcp.api.api_client_archi import ArchiApi

api = ArchiApi(model_path="./model.archimate")

# Model lifecycle
api.new_model(name="Reference Architecture")

# Author elements and relationships
customer = api.add_element("BusinessActor", "Customer")
order = api.add_element("ApplicationComponent", "Order Service")
rel = api.add_relationship("Serving", customer["id"], order["id"])

# Query / traversal (read calls)
summary = api.model_summary()
components = api.elements_by_type("ApplicationComponent")
neighbors = api.neighbors(customer["id"])
edges = api.relationships_of(order["id"])

# Validate a candidate relationship
verdict = api.validate_relationship("Serving", customer["id"], order["id"])
```

Author a diagram and round-trip the Open Exchange Format so the model opens in Archi:

```python
view = api.create_view("Context View")
api.add_element_to_view(view, customer["id"])
api.add_element_to_view(view, order["id"])
api.add_connection_to_view(view, rel["id"])

api.export_open_exchange("./reference-architecture.archimate")
```

Build a client straight from the environment:

```python
from archimate_mcp.auth import get_client
api = get_client()        # reads ARCHI_MODEL_PATH from the environment / .env
```

## As a CLI

The package installs two console scripts:

```bash
# MCP server (stdio by default; --transport for HTTP/SSE)
archimate-mcp --transport streamable-http --host 0.0.0.0 --port 8000

# A2A agent server — connects to a running MCP server via MCP_URL
MCP_URL=http://localhost:8000/mcp archimate-agent --host 0.0.0.0 --port 8001
```

The agent capabilities advertised over A2A are declared in
[`a2a.json`](https://github.com/Knuckles-Team/archimate-mcp/blob/main/a2a.json). See
[Deployment](deployment.md#a2a-agent-server) for wiring the agent to the MCP server.
