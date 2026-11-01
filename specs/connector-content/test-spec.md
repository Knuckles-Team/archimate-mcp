# CONN-ARCHIMATE-MCP-CONNECTOR-CONTENT — Test specification

Governing spec: [spec.md](spec.md).

| Test ID | Requirement | Proving test | Expected observation |
|---|---|---|---|
| T-001 | `CONN-ARCHIMATE-MCP-CONNECTOR-CONTENT-R001` | `tests/test_default_content_surfaces.py` | The listings include the packaged skills, ontology and prompts. |

## Rows awaiting bound tests
- `CONN-ARCHIMATE-MCP-CONNECTOR-CONTENT-R002`: planned proof `tests/test_access_contracts.py::test_competency_contracts_certified`. Expected: Each entity has a contract whose operation is the existing tool and whose recording validates against it.. Refusal: A contract naming a column absent from the ontology properties or a missing recording fails certification..
