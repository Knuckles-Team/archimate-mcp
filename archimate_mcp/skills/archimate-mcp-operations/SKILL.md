---
name: archimate-mcp-operations
skill_type: skill
description: >-
  Operate archimate-mcp through its governed MCP and Arbora capabilities, including archimate kg ingestion, archimate model analysis, archimate model authoring. Use when a request requires this provider's read, change, automation, ingestion, troubleshooting, or evidence workflows.
---

# Archimate Mcp Operations

Every step below is one typed tool call; there is no `action` or JSON-string argument. Resolve ids by name first, read before you change, and ask for approval before anything destructive.

## Inspect model

Read the loaded model: its size, the ArchiMate vocabulary, folders and views.

1. `archimate_model_summary`
2. `archimate_element_types`
3. `archimate_relationship_types`
4. `archimate_list_folders`
5. `archimate_list_views`

## Guardrails

- Never print tokens, passwords or webhook secrets.
- Public or destructive actions need the requester's confirmation of the target and text.
- Report ids (and refusal codes) for every call.
