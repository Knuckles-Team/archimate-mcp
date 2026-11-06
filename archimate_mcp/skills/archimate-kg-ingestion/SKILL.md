---
name: archimate-kg-ingestion
skill_type: skill
description: >-
  Natively mirror an ArchiMate 3.x model into the epistemic-graph knowledge graph
  via the archimate-mcp MCP server — every element becomes a typed OWL node
  (:ArchimateElement subclass such as :ApplicationComponent / :BusinessProcess /
  :Node), every relationship a reified :ArchimateRelationship node plus a direct
  edge, and every view an :ArchimateView node, all under one :ArchimateModel. Use
  when the agent must make an architecture model queryable in the KG alongside the
  rest of the enterprise. Do NOT use to create/edit the model (use
  archimate-model-authoring) or to read it locally (use archimate-model-analysis).
license: MIT
tags: [archimate, knowledge-graph, ingestion, owl, mcp]
metadata:
  author: Knuckles-Team
  version: '0.1.0'
---

# Archimate Kg Ingestion

Every step below is one typed tool call; there is no `action` or JSON-string argument. Resolve ids by name first, read before you change, and ask for approval before anything destructive.

## Mirror model to graph

Land the model's elements, relationships and views in the knowledge graph.

1. `archimate_ingest_model` (path)
2. `archimate_ingest_to_kg`
3. `archimate_model_summary`

## Guardrails

- Never print tokens, passwords or webhook secrets.
- Public or destructive actions need the requester's confirmation of the target and text.
- Report ids (and refusal codes) for every call.
