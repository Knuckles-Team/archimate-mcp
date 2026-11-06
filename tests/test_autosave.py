"""A mutating model operation writes the model file (CONN-ARCHIMATE-MCP-CONNECTOR-CONTENT-R001)."""

from archimate_mcp.api.api_client_archi import ArchiApi


def test_a_mutation_is_saved_to_the_model_file(tmp_path):
    path = tmp_path / "model.archimate"
    api = ArchiApi(model_path=str(path), autoload=False)
    api.new_model("Saved")
    api.add_element("ApplicationComponent", "CRM")
    reloaded = ArchiApi(model_path=str(path))
    assert [e["name"] for e in reloaded.find_elements("CRM")] == ["CRM"]
