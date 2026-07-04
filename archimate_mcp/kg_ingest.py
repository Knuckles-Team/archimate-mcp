"""Native epistemic-graph ingestion for ArchiMate models (typed OWL nodes).

CONCEPT:AU-KG.ingest.enterprise-source-extractor. The archimate-mcp package natively
pushes an ArchiMate model into the ONE epistemic-graph knowledge graph as **typed OWL
nodes** — every element becomes an ``:ArchimateElement`` subclass node (``:ApplicationComponent``,
``:BusinessProcess``, ``:Node``, …), every relationship a reified ``:ArchimateRelationship``
node **and** a direct LPG edge between its endpoints, and every view an ``:ArchimateView``
node. The classes match those federated by :mod:`archimate_mcp.ontology`.

Two write paths, resolved at call time:

* Preferred — the shared fleet primitive
  ``agent_utilities.knowledge_graph.memory.native_ingest`` (the ONE txn write path).
* Fallback — a self-contained txn dance over ``GraphComputeEngine()._client`` (the
  primitive is not yet in every installed ``agent_utilities``).

Everything is dependency-/engine-guarded: with no KG stack or no reachable engine every
entry point **no-ops** (returns ``None``), so the connector runs with zero KG
infrastructure. Node ids follow ``archimate:<class>:<extId>``.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger("archimate_mcp.kg")

_SOURCE = "archimate-mcp"
_DOMAIN = "archimate"
_DEFAULT_GRAPH = "__commons__"


# --------------------------------------------------------------------------- #
# Engine client resolution + write paths (shared-primitive-first, fallback)
# --------------------------------------------------------------------------- #
def _layer_of(elem_type: str) -> str | None:
    """Return the ArchiMate layer of ``elem_type`` (best-effort, import-guarded)."""
    try:
        from archimate_mcp.api.archimate_model import LAYER_OF_TYPE

        return LAYER_OF_TYPE.get(elem_type)
    except Exception:  # noqa: BLE001 — vocabulary import optional
        return None


def _client() -> tuple[Any | None, str]:
    """Return ``(engine_client, graph_name)`` or ``(None, "")`` when unavailable."""
    try:
        from agent_utilities.knowledge_graph.core.graph_compute import (
            GraphComputeEngine,
        )
    except Exception as e:  # noqa: BLE001 — KG stack absent
        logger.debug("KG ingest unavailable (import): %s", e)
        return None, ""
    try:
        engine = GraphComputeEngine()
        client = getattr(engine, "_client", None)
        if client is None:
            return None, ""
        return client, (getattr(engine, "graph_name", None) or _DEFAULT_GRAPH)
    except Exception as e:  # noqa: BLE001 — engine unreachable
        logger.debug("KG ingest: engine unreachable: %s", e)
        return None, ""


def _fallback_write(
    nodes: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None,
    *,
    client: Any,
    graph: str,
) -> dict[str, int] | None:
    """Self-contained txn write used when the shared primitive is unavailable."""
    nodes = [n for n in nodes if n.get("id")]
    if not nodes:
        return None
    try:
        txn = client.txn.begin(graph=graph)
        for node in nodes:
            props = {k: v for k, v in node.items() if k != "id" and v is not None}
            props.setdefault("source", _SOURCE)
            props.setdefault("domain", _DOMAIN)
            client.txn.add_node(txn, node["id"], props)
        committed = client.txn.commit(txn)
    except Exception as e:  # noqa: BLE001 — engine/txn failure is non-fatal
        logger.warning("KG ingest: txn failed: %s", e)
        return None
    if not committed:
        logger.warning("KG ingest: txn not committed (conflict)")
        return None

    edges = 0
    for rel in relationships or []:
        try:
            client.edges.add(
                rel["source"],
                rel["target"],
                {"type": rel.get("type", "RELATED")},
            )
            edges += 1
        except Exception as e:  # noqa: BLE001 — pure edge link, best-effort
            logger.debug("KG ingest: edge skipped: %s", e)

    logger.info("KG ingest: wrote %d nodes, %d edges", len(nodes), edges)
    return {"nodes": len(nodes), "edges": edges}


def ingest_entities(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    *,
    source: str = _SOURCE,
    domain: str = _DOMAIN,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
    """Write typed OWL nodes (+ edges) into the engine.

    Prefers the shared ``native_ingest`` primitive; falls back to a self-contained
    txn write. ``client``/``graph`` may be injected (tests); otherwise resolved via
    the lightweight engine client. Returns ``{"nodes":n,"edges":m}`` or ``None``.
    """
    entities = [e for e in (entities or []) if e.get("id")]
    if not entities:
        return None

    # Preferred path: the shared fleet primitive (the ONE txn write path).
    if client is None:
        try:
            from agent_utilities.knowledge_graph.memory.native_ingest import (
                ingest_entities as _shared,
            )

            return _shared(
                entities,
                relationships,
                source=source,
                domain=domain,
            )
        except Exception as e:  # noqa: BLE001 — primitive absent / failed → fallback
            logger.debug("KG ingest: shared primitive unavailable: %s", e)

    # Fallback path: resolve a client ourselves and do the txn dance.
    if client is None:
        client, graph = _client()
    if client is None:
        return None
    return _fallback_write(
        entities, relationships, client=client, graph=graph or _DEFAULT_GRAPH
    )


def ingest_documents(
    docs: list[dict[str, Any]],
    *,
    source: str = _SOURCE,
    domain: str = _DOMAIN,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
    """Write free-text ``:Document`` nodes (element/view documentation) for search.

    ``docs``: ``[{"id":..., "title":..., "text":..., "source_uri":...}]``. Prefers the
    shared primitive; falls back to typed-node write with ``type="Document"``.
    """
    docs = [d for d in (docs or []) if d.get("id") and d.get("text")]
    if not docs:
        return None

    if client is None:
        try:
            from agent_utilities.knowledge_graph.memory.native_ingest import (
                ingest_documents as _shared_docs,
            )

            return _shared_docs(docs, source=source, domain=domain)
        except Exception as e:  # noqa: BLE001 — primitive absent → fallback
            logger.debug("KG ingest: shared doc primitive unavailable: %s", e)

    nodes = [{**d, "type": "Document"} for d in docs]
    if client is None:
        client, graph = _client()
    if client is None:
        return None
    return _fallback_write(nodes, None, client=client, graph=graph or _DEFAULT_GRAPH)


# --------------------------------------------------------------------------- #
# Mappers — ArchiMate records → typed entity / relationship / document dicts
# --------------------------------------------------------------------------- #
def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "model").lower()).strip("-") or "model"


def _node_id(kind: str, ext_id: str) -> str:
    return f"archimate:{kind.lower()}:{ext_id}"


def build_model_graph(
    elements: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    views: list[dict[str, Any]] | None = None,
    model: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Map ArchiMate model records → ``(entities, relationships, documents)``.

    Pure function (no engine): each element → an ``:<ArchiMateType>`` node, each
    relationship → an ``:ArchimateRelationship`` node + a direct edge, each view →
    an ``:ArchimateView`` node, plus an owning ``:ArchimateModel`` node. Element and
    view documentation become ``:Document`` nodes for semantic search.
    """
    entities: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    documents: list[dict[str, Any]] = []

    model = model or {}
    model_name = model.get("name") or "ArchiMate Model"
    model_ext = model.get("id") or _slug(model_name)
    model_nid = _node_id("model", model_ext)
    entities.append(
        {
            "id": model_nid,
            "type": "ArchimateModel",
            "name": model_name,
            "documentation": model.get("documentation") or None,
            "externalToolId": str(model_ext),
        }
    )

    # id (raw archimate element id) -> KG node id, for edge wiring.
    elem_nid: dict[str, str] = {}
    for elem in elements or []:
        eid = elem.get("id")
        etype = elem.get("type")
        if not eid or not etype:
            continue
        nid = _node_id(etype, eid)
        elem_nid[eid] = nid
        entities.append(
            {
                "id": nid,
                "type": etype,
                "name": elem.get("name") or None,
                "documentation": elem.get("documentation") or None,
                "archimateType": etype,
                "archimateLayer": elem.get("layer") or _layer_of(etype),
                "externalToolId": str(eid),
            }
        )
        edges.append({"source": model_nid, "target": nid, "type": "hasElement"})
        doc = (elem.get("documentation") or "").strip()
        if doc:
            documents.append(
                {
                    "id": f"{nid}:doc",
                    "type": "Document",
                    "title": elem.get("name") or etype,
                    "text": doc,
                    "source_uri": nid,
                    "archimateType": etype,
                }
            )

    for rel in relationships or []:
        rid = rel.get("id")
        rtype = rel.get("type")
        src = rel.get("source")
        tgt = rel.get("target")
        if not rid or not rtype:
            continue
        rnid = _node_id("relationship", rid)
        src_nid = elem_nid.get(src)
        tgt_nid = elem_nid.get(tgt)
        entities.append(
            {
                "id": rnid,
                "type": "ArchimateRelationship",
                "name": rel.get("name") or None,
                "archimateType": rtype,
                "relSource": src_nid,
                "relTarget": tgt_nid,
                "externalToolId": str(rid),
            }
        )
        # Direct element-to-element edge carrying the ArchiMate relationship type.
        if src_nid and tgt_nid:
            edges.append({"source": src_nid, "target": tgt_nid, "type": rtype})

    for view in views or []:
        vid = view.get("id")
        if not vid:
            continue
        vnid = _node_id("view", vid)
        entities.append(
            {
                "id": vnid,
                "type": "ArchimateView",
                "name": view.get("name") or None,
                "documentation": view.get("documentation") or None,
                "externalToolId": str(vid),
            }
        )
        edges.append({"source": model_nid, "target": vnid, "type": "hasView"})
        for node in view.get("nodes", []) or []:
            ref = elem_nid.get(node.get("element_ref"))
            if ref:
                edges.append({"source": vnid, "target": ref, "type": "depictsElement"})

    return entities, edges, documents


def ingest_model(
    elements: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    views: list[dict[str, Any]] | None = None,
    model: dict[str, Any] | None = None,
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
    """Map ArchiMate model records and push them into the KG.

    Returns ``{"nodes":n,"edges":m,"documents":d}`` or ``None`` (no engine).
    """
    entities, edges, documents = build_model_graph(
        elements, relationships, views, model
    )
    res = ingest_entities(entities, edges, client=client, graph=graph)
    if res is None:
        return None
    doc_res = ingest_documents(documents, client=client, graph=graph)
    res["documents"] = (doc_res or {}).get("nodes", 0)
    return res


def ingest_from_api(
    api: Any,
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int] | None:
    """List the current model via an :class:`ArchiApi` and ingest it.

    Best-effort: any listing error yields ``None`` (never raises). Used both by the
    Wire-First MCP tool and the default-on auto-ingest hook on model load.
    """
    try:
        elements = api.list_elements()
        relationships = api.list_relationships()
        views = api.list_views()
        model = api.model_summary()
    except Exception as e:  # noqa: BLE001 — listing failure is non-fatal
        logger.debug("KG ingest: could not list model: %s", e)
        return None
    return ingest_model(
        elements, relationships, views, model, client=client, graph=graph
    )
