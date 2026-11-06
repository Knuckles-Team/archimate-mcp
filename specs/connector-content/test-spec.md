# CONN-ARCHIMATE-MCP-CONNECTOR-CONTENT — Test specification

Governing spec: [spec.md](spec.md).

| Test ID | Requirement | Proving test | Expected observation |
|---|---|---|---|
| T-001 | `CONN-ARCHIMATE-MCP-CONNECTOR-CONTENT-R001` | `tests/test_default_content_surfaces.py` | The listings include the packaged skills, ontology and prompts. |

## Rows awaiting bound tests
- `CONN-ARCHIMATE-MCP-CONNECTOR-CONTENT-R002`: planned proof `tests/test_access_contracts.py::test_competency_contracts_certified`. Expected: Each entity has a contract whose operation is the existing tool and whose recording validates against it.. Refusal: A contract naming a column absent from the ontology properties or a missing recording fails certification..
- `CONN-ARCHIMATE-MCP-CONNECTOR-CONTENT-R003`: planned proof `tests/test_access_contracts.py::test_exchange_document_contract_certified`. Expected: Rollup closes when `.1` to `.4` are verified. Root test: `tests/test_access_contracts.py::test_exchange_document_contract_certified`.
- `CONN-ARCHIMATE-MCP-CONNECTOR-CONTENT-R003.1`: planned proof `tests/test_exchange_document_tool.py::test_read_returns_document_and_stable_revision`. Expected: Two reads of an unchanged model return the same revision.
- `CONN-ARCHIMATE-MCP-CONNECTOR-CONTENT-R003.2`: planned proof `tests/test_access_contracts.py::test_exchange_document_contract_certified`. Expected: The contract names the tool and its columns.
- `CONN-ARCHIMATE-MCP-CONNECTOR-CONTENT-R003.3`: planned proof `tests/test_access_contracts.py::test_exchange_recording_validates`. Expected: The recording validates against the contract.
- `CONN-ARCHIMATE-MCP-CONNECTOR-CONTENT-R003.4`: planned proof `tests/test_ontology_rollup.py::test_element_classes_roll_up_to_engine_terms`. Expected: Every element class has one engine ancestor.
- `CONN-ARCHIMATE-MCP-CONNECTOR-CONTENT-R004`: planned proof `tests/test_exchange_import_sink.py::test_released_document_replaces_model_once`. Expected: Rollup closes when `.1` to `.3` are verified. Root test: `tests/test_exchange_import_sink.py::test_released_document_replaces_model_once`.
- `CONN-ARCHIMATE-MCP-CONNECTOR-CONTENT-R004.1`: planned proof `tests/test_exchange_import_sink.py::test_released_document_replaces_model_once`. Expected: A released document replaces the model once.
- `CONN-ARCHIMATE-MCP-CONNECTOR-CONTENT-R004.2`: planned proof `tests/test_exchange_import_sink.py::test_stale_base_revision_refuses_and_keeps_model`. Expected: A stale base revision leaves the model file unchanged.
- `CONN-ARCHIMATE-MCP-CONNECTOR-CONTENT-R004.3`: planned proof `tests/test_exchange_import_sink.py::test_registered_sink_round_trips_revision`. Expected: The read-back revision equals the released document digest.
