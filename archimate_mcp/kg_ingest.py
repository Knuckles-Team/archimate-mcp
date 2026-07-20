"""Native epistemic-graph ingestion for ArchiMate models (typed OWL nodes).

CONCEPT:AU-KG.ingest.enterprise-source-extractor. The archimate-mcp package natively
pushes an ArchiMate model into the ONE epistemic-graph knowledge graph as **typed OWL
nodes** — every element becomes an ``:ArchimateElement`` subclass node (``:ApplicationComponent``,
``:BusinessProcess``, ``:Node``, …), every relationship a reified ``:ArchimateRelationship``
node **and** a direct LPG edge between its endpoints, and every view an ``:ArchimateView``
node. The classes match those federated by :mod:`archimate_mcp.ontology`.

Writes go directly through the required
``agent_utilities.knowledge_graph.memory.native_ingest`` authority. Node ids follow
``archimate:<class>:<extId>`` and structural fields use ``node_type`` / ``relationship``.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from agent_utilities.knowledge_graph.memory.native_ingest import (
    ingest_documents as _native_ingest_documents,
)
from agent_utilities.knowledge_graph.memory.native_ingest import (
    ingest_entities as _native_ingest_entities,
)

from archimate_mcp.api.archimate_model import LAYER_OF_TYPE

logger = logging.getLogger("archimate_mcp.kg")

_SOURCE = "archimate-mcp"
_DOMAIN = "archimate"


def _layer_of(elem_type: str) -> str | None:
    """Return the ArchiMate layer of ``elem_type``."""
    return LAYER_OF_TYPE.get(elem_type)


def ingest_entities(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    *,
    source: str = _SOURCE,
    domain: str = _DOMAIN,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Write typed OWL nodes (+ edges) into the engine.

    Validation and engine failures are surfaced as ``NativeIngestError``.
    """
    return _native_ingest_entities(
        entities,
        relationships,
        source=source,
        domain=domain,
        client=client,
        graph=graph,
    )


def ingest_documents(
    docs: list[dict[str, Any]],
    *,
    source: str = _SOURCE,
    domain: str = _DOMAIN,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Write free-text ``:Document`` nodes (element/view documentation) for search.

    ``docs``: ``[{"id":..., "title":..., "text":..., "source_uri":...}]``.
    """
    return _native_ingest_documents(
        docs, source=source, domain=domain, client=client, graph=graph
    )


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
            "node_type": "ArchimateModel",
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
        eid_key = str(eid)
        etype_name = str(etype)
        nid = _node_id(etype_name, eid_key)
        elem_nid[eid_key] = nid
        entities.append(
            {
                "id": nid,
                "node_type": etype_name,
                "name": elem.get("name") or None,
                "documentation": elem.get("documentation") or None,
                "archimateType": etype_name,
                "archimateLayer": elem.get("layer") or _layer_of(etype_name),
                "externalToolId": eid_key,
            }
        )
        edges.append({"source": model_nid, "target": nid, "relationship": "hasElement"})
        doc = (elem.get("documentation") or "").strip()
        if doc:
            documents.append(
                {
                    "id": f"{nid}:doc",
                    "document_type": "archimate_element",
                    "title": elem.get("name") or etype_name,
                    "text": doc,
                    "source_uri": nid,
                    "archimateType": etype_name,
                }
            )

    for rel in relationships or []:
        rid = rel.get("id")
        rtype = rel.get("type")
        src = rel.get("source")
        tgt = rel.get("target")
        if not rid or not rtype:
            continue
        rid_key = str(rid)
        relationship_type = str(rtype)
        rnid = _node_id("relationship", rid_key)
        src_nid = elem_nid.get(str(src)) if src is not None else None
        tgt_nid = elem_nid.get(str(tgt)) if tgt is not None else None
        entities.append(
            {
                "id": rnid,
                "node_type": "ArchimateRelationship",
                "name": rel.get("name") or None,
                "archimateType": relationship_type,
                "relSource": src_nid,
                "relTarget": tgt_nid,
                "externalToolId": rid_key,
            }
        )
        # Direct element-to-element edge carrying the ArchiMate relationship type.
        if src_nid and tgt_nid:
            edges.append(
                {
                    "source": src_nid,
                    "target": tgt_nid,
                    "relationship": relationship_type,
                }
            )

    for view in views or []:
        vid = view.get("id")
        if not vid:
            continue
        vid_key = str(vid)
        vnid = _node_id("view", vid_key)
        entities.append(
            {
                "id": vnid,
                "node_type": "ArchimateView",
                "name": view.get("name") or None,
                "documentation": view.get("documentation") or None,
                "externalToolId": vid_key,
            }
        )
        edges.append({"source": model_nid, "target": vnid, "relationship": "hasView"})
        for node in view.get("nodes", []) or []:
            element_ref = node.get("element_ref")
            ref = elem_nid.get(str(element_ref)) if element_ref is not None else None
            if ref:
                edges.append(
                    {
                        "source": vnid,
                        "target": ref,
                        "relationship": "depictsElement",
                    }
                )

    return entities, edges, documents


def ingest_model(
    elements: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    views: list[dict[str, Any]] | None = None,
    model: dict[str, Any] | None = None,
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """Map ArchiMate model records and push them into the KG.

    Returns ``{"nodes":n,"edges":m,"documents":d}`` or raises on failure.
    """
    entities, edges, documents = build_model_graph(
        elements, relationships, views, model
    )
    res = ingest_entities(entities, edges, client=client, graph=graph)
    doc_res = (
        ingest_documents(documents, client=client, graph=graph)
        if documents
        else {"nodes": 0}
    )
    res["documents"] = doc_res["nodes"]
    return res


def ingest_from_api(
    api: Any,
    *,
    client: Any | None = None,
    graph: str | None = None,
) -> dict[str, int]:
    """List the current model via an :class:`ArchiApi` and ingest it.

    Source and native-ingestion failures propagate to the caller.
    """
    elements = api.list_elements()
    relationships = api.list_relationships()
    views = api.list_views()
    model = api.model_summary()
    return ingest_model(
        elements, relationships, views, model, client=client, graph=graph
    )
