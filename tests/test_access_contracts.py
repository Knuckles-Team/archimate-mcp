"""CONN-ARCHIMATE-MCP-CONNECTOR-CONTENT-R002: the competency reads are declared
as access contracts and each recorded response satisfies its contract."""

import asyncio
import json
from importlib import resources
from pathlib import Path

import pytest
from fastmcp import Client
from scion_sdk.access_contract import parse_access_contracts
from scion_sdk.connector import build_server

from archimate_mcp.api.api_client_archi import ArchiApi

ID = "CONN-ARCHIMATE-MCP-CONNECTOR-CONTENT-R002"
ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = parse_access_contracts(
    (ROOT / "archimate_mcp/ontology/access_contracts.ttl").read_text()
)
ONTOLOGY = (
    resources.files("archimate_mcp").joinpath("ontology", "archimate.ttl").read_text()
)
CONNECTOR_NS = "https://knuckles-team.github.io/ontology/connector/archimate#"


def _model(tmp_path):
    path = tmp_path / "model.archimate"
    api = ArchiApi(model_path=str(path), autoload=False)
    api.new_model("Fixture")
    crm = api.add_element("ApplicationComponent", "CRM")
    host = api.add_element("Node", "Database host")
    api.add_relationship("Serving", host, crm)
    api.save()
    return path


def _serve(operation):
    async def call():
        _, mcp = build_server("archimate_mcp", command_args=[])
        async with Client(mcp) as client:
            assert operation in {t.name for t in await client.list_tools()}
            result = await client.call_tool(operation, {})
            return json.loads(result.content[0].text)

    return asyncio.run(call())


@pytest.mark.spec(ID)
def test_competency_contracts_certified(tmp_path, monkeypatch):
    monkeypatch.setenv("ARCHI_MODEL_PATH", str(_model(tmp_path)))
    assert {c.entity for c in CONTRACTS} == {"element", "relationship"}
    for contract in CONTRACTS:
        assert contract.source_id == "archimate-mcp"
        assert contract.access_kind == "mcp_tool"
        assert contract.pagination == "none"
        assert contract.key_field == "id"
        assert contract.class_iri.startswith(CONNECTOR_NS)
        local = contract.class_iri.removeprefix(CONNECTOR_NS)
        assert f"\n:{local} a owl:Class" in ONTOLOGY
        for prop, _field in contract.predicates:
            if prop.startswith(CONNECTOR_NS):
                name = prop.removeprefix(CONNECTOR_NS)
                assert f"\n:{name} a owl:" in ONTOLOGY, name
        recording = json.loads(
            (ROOT / f"tests/recordings/{contract.entity}.json").read_text()
        )
        assert recording
        for record in recording:
            assert contract.key_field in record
            assert all(field in record for _, field in contract.predicates)
        served = _serve(contract.operation)
        assert {frozenset(r) for r in served} == {frozenset(r) for r in recording}


@pytest.mark.spec(ID)
def test_contract_refuses_a_recording_missing_a_bound_field():
    (contract,) = [c for c in CONTRACTS if c.entity == "relationship"]
    record = {"id": "x", "type": "Serving", "source": "a"}
    assert not all(field in record for _, field in contract.predicates)
