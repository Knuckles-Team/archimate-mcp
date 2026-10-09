"""Native epistemic-graph ingestion for ArchiMate models (typed OWL nodes).

CONCEPT:AU-KG.ingest.enterprise-source-extractor. The archimate-mcp package natively
pushes an ArchiMate model into the ONE epistemic-graph knowledge graph as **typed OWL
nodes** — every element becomes an ``:ArchimateElement`` subclass node (``:ApplicationComponent``,
``:BusinessProcess``, ``:Node``, …), every relationship a reified ``:ArchimateRelationship``
node **and** a direct LPG edge between its endpoints, and every view an ``:ArchimateView``
node. The classes match those federated by :mod:`archimate_mcp.ontology`.

Writes go directly through the ``agent_connector_sdk.ingest`` knowledge-ingest facade
(the generated EG client), bound to this connector's manifest identity. Node ids follow
``archimate:<class>:<extId>`` and structural fields use ``node_type`` / ``relationship``.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from agent_connector_sdk.ingest import (
    ChangeSet,
    Document,
    Entity,
    IngestBinding,
    IngestError,
    KnowledgeIngest,
    Relationship,
    current_ingest,
)

from archimate_mcp.api.archimate_model import LAYER_OF_TYPE

logger = logging.getLogger("archimate_mcp.kg")

_SOURCE = "archimate-mcp"
_DOMAIN = "archimate"
_BINDING = IngestBinding(connector=_SOURCE, stream=_DOMAIN)


def _layer_of(elem_type: str) -> str | None:
    """Return the ArchiMate layer of ``elem_type``."""
    return LAYER_OF_TYPE.get(elem_type)


def _to_entity(record: dict[str, Any]) -> Entity:
    return Entity(
        id=record.get("id"),
        node_type=record.get("node_type"),
        properties={k: v for k, v in record.items() if k not in ("id", "node_type")},
    )


def _to_relationship(record: dict[str, Any]) -> Relationship:
    props = {
        k: v
        for k, v in record.items()
        if k not in ("source", "target", "relationship")
    }
    return Relationship(
        source=record["source"],
        target=record["target"],
        relationship=record["relationship"],
        properties=props or None,
    )


def _to_document(record: dict[str, Any]) -> Document:
    return Document(
        id=record["id"],
        text=record.get("text", ""),
        title=record.get("title"),
        source_uri=record.get("source_uri"),
        properties={
            k: v
            for k, v in record.items()
            if k not in ("id", "text", "title", "source_uri")
        },
    )


async def ingest_entities(
    entities: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    *,
    ingest: KnowledgeIngest | None = None,
) -> dict[str, int]:
    """Write typed OWL nodes (+ edges) into the engine.

    Validation and engine failures are surfaced as ``IngestError``.
    """
    if not entities:
        raise IngestError("ingest_entities needs at least one entity")
    change_set = ChangeSet(
        entities=tuple(_to_entity(e) for e in entities),
        relationships=tuple(_to_relationship(r) for r in relationships or ()),
    )
    service = ingest or current_ingest()
    receipt = await service.submit(_BINDING, change_set)
    return {"nodes": receipt.affected_count, "edges": receipt.relationship_count}


async def ingest_documents(
    docs: list[dict[str, Any]],
    *,
    ingest: KnowledgeIngest | None = None,
) -> dict[str, int]:
    """Write free-text ``:Document`` nodes (element/view documentation) for search.

    ``docs``: ``[{"id":..., "title":..., "text":..., "source_uri":...}]``.
    """
    if not docs:
        return {"nodes": 0}
    change_set = ChangeSet(documents=tuple(_to_document(d) for d in docs))
    service = ingest or current_ingest()
    receipt = await service.submit(_BINDING, change_set)
    return {"nodes": receipt.affected_count}


# --------------------------------------------------------------------------- #
# Mappers — ArchiMate records → typed entity / relationship / document dicts
# --------------------------------------------------------------------------- #
def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "model").lower()).strip("-") or "model"


def _node_id(kind: str, ext_id: str) -> str:
    return f"archimate:{kind.lower()}:{ext_id}"


def _build_model_entity(model: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """Return the owning ``:ArchimateModel`` entity dict and its KG node id."""
    model_name = model.get("name") or "ArchiMate Model"
    model_ext = model.get("id") or _slug(model_name)
    model_nid = _node_id("model", model_ext)
    entity = {
        "id": model_nid,
        "node_type": "ArchimateModel",
        "name": model_name,
        "documentation": model.get("documentation") or None,
        "externalToolId": str(model_ext),
    }
    return entity, model_nid


def _element_documentation_node(
    nid: str, etype_name: str, elem: dict[str, Any]
) -> dict[str, Any] | None:
    """Return a ``:Document`` node for ``elem``'s documentation, if any."""
    doc = (elem.get("documentation") or "").strip()
    if not doc:
        return None
    return {
        "id": f"{nid}:doc",
        "document_type": "archimate_element",
        "title": elem.get("name") or etype_name,
        "text": doc,
        "source_uri": nid,
        "archimateType": etype_name,
    }


