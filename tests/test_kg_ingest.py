"""Native epistemic-graph typed-node ingestion — Wire-First coverage.

Exercises the real ``build_model_graph`` mapper + ``ingest_entities`` / ``ingest_model``
/ ``ingest_from_api`` seams against a fake epistemic-graph ingest transport (no engine
required), asserting the governed atomic write and the ArchiMate element →
:ApplicationComponent / relationship → :ArchimateRelationship mapping.
CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from agent_connector_sdk.ingest import IngestError, KnowledgeIngest

from archimate_mcp.kg_ingest import (
    build_model_graph,
    ingest_entities,
    ingest_from_api,
    ingest_model,
)


class _FakeTransport:
    """Stands in for the epistemic-graph ingest transport boundary."""

    def __init__(self) -> None:
        self.requests: list[Any] = []

    async def source_status(self, connector: str, stream: str) -> SimpleNamespace:
        return SimpleNamespace(accepted_checkpoint=None)

    async def submit(self, request: Any) -> SimpleNamespace:
        self.requests.append(request)
        return SimpleNamespace(
            affected_count=len(request.records),
            relationship_count=len(request.relationships),
        )

    async def store_blob(self, data: bytes) -> str:
        raise AssertionError("this connector's ingestion carries no media")


@pytest.fixture
def ingest() -> tuple[KnowledgeIngest, _FakeTransport]:
    transport = _FakeTransport()
    return KnowledgeIngest(transport, loop=None), transport


class _FakeApi:
    """Stands in for ArchiApi's list_* / model_summary surface."""

    def list_elements(self):
        return [
            {
                "id": "elem-a",
                "type": "ApplicationComponent",
                "name": "Billing",
                "documentation": "Issues invoices",
                "layer": "Application",
            },
            {"id": "elem-b", "type": "ApplicationService", "name": "Portal"},
        ]

    def list_relationships(self):
        return [
            {
                "id": "rel-1",
                "type": "Serving",
                "source": "elem-a",
                "target": "elem-b",
                "name": "",
            }
        ]

    def list_views(self):
        return [
            {
                "id": "view-1",
                "name": "App Cooperation",
                "nodes": [{"element_ref": "elem-a"}],
                "connections": [],
            }
        ]

    def model_summary(self):
        return {"id": "model-1", "name": "Payments", "counts": {"elements": 2}}


# --------------------------------------------------------------------------- #
# Pure mapper
# --------------------------------------------------------------------------- #
def test_build_model_graph_maps_elements_relationships_views():
    entities, edges, docs = build_model_graph(
        _FakeApi().list_elements(),
        _FakeApi().list_relationships(),
        _FakeApi().list_views(),
        _FakeApi().model_summary(),
    )
    by_id = {e["id"]: e for e in entities}

    # model + 2 elements + 1 relationship + 1 view
    assert by_id["archimate:model:model-1"]["node_type"] == "ArchimateModel"
    ac = by_id["archimate:applicationcomponent:elem-a"]
    assert ac["node_type"] == "ApplicationComponent"
    assert ac["archimateType"] == "ApplicationComponent"
    assert ac["archimateLayer"] == "Application"
    assert ac["externalToolId"] == "elem-a"
    rel = by_id["archimate:relationship:rel-1"]
    assert rel["node_type"] == "ArchimateRelationship"
    assert rel["archimateType"] == "Serving"
    assert rel["relSource"] == "archimate:applicationcomponent:elem-a"
    assert by_id["archimate:view:view-1"]["node_type"] == "ArchimateView"

    # direct Serving edge between the two elements + hasElement/hasView/depictsElement
    assert (
        "archimate:applicationcomponent:elem-a",
        "archimate:applicationservice:elem-b",
        "Serving",
    ) in {(e["source"], e["target"], e["relationship"]) for e in edges}
    edge_types = {e["relationship"] for e in edges}
    assert {"hasElement", "hasView", "depictsElement", "Serving"} <= edge_types

    # documentation becomes a :Document node
    assert docs and docs[0]["document_type"] == "archimate_element"
    assert docs[0]["text"] == "Issues invoices"


def test_build_model_graph_normalizes_external_identifiers():
    entities, edges, _documents = build_model_graph(
        [{"id": 7, "type": "ApplicationComponent", "name": "Synthetic"}],
        [{"id": 8, "type": "Serving", "source": 7, "target": "7"}],
        [{"id": 9, "nodes": [{"element_ref": 7}]}],
        {"id": 10, "name": "Synthetic model"},
    )

    assert {entity["id"] for entity in entities} >= {
        "archimate:model:10",
        "archimate:applicationcomponent:7",
        "archimate:relationship:8",
        "archimate:view:9",
    }
    assert {
        (edge["source"], edge["target"], edge["relationship"]) for edge in edges
    } >= {
        (
            "archimate:applicationcomponent:7",
            "archimate:applicationcomponent:7",
            "Serving",
        ),
        (
            "archimate:view:9",
            "archimate:applicationcomponent:7",
            "depictsElement",
        ),
    }


# --------------------------------------------------------------------------- #
# Engine write path (fake transport)
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_ingest_entities_writes_nodes_and_edges(ingest):
    service, transport = ingest
    res = await ingest_entities(
        [
            {"id": "archimate:model:m1", "node_type": "ArchimateModel", "name": "m"},
            {"id": "archimate:node:n1", "node_type": "Node"},
        ],
        [
            {
                "source": "archimate:model:m1",
                "target": "archimate:node:n1",
                "relationship": "hasElement",
            }
        ],
        ingest=service,
    )
    assert res == {"nodes": 2, "edges": 1}
    assert len(transport.requests) == 1
    request = transport.requests[0]
    assert {record.record_id for record in request.records} == {
        "archimate:model:m1",
        "archimate:node:n1",
    }
    assert request.relationships[0].relation_reference.endswith("/relations/hasElement")


@pytest.mark.asyncio
async def test_ingest_model_end_to_end_with_fake_transport(ingest):
    service, transport = ingest
    res = await ingest_model(
        _FakeApi().list_elements(),
        _FakeApi().list_relationships(),
        _FakeApi().list_views(),
        _FakeApi().model_summary(),
        ingest=service,
    )
    assert res is not None
    # model + 2 elements + 1 relationship + 1 view = 5 nodes
    assert res["nodes"] == 5
    assert res["documents"] == 1
    # two submits: entities+relationships, then documents
    assert len(transport.requests) == 2
    entity_ids = {record.record_id for record in transport.requests[0].records}
    assert "archimate:applicationcomponent:elem-a" in entity_ids


@pytest.mark.asyncio
async def test_ingest_from_api_lists_and_pushes(ingest):
    service, transport = ingest
    res = await ingest_from_api(_FakeApi(), ingest=service)
    assert res is not None
    assert res["nodes"] == 5
    entity_ids = {record.record_id for record in transport.requests[0].records}
    assert "archimate:relationship:rel-1" in entity_ids


# --------------------------------------------------------------------------- #
# Guarded no-ops
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_ingest_rejects_entity_missing_node_type(ingest):
    service, _transport = ingest
    with pytest.raises(IngestError, match="node_type"):
        await ingest_entities([{"id": "legacy", "type": "Legacy"}], ingest=service)


@pytest.mark.asyncio
async def test_ingest_empty_is_rejected(ingest):
    service, _transport = ingest
    with pytest.raises(IngestError, match="at least one entity"):
        await ingest_entities([], ingest=service)
