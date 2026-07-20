# Archimate Kg Ingestion

Natively mirror an ArchiMate 3.x model into the epistemic-graph knowledge graph via the archimate-mcp MCP server — every element becomes a typed OWL node (:ArchimateElement subclass such as :ApplicationComponent / :BusinessProcess / :Node), every relationship a reified :ArchimateRelationship node plus a direct edge, and every view an :ArchimateView node, all under one :ArchimateModel. Use when the agent must make an architecture model queryable in the KG alongside the rest of the enterprise. Do NOT use to create/edit the model (use archimate-model-authoring) or to read it locally (use archimate-model-analysis).

# ArchiMate Knowledge-Graph Ingestion

Push an ArchiMate model into the ONE epistemic-graph knowledge graph as **typed OWL
nodes + edges**, so architecture facts join the rest of the enterprise graph and
resolve through the shared `[configured-endpoint]` ontology.

## When to use
- Make the current (or a freshly loaded) ArchiMate model queryable in the KG.
- Refresh the KG after authoring/editing a model.
- Give downstream agents typed access to `:ApplicationComponent`,
  `:BusinessProcess`, `:ArchimateRelationship`, `:ArchimateView`, etc.

## When NOT to use
- Building or editing the model itself → `archimate-model-authoring`.
- Local read-only inspection that does not need the KG → `archimate-model-analysis`.

## Prerequisites & environment
Connect via the `mcp-client` skill against the **`archimate-mcp`** MCP server, with a
reachable epistemic-graph engine (graph-os). Ingestion is authoritative: engine,
validation, and transaction failures are surfaced explicitly.

| Variable | Required | Notes |
|----------|----------|-------|
| `ARCHI_MODEL_PATH` | optional | Model file the engine loads (default `./model.archimate`). |
| `ARCHI_KG_INGEST` | optional | Default-on. Set `0`/`false` to disable the automatic ingest that fires on every `load`/`import_exchange`. |

## Tools & actions
| Tool | Purpose |
|------|---------|
| `archimate_ingest_model` | List the model's elements/relationships/views and push them into the KG as typed nodes + edges. |
| `archi_model` (`load`/`import_exchange`) | Loading a model **auto-ingests** it (unless `ARCHI_KG_INGEST=0`). |

### What gets written
- `:ArchimateModel` — one node per model (id `archimate:model:<id>`).
- Element nodes typed by ArchiMate concept (`:ApplicationComponent`, `:Node`, …),
  id `archimate:<type>:<elementId>`, carrying `archimateType` + `archimateLayer`,
  linked from the model by `hasElement`.
- `:ArchimateRelationship` nodes (id `archimate:relationship:<relId>`) **and** a
  direct element→element edge carrying the ArchiMate relationship type.
- `:ArchimateView` nodes linked by `hasView`, with `depictsElement` edges.
- `:Document` nodes carrying element/view documentation for semantic search.

## Recipes (`params_json`)
Ingest the currently loaded model:
```json
{}
```
Load a specific file, then ingest it:
```json
{"path":"./model.archimate"}
```

## Gotchas
- `params_json` is a **string** of JSON, not an object — serialize it.
- Ingestion is idempotent (nodes MERGE by id); re-running after edits refreshes,
  it does not duplicate.
- A `load`/`import_exchange` already auto-ingests, so calling `archimate_ingest_model`
  right after is redundant (harmless) — set `ARCHI_KG_INGEST=0` to author without
  touching the KG.
- Node `type` values match the classes federated by `archimate_mcp.ontology`
  (`archimate.ttl`); the same names resolve across every ingested model.
- A missing engine or failed transaction is reported as an ingestion error; it is
  never acknowledged as a successful write.

## Related
- **Author** the model first → `archimate-model-authoring`.
- **Analyze** it locally → `archimate-model-analysis`.
- Mapper/primitive lives in `archimate_mcp/kg_ingest.py`
  (`ingest_from_api` / `build_model_graph`).
