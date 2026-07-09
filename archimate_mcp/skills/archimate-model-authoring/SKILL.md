---
name: archimate-model-authoring
skill_type: skill
description: >-
  Author ArchiMate 3.x enterprise-architecture models with the archimate-mcp MCP
  server — create the model, add typed elements (ApplicationComponent,
  BusinessProcess, Node, …), wire valid relationships (Serving, Realization,
  Assignment, …), organize folders, and lay out views (diagrams). Use when the
  agent must build or edit an ArchiMate model and export it as an Open Group Model
  Exchange file that opens directly in Archi. Do NOT use for read-only
  querying/traversal (use archimate-model-analysis) or for pushing a model into the
  knowledge graph (use archimate-kg-ingestion).
license: MIT
tags: [archimate, enterprise-architecture, modeling, mcp, open-exchange]
metadata:
  author: Genius
  version: '0.1.0'
---
# ArchiMate Model Authoring

Drive the self-contained ArchiMate 3.x model engine in **archimate-mcp** to author
models programmatically. The engine round-trips through the Open Group **Model
Exchange File Format**, so anything you build opens directly in Archi.

## When to use
- Stand up a new model, then add elements, relationships, folders, and views.
- Edit an existing `.archimate` model (rename, re-document, add properties).
- Produce a shareable Open Exchange file for hand-off to Archi.

## When NOT to use
- Read-only queries, neighbor traversal, or vocabulary introspection →
  `archimate-model-analysis`.
- Mirroring the model into the epistemic-graph knowledge graph →
  `archimate-kg-ingestion`.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`archimate-mcp`** MCP server.

| Variable | Required | Notes |
|----------|----------|-------|
| `ARCHI_MODEL_PATH` | optional | Path of the model file the engine loads/saves (default `./model.archimate`). Mutations auto-save here. |
| `MCP_TOOL_MODE` | optional | `condensed` (default) \| `verbose` \| `both`. |

There is no remote server or credentials — the model engine is local.

## Tools & actions
Prefer the **condensed** tools; each takes `action` + a `params_json` **JSON string**.

| Tool | Actions |
|------|---------|
| `archi_model` | `new`, `load`, `save`, `export_exchange`, `import_exchange`, `summary` |
| `archi_element` | `add`, `get`, `update`, `delete`, `list`, `find` |
| `archi_relationship` | `add`, `get`, `update`, `delete`, `list`, `validate` |
| `archi_folder` | `add`, `move`, `list` |
| `archi_view` | `create`, `add_element`, `add_connection`, `list`, `get` |

### Key parameters
- `archi_element add`: `type` (an ArchiMate element type — see
  `archi_query/element_types`), `name`, `documentation`, `properties`.
- `archi_relationship add`: `type`, `source` (element id), `target` (element id),
  optional `validate` (default `true`).
- `archi_view add_element`: `view_id`, `element_id`, `x`, `y`, `w`, `h`.

## Recipes (`params_json`)
Create a model, then an application component:
```json
{"name":"Payments Platform","documentation":"Target-state architecture"}
```
```json
{"type":"ApplicationComponent","name":"Billing Service","documentation":"Issues invoices"}
```
Wire a Serving relationship (ids returned by the two `add` calls):
```json
{"type":"Serving","source":"elem-<billing>","target":"elem-<portal>"}
```
Lay it out on a view:
```json
{"name":"Application Cooperation"}
```
```json
{"view_id":"view-<id>","element_id":"elem-<billing>","x":40,"y":40,"w":140,"h":60}
```
Export an Open Exchange file for Archi:
```json
{"path":"/tmp/payments.archimate"}
```

## Gotchas
- `params_json` is a **string** of JSON, not an object — serialize it.
- Element/relationship `type` must be a known ArchiMate type; unknown types raise.
  List the vocabulary with `archi_query` `element_types` / `relationship_types`.
- Relationship `add` validates endpoints by default; pass `"validate": false` to
  force an unusual pairing. `Association` is always allowed.
- `add_connection` binds a relationship onto a view only if **both** endpoint
  elements are already placed on that view — add the element nodes first.
- Every mutation auto-saves to `ARCHI_MODEL_PATH`; set it before authoring if you
  want a specific output file.

## Related
- **Analyze / traverse** the authored model → `archimate-model-analysis`.
- **Ingest** the model into the KG as typed nodes → `archimate-kg-ingestion`.
