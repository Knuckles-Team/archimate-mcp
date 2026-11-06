---
name: archimate-model-analysis
skill_type: skill
description: >-
  Query, traverse, and validate an ArchiMate 3.x model through the archimate-mcp
  MCP server — list elements by type/layer, find by name, walk neighbors and
  relationships of an element, introspect the element/relationship vocabulary, and
  check whether a relationship is structurally valid. Also imports/exports the Open
  Group Model Exchange file. Use when the agent must understand or audit an existing
  model. Do NOT use to create or edit model content (use archimate-model-authoring)
  or to push the model into the knowledge graph (use archimate-kg-ingestion).
license: MIT
tags: [archimate, enterprise-architecture, analysis, traversal, mcp]
metadata:
  author: Knuckles-Team
  version: '0.1.0'
---

# Archimate Model Analysis

Every step below is one typed tool call; there is no `action` or JSON-string argument. Resolve ids by name first, read before you change, and ask for approval before anything destructive.

## Inspect model

Read the loaded model: its size, the ArchiMate vocabulary, folders and views.

1. `archimate_model_summary`
2. `archimate_element_types`
3. `archimate_relationship_types`
4. `archimate_list_folders`
5. `archimate_list_views`

## Model elements

Add, change, find and remove typed ArchiMate elements.

1. `archimate_element_types`
2. `archimate_add_element` (type, name, documentation, properties)
3. `archimate_get_element` (element_id)
4. `archimate_update_element` (element_id, name, documentation, properties, type)
5. `archimate_find_elements` (name_substring)
6. `archimate_list_elements` (type, layer)
7. `archimate_elements_by_type` (type)
8. `archimate_delete_element` (element_id, cascade, confirm)

## Analyze dependencies

Walk an element's neighbours and relationships to answer impact questions.

1. `archimate_find_elements` (name_substring)
2. `archimate_get_element` (element_id)
3. `archimate_neighbors` (element_id)
4. `archimate_relationships_of` (element_id)
5. `archimate_list_relationships` (type, source, target)

## Guardrails

- Never print tokens, passwords or webhook secrets.
- Public or destructive actions need the requester's confirmation of the target and text.
- Report ids (and refusal codes) for every call.
