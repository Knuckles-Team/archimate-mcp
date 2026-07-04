"""Native epistemic-graph typed-node ingestion — Wire-First coverage.

Exercises the real ``build_model_graph`` mapper + ``ingest_entities`` / ``ingest_model``
/ ``ingest_from_api`` seams with a fake engine client and a fake ArchiApi (no engine
required), asserting the txn add_node/commit + edge calls and the ArchiMate element →
:ApplicationComponent / relationship → :ArchimateRelationship mapping.
CONCEPT:AU-KG.ingest.enterprise-source-extractor.
"""

from __future__ import annotations

from archimate_mcp.kg_ingest import (
    build_model_graph,
    ingest_entities,
    ingest_from_api,
    ingest_model,
)


class _FakeTxn:
    def __init__(self):
        self.nodes = {}
        self.committed = False

    def begin(self, graph=None):
        self.graph = graph
        return "txn-1"

    def add_node(self, txn, node_id, props):
        self.nodes[node_id] = props

    def commit(self, txn):
        self.committed = True
        return True


class _FakeEdges:
    def __init__(self):
        self.edges = []

    def add(self, src, dst, props):
        self.edges.append((src, dst, props))


class _FakeClient:
    def __init__(self):
        self.txn = _FakeTxn()
        self.edges = _FakeEdges()


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
    assert by_id["archimate:model:model-1"]["type"] == "ArchimateModel"
    ac = by_id["archimate:applicationcomponent:elem-a"]
    assert ac["type"] == "ApplicationComponent"
    assert ac["archimateType"] == "ApplicationComponent"
    assert ac["archimateLayer"] == "Application"
    assert ac["externalToolId"] == "elem-a"
    rel = by_id["archimate:relationship:rel-1"]
    assert rel["type"] == "ArchimateRelationship"
    assert rel["archimateType"] == "Serving"
    assert rel["relSource"] == "archimate:applicationcomponent:elem-a"
    assert by_id["archimate:view:view-1"]["type"] == "ArchimateView"

    # direct Serving edge between the two elements + hasElement/hasView/depictsElement
    assert (
        "archimate:applicationcomponent:elem-a",
        "archimate:applicationservice:elem-b",
        "Serving",
    ) in {(e["source"], e["target"], e["type"]) for e in edges}
    edge_types = {e["type"] for e in edges}
    assert {"hasElement", "hasView", "depictsElement", "Serving"} <= edge_types

    # documentation becomes a :Document node
    assert docs and docs[0]["type"] == "Document"
    assert docs[0]["text"] == "Issues invoices"


# --------------------------------------------------------------------------- #
# Engine write path (fake client)
# --------------------------------------------------------------------------- #
def test_ingest_entities_writes_nodes_and_edges():
    c = _FakeClient()
    res = ingest_entities(
        [
            {"id": "archimate:model:m1", "type": "ArchimateModel", "name": "m"},
            {"id": "archimate:node:n1", "type": "Node"},
        ],
        [
            {
                "source": "archimate:model:m1",
                "target": "archimate:node:n1",
                "type": "hasElement",
            }
        ],
        client=c,
        graph="__commons__",
    )
    assert res == {"nodes": 2, "edges": 1}
    assert c.txn.committed is True
    assert set(c.txn.nodes) == {"archimate:model:m1", "archimate:node:n1"}
    # provenance is stamped
    assert c.txn.nodes["archimate:model:m1"]["source"] == "archimate-mcp"
    assert c.txn.nodes["archimate:model:m1"]["domain"] == "archimate"
    assert c.edges.edges[0][2] == {"type": "hasElement"}


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
    assert c.txn.nodes["archimate:applicationcomponent:elem-a"]["type"] == (
        "ApplicationComponent"
    )


def test_ingest_from_api_lists_and_pushes():
    c = _FakeClient()
    res = ingest_from_api(_FakeApi(), client=c)
    assert res is not None
    assert res["nodes"] == 5
    assert "archimate:relationship:rel-1" in c.txn.nodes


# --------------------------------------------------------------------------- #
# Guarded no-ops
# --------------------------------------------------------------------------- #
def test_ingest_noops_without_engine():
    # No injected client + no reachable engine -> clean no-op (never raises).
    # Returns None (no engine) or a dict (engine happened to be reachable); never raises.
    res = ingest_entities([{"id": "archimate:node:n1", "type": "Node"}], client=None)
    assert res is None or isinstance(res, dict)


def test_ingest_empty_is_noop():
    assert ingest_entities([], client=_FakeClient()) is None
    assert build_model_graph([], [], [], {})[0][0]["type"] == "ArchimateModel"
