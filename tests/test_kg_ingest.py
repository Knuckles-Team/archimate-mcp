"""Native epistemic-graph typed-node ingestion — Wire-First coverage.

Exercises the real ``build_model_graph`` mapper + ``ingest_entities`` / ``ingest_model``
/ ``ingest_from_api`` seams with a fake ChangeEnvelope client and a fake ArchiApi (no
engine required), asserting the governed atomic write and the ArchiMate element →
:ApplicationComponent / relationship → :ArchimateRelationship mapping.
CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

from typing import Any

import msgpack
import pytest
from agent_utilities.knowledge_graph.core.session import GraphSession, use_session
from agent_utilities.knowledge_graph.memory.native_ingest import NativeIngestError
from agent_utilities.models.company_brain import ActorType
from agent_utilities.security.brain_context import ActorContext, use_actor

from archimate_mcp.kg_ingest import (
    build_model_graph,
    ingest_entities,
    ingest_from_api,
    ingest_model,
)


@pytest.fixture(autouse=True)
def _governed_session():
    actor = ActorContext(
        actor_id="subject:opaque:synthetic",
        actor_type=ActorType.AUTOMATED_SERVICE,
        roles=(),
        tenant_id="tenant:opaque:synthetic",
        authenticated=True,
    )
    session = GraphSession(
        actor=actor,
        tenant=actor.tenant_id,
        scopes=frozenset({"kg:write"}),
        graph="graph:opaque:synthetic",
        policy_version="policy:opaque:synthetic",
        audience="epistemic-graph",
    )
    with use_actor(actor), use_session(session):
        yield


class _FakeNodes:
    def __init__(self) -> None:
        self.values: dict[str, dict[str, Any]] = {}

    def properties(self, node_id: str) -> dict[str, Any] | None:
        return self.values.get(node_id)

    def list(self) -> list[tuple[str, dict[str, Any]]]:
        return list(self.values.items())


class _FakeChanges:
    def __init__(self, nodes: _FakeNodes) -> None:
        self.nodes = nodes
        self.edges: list[tuple[str, str, dict[str, Any]]] = []
        self.applied: list[dict[str, Any]] = []
        self.records: dict[str, dict[str, Any]] = {}
        self.versions: dict[str, dict[str, Any]] = {}

    def get(self, envelope_id: str) -> dict[str, Any] | None:
        return self.records.get(envelope_id)

    def content_version(self, object_id: str) -> dict[str, Any] | None:
        return self.versions.get(object_id)

    def cursor(self, _source: str, _partition: str = "") -> None:
        return None

    def apply(self, envelope: dict[str, Any]) -> dict[str, Any]:
        self.applied.append(envelope)
        mutation = envelope["mutation"]
        for operation in mutation["operations"]:
            method = operation["method"]
            params = method["params"]
            properties = msgpack.unpackb(params["properties_msgpack"], raw=False)
            if method["method"] == "AddNode":
                self.nodes.values[params["node_id"]] = properties
            elif method["method"] == "AddEdge":
                self.edges.append(
                    (params["source_id"], params["target_id"], properties)
                )
        version = envelope["content_version"]
        self.versions[version["object_id"]] = version
        self.records[envelope["envelope_id"]] = envelope
        return {
            "batch_id": mutation["batch_id"],
            "replayed": False,
            "projection_pending": False,
        }


class _FakeRdf:
    def validate_shacl(self, _shapes: str, _data_graph: str) -> dict[str, Any]:
        return {"conforms": True, "results": []}


class _FakeClient:
    def __init__(self) -> None:
        self.nodes = _FakeNodes()
        self.changes = _FakeChanges(self.nodes)
        self.rdf = _FakeRdf()

    @staticmethod
    def supports(operation: str) -> bool:
        return operation == "ApplyChangeEnvelope"


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
# Engine write path (fake client)
# --------------------------------------------------------------------------- #
def test_ingest_entities_writes_nodes_and_edges():
    c = _FakeClient()
    res = ingest_entities(
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
        client=c,
        graph="graph:opaque:synthetic",
    )
    assert res == {"nodes": 2, "edges": 1}
    assert len(c.changes.applied) == 1
    assert set(c.nodes.values) == {"archimate:model:m1", "archimate:node:n1"}
    # provenance is stamped
    assert c.nodes.values["archimate:model:m1"]["source"] == "archimate-mcp"
    assert c.nodes.values["archimate:model:m1"]["domain"] == "archimate"
    assert c.changes.edges[0][2] == {"relationship": "hasElement"}


def test_ingest_model_end_to_end_with_fake_client():
    c = _FakeClient()
    res = ingest_model(
        _FakeApi().list_elements(),
        _FakeApi().list_relationships(),
        _FakeApi().list_views(),
        _FakeApi().model_summary(),
        client=c,
    )
    assert res is not None
    # model + 2 elements + 1 relationship + 1 view = 5 nodes
    assert res["nodes"] == 5
    assert res["documents"] == 1
    assert c.nodes.values["archimate:applicationcomponent:elem-a"]["node_type"] == (
        "ApplicationComponent"
    )


def test_ingest_from_api_lists_and_pushes():
    c = _FakeClient()
    res = ingest_from_api(_FakeApi(), client=c)
    assert res is not None
    assert res["nodes"] == 5
    assert "archimate:relationship:rel-1" in c.nodes.values


# --------------------------------------------------------------------------- #
# Guarded no-ops
# --------------------------------------------------------------------------- #
def test_ingest_rejects_legacy_structural_fields():
    with pytest.raises(NativeIngestError, match="canonical node_type"):
        ingest_entities([{"id": "legacy", "type": "Legacy"}], client=_FakeClient())


def test_ingest_empty_is_rejected():
    with pytest.raises(NativeIngestError, match="at least one entity"):
        ingest_entities([], client=_FakeClient())
