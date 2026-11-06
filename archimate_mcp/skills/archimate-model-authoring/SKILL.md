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
  author: Knuckles-Team
  version: '0.1.0'
---

# Archimate Model Authoring

Every step below is one typed tool call; there is no `action` or JSON-string argument. Resolve ids by name first, read before you change, and ask for approval before anything destructive.

## Start model

Start a new model, or load or import an existing one.

1. `archimate_new_model` (name, documentation)
2. `archimate_load` (path)
3. `archimate_import_open_exchange` (path)
4. `archimate_model_summary`

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

## Relate elements

Validate and add relationships between elements, and change or remove them.

1. `archimate_validate_relationship` (type, source_type, target_type)
2. `archimate_relationship_types`
3. `archimate_add_relationship` (type, source, target, name, documentation, properties, validate)
4. `archimate_get_relationship` (relationship_id)
5. `archimate_update_relationship` (relationship_id, name, documentation, properties)
6. `archimate_list_relationships` (type, source, target)
7. `archimate_delete_relationship` (relationship_id, confirm)

## Organize folders

Create folders and place elements in them.

1. `archimate_add_folder` (name, type)
2. `archimate_list_folders`
3. `archimate_move_to_folder` (folder_id, element_id)

## Draw view

Create a view and place elements and connections on it.

1. `archimate_create_view` (name, documentation)
2. `archimate_add_element_to_view` (view_id, element_id, x, y, w, h)
3. `archimate_add_connection_to_view` (view_id, relationship_id)
4. `archimate_get_view` (view_id)
5. `archimate_list_views`

## Save and export

Save the model and export an Open Group Model Exchange file Archi opens.

1. `archimate_save` (path)
2. `archimate_export_open_exchange` (path)
3. `archimate_model_summary`

## Guardrails

- Never print tokens, passwords or webhook secrets.
- Public or destructive actions need the requester's confirmation of the target and text.
- Report ids (and refusal codes) for every call.
