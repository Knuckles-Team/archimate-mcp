---
name: archimate-mcp-development
skill_type: skill
description: >-
  Develop, test, package, and release the archimate-mcp connector. Use this skill
  when changing the ArchiMate model engine, MCP tools, ontology content, packaged
  workflows, documentation, or repository delivery gates.
domain: development
license: MIT
tags: [archimate, enterprise-architecture, mcp, connector, sdk, development, delivery]
metadata:
  author: Repository Maintainers
  version: '0.1.0'
---

# archimate-mcp development

`archimate-mcp` is a connector for a local ArchiMate 3.x model engine. It exposes
model authoring, querying, Open Group Model Exchange import/export, and optional
epistemic-graph ingestion through the Agent Connector SDK. Keep model semantics,
XML handling, MCP tools, ontology assets, and connector source declarations in
this repository. Admission, transport, and durable graph storage belong to the
SDK and platform owners.

## Repository map and real entry points

- `archimate_mcp/__init__.py` declares the SDK `Connector`, binds the `Api`
  facade and `get_client`, and registers `archimate_mcp.mcp.mcp_archi`.
- `archimate_mcp/api_client.py` is the public facade. The model implementation is
  in `archimate_mcp/api/api_client_archi.py` and
  `archimate_mcp/api/archimate_model.py`; XML parsing and safety checks are in
  `archimate_mcp/api/xml_security.py`.
- `archimate_mcp/mcp/mcp_archi.py` registers the real tools: `archi_model`,
  `archi_element`, `archi_relationship`, `archi_view`, `archi_folder`,
  `archi_query`, and `archimate_ingest_model`.
- `archimate_mcp/auth.py` constructs the local `Api` from `ARCHI_MODEL_PATH`
  (default `./model.archimate`). There is no remote provider login in this
  connector; do not add credentials or endpoint claims to its content.
- `archimate_mcp/connector_sources.py` declares live source presets and mappings.
  `archimate_mcp/ontology/` contains `archimate.ttl`, source mappings, and the
  migration manifest. `archimate_mcp/prompts/` contains the packaged prompt.
- `archimate_mcp/skills/` contains the operation, analysis, authoring, ingestion,
  and development skills. `docs/` is the MkDocs source and `tests/` contains
  startup, publication, model, XML-security, and ingestion checks.
- `pyproject.toml` declares the single console script
  `archimate-mcp = agent_connector_sdk.cli:serve` and the SDK connector entry
  point `archimate-mcp = archimate_mcp:connector`. Do not document an absent
  second console script.

## Route and inspect before editing

1. Read `AGENTS.md` and locate the owning `CONN-ARCHIMATE-MCP-*` row with
   `git grep -n "<term>" -- specs` before changing behavior.
2. Reuse the SDK Connector, configuration, transport, and tool registration
   helpers. Do not add a parallel MCP server, authentication path, or agent
   runtime entry point.
3. Keep ArchiMate behavior in `archimate_mcp/api/`, thin MCP adapters in
   `archimate_mcp/mcp/mcp_archi.py`, XML safety in `xml_security.py`, and source
   declarations in `connector_sources.py`.
4. Preserve the model persistence boundary: mutating tools save through the
   existing `Api` client, and `ARCHI_MODEL_PATH` remains runtime configuration.

## Rapid delivery: the 5-minute contract

Specs are already designed. Deliver one small, reviewable slice and tie every
claim to a real path and command.

**Extend first**

- Find the owning requirement before changing behavior and cite its ID in the
  commit `Spec:` trailer. Never hand-edit generated `specs/*/status.json`.
- Bind behavior to an existing focused test or add a focused credential-free,
  network-free test under `tests/` with the literal spec marker.
- Keep one implementation of each capability. Use the SDK client and existing
  XML parser rather than ad-hoc HTTP, authentication, or deserialization.

**Five-minute delivery**

- Work from an immutable `origin/main` commit in a private worktree. Do not use
  `git stash`, force-push, broad staging, live provider calls, or native builds.
- Run the smallest relevant checks first, then the configured commit and push
  gates. A missing dependency or skipped check is an evidence gap.
- When packaged skill or package metadata changes, advance the patch version with
  the repository's version tool and refresh `uv.lock` in the same change.
- Put `Spec:` and `Co-Authored-By:` on consecutive lines in the final paragraph
  of each commit message so the shared trailer gate can read both.

## Development and verification commands

Use the committed lockfile and supported Python range:

```bash
uv sync --locked
uv run archimate-mcp --help
uv run pytest -q tests/test_init_dynamics.py tests/test_publication_workflow.py
uv run pytest -q tests/test_xml_security.py tests/test_kg_ingest.py
uv run ruff check archimate_mcp tests
uvx pre-commit run --all-files
uv run mkdocs build --strict
```

The focused tests cover connector initialization, the canonical Pages and
publication workflows, XML security, and model ingestion. Keep checks local and
credential-free; hosted release and Pages workflows own publication evidence.

## Pages and runtime delivery

The canonical Pages caller is `.github/workflows/pages.yml`; it invokes
`Knuckles-Team/pipelines/.github/workflows/pages_pipeline.yml@main` with
`content_source: docs`, `spec_dashboard_enabled: true`, and
`.github/spec-dashboard.json`. Its push paths include docs, specs, the dashboard
config, and the caller. Keep this as the only public Pages publisher;
`.github/workflows/docs.yml` remains a documentation validation job.

The committed `docker/compose.yml` currently describes one legacy `agent` build
service with non-root, read-only, capability-drop, no-new-privileges, process,
CPU, memory, and tmpfs limits. The pinned source has no tracked
`docker/Dockerfile` or `docker/mcp.compose.yml`; existing deployment prose that
mentions those files or an agent console script is stale until a separate owner
reconciles it. Do not claim those absent files or services are part of the live
runtime.

The central Pipelines renderer owns generated connector Docker and MCP Compose
files. Generated files are not committed. Before changing deployment metadata,
render the exact source tree and compare the generated single `archimate-mcp-mcp`
service with the SDK entry point, `ARCHI_MODEL_PATH` behavior, loopback/port
defaults, authentication boundary, and model-state handling. Do not add a state
volume or replace the existing model semantics without an owning requirement.

After a merge, prove the Pages workflow used the exact main SHA and fetch `/`,
`/spec-delivery/`, `/spec-delivery/index.html`, and
`/spec-delivery/snapshot.json` with HTTP 200. Record the snapshot revision and
the hosted run URL; do not infer publication from workflow markers alone.
