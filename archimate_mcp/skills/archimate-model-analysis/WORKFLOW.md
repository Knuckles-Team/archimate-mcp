# Archimate Model Analysis

Query, traverse, and validate an ArchiMate 3.x model through the archimate-mcp MCP server — list elements by type/layer, find by name, walk neighbors and relationships of an element, introspect the element/relationship vocabulary, and check whether a relationship is structurally valid. Also imports/exports the Open Group Model Exchange file. Use when the agent must understand or audit an existing model. Do NOT use to create or edit model content (use archimate-model-authoring) or to push the model into the knowledge graph (use archimate-kg-ingestion).

# ArchiMate Model Analysis

Read-only interrogation of an ArchiMate 3.x model held by the **archimate-mcp**
engine: filtering, name search, graph traversal, vocabulary introspection, and
relationship validation.

## When to use
- Inventory a model: list elements by `type` or `layer`, find by name substring.
- Traverse: get an element's `neighbors` or all `relationships_of` it.
- Audit: check whether a `type` is valid between two element types before authoring.
- Load an `.archimate` file to inspect, or export the current model.

## When NOT to use
- Creating/editing elements, relationships, folders, or views →
  `archimate-model-authoring`.
- Mirroring the model into the epistemic-graph knowledge graph →
  `archimate-kg-ingestion`.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`archimate-mcp`** MCP server.

| Variable | Required | Notes |
|----------|----------|-------|
| `ARCHI_MODEL_PATH` | optional | Model file the engine auto-loads (default `./model.archimate`). |
| `MCP_TOOL_MODE` | optional | `condensed` (default) \| `verbose` \| `both`. |

## Tools & actions
Prefer the **condensed** tools; each takes `action` + a `params_json` **JSON string**.

| Tool | Actions |
|------|---------|
| `archi_query` | `neighbors`, `relationships_of`, `by_type`, `element_types`, `relationship_types` |
| `archi_element` | `list` (filter by `type`/`layer`), `get`, `find` (by `name_substring`) |
| `archi_relationship` | `list` (filter by `type`/`source`/`target`), `get`, `validate` |
| `archi_model` | `summary`, `load`, `export_exchange` |

### Key parameters
- `archi_query neighbors` / `relationships_of`: `element_id`.
- `archi_element list`: `type` and/or `layer` (Business, Application, Technology,
  Strategy, Physical, Motivation, Implementation, Other).
- `archi_relationship validate`: `type`, `source_type`, `target_type`.

## Recipes (`params_json`)
List all Application-layer elements:
```json
{"layer":"Application"}
```
Find an element by name, then walk its neighbors:
```json
{"name_substring":"billing"}
```
```json
{"element_id":"elem-<id>"}
```
Check a relationship is structurally valid before authoring it:
```json
{"type":"Realization","source_type":"ApplicationComponent","target_type":"ApplicationService"}
```
Model counts at a glance:
```json
{}
```

## Gotchas
- `params_json` is a **string** of JSON, not an object — serialize it.
- `layer` values are the eight ArchiMate layers exactly (case-sensitive); an
  unknown layer simply returns no matches.
- `neighbors` only returns the far-end **element** of each relationship (with the
  connecting relationship id/type under `via`); use `relationships_of` for the raw
  relationship records including dangling ones.
- `validate` encodes common structural rules and defaults to allowing pairs it does
  not explicitly constrain (and always allows `Association`) — treat a `true` as
  "plausible", not "fully ArchiMate-derivation-checked".

## Related
- **Author / edit** the model → `archimate-model-authoring`.
- **Ingest** the model into the KG as typed nodes → `archimate-kg-ingestion`.