def _map_element_record(
    elem: dict[str, Any], model_nid: str
) -> tuple[str, str, dict[str, Any], dict[str, Any], dict[str, Any] | None] | None:
    """Map one ArchiMate element to its (id key, node id, entity, edge, doc)."""
    eid = elem.get("id")
    etype = elem.get("type")
    if not eid or not etype:
        return None
    eid_key = str(eid)
    etype_name = str(etype)
    nid = _node_id(etype_name, eid_key)
    entity = {
        "id": nid,
        "node_type": etype_name,
        "name": elem.get("name") or None,
        "documentation": elem.get("documentation") or None,
        "archimateType": etype_name,
        "archimateLayer": elem.get("layer") or _layer_of(etype_name),
        "externalToolId": eid_key,
    }
    edge = {"source": model_nid, "target": nid, "relationship": "hasElement"}
    doc = _element_documentation_node(nid, etype_name, elem)
    return eid_key, nid, entity, edge, doc


def _map_elements(
    elements: list[dict[str, Any]], model_nid: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    """Map ArchiMate elements → (entities, edges, documents, id -> KG node id)."""
    entities: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    documents: list[dict[str, Any]] = []
    elem_nid: dict[str, str] = {}

    for elem in elements or []:
        mapped = _map_element_record(elem, model_nid)
        if mapped is None:
            continue
        eid_key, nid, entity, edge, doc = mapped
        elem_nid[eid_key] = nid
        entities.append(entity)
        edges.append(edge)
        if doc:
            documents.append(doc)

    return entities, edges, documents, elem_nid


def _map_relationship_record(
    rel: dict[str, Any], elem_nid: dict[str, str]
) -> tuple[dict[str, Any], dict[str, Any] | None] | None:
    """Map one ArchiMate relationship to its (entity, direct element-to-element edge)."""
    rid = rel.get("id")
    rtype = rel.get("type")
    if not rid or not rtype:
        return None
    rid_key = str(rid)
    relationship_type = str(rtype)
    rnid = _node_id("relationship", rid_key)
    src = rel.get("source")
    tgt = rel.get("target")
    src_nid = elem_nid.get(str(src)) if src is not None else None
    tgt_nid = elem_nid.get(str(tgt)) if tgt is not None else None
    entity = {
        "id": rnid,
        "node_type": "ArchimateRelationship",
        "name": rel.get("name") or None,
        "archimateType": relationship_type,
        "relSource": src_nid,
        "relTarget": tgt_nid,
        "externalToolId": rid_key,
    }
    # Direct element-to-element edge carrying the ArchiMate relationship type.
    edge = None
    if src_nid and tgt_nid:
        edge = {"source": src_nid, "target": tgt_nid, "relationship": relationship_type}
    return entity, edge


def _map_relationships(
    relationships: list[dict[str, Any]] | None, elem_nid: dict[str, str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Map ArchiMate relationships → (entities, direct element-to-element edges)."""
    entities: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for rel in relationships or []:
        mapped = _map_relationship_record(rel, elem_nid)
        if mapped is None:
            continue
        entity, edge = mapped
        entities.append(entity)
        if edge:
            edges.append(edge)

    return entities, edges


def _view_depicts_edges(
    view: dict[str, Any], vnid: str, elem_nid: dict[str, str]
) -> list[dict[str, Any]]:
    """Return ``depictsElement`` edges from ``view`` to the elements it shows."""
    edges: list[dict[str, Any]] = []
    for node in view.get("nodes", []) or []:
        element_ref = node.get("element_ref")
        ref = elem_nid.get(str(element_ref)) if element_ref is not None else None
        if ref:
            edges.append({"source": vnid, "target": ref, "relationship": "depictsElement"})
    return edges


def _map_view_record(
    view: dict[str, Any], model_nid: str, elem_nid: dict[str, str]
) -> tuple[dict[str, Any], list[dict[str, Any]]] | None:
    """Map one ArchiMate view to its (entity, [hasView edge, depictsElement edges...])."""
    vid = view.get("id")
    if not vid:
        return None
    vid_key = str(vid)
    vnid = _node_id("view", vid_key)
    entity = {
        "id": vnid,
        "node_type": "ArchimateView",
        "name": view.get("name") or None,
        "documentation": view.get("documentation") or None,
        "externalToolId": vid_key,
    }
    edges = [{"source": model_nid, "target": vnid, "relationship": "hasView"}]
    edges.extend(_view_depicts_edges(view, vnid, elem_nid))
    return entity, edges


def _map_views(
    views: list[dict[str, Any]] | None, model_nid: str, elem_nid: dict[str, str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Map ArchiMate views → (entities, edges to the model + depicted elements)."""
    entities: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    for view in views or []:
        mapped = _map_view_record(view, model_nid, elem_nid)
        if mapped is None:
            continue
        entity, view_edges = mapped
        entities.append(entity)
        edges.extend(view_edges)

    return entities, edges


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
    model_entity, model_nid = _build_model_entity(model or {})
    entities: list[dict[str, Any]] = [model_entity]
    edges: list[dict[str, Any]] = []
    documents: list[dict[str, Any]] = []

    elem_entities, elem_edges, elem_docs, elem_nid = _map_elements(elements, model_nid)
    entities.extend(elem_entities)
    edges.extend(elem_edges)
    documents.extend(elem_docs)

    rel_entities, rel_edges = _map_relationships(relationships, elem_nid)
    entities.extend(rel_entities)
    edges.extend(rel_edges)

    view_entities, view_edges = _map_views(views, model_nid, elem_nid)
    entities.extend(view_entities)
    edges.extend(view_edges)

    return entities, edges, documents


async def ingest_model(
    elements: list[dict[str, Any]],
    relationships: list[dict[str, Any]] | None = None,
    views: list[dict[str, Any]] | None = None,
    model: dict[str, Any] | None = None,
    *,
    ingest: KnowledgeIngest | None = None,
) -> dict[str, int]:
    """Map ArchiMate model records and push them into the KG.

    Returns ``{"nodes":n,"edges":m,"documents":d}`` or raises on failure.
    """
    entities, edges, documents = build_model_graph(
        elements, relationships, views, model
    )
    res = await ingest_entities(entities, edges, ingest=ingest)
    doc_res = (
        await ingest_documents(documents, ingest=ingest)
        if documents
        else {"nodes": 0}
    )
    res["documents"] = doc_res["nodes"]
    return res


async def ingest_from_api(
    api: Any,
    *,
    ingest: KnowledgeIngest | None = None,
) -> dict[str, int]:
    """List the current model via an :class:`ArchiApi` and ingest it.

    Source and ingestion failures propagate to the caller.
    """
    elements = api.list_elements()
    relationships = api.list_relationships()
    views = api.list_views()
    model = api.model_summary()
    return await ingest_model(
        elements, relationships, views, model, ingest=ingest
    )
