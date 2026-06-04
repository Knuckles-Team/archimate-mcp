"""Thin MCP wrappers around the ArchiMate model engine.

Each tool is a thin shim: it parses params, calls the corresponding
:class:`~archimate_mcp.api.api_client_archi.ArchiApi` method, and returns the
result. All authoring logic lives in ``archimate_mcp.api`` — these tools add no
business logic. Mutations are written to ``ARCHI_MODEL_PATH`` after each call
so the in-memory model and the on-disk Open Exchange file stay in sync.
"""

import json
from typing import Any

from fastmcp import FastMCP
from pydantic import Field

from archimate_mcp.auth import get_client


def _persist(client) -> None:
    """Best-effort save of the current model after a mutation."""
    try:
        client.save()
    except Exception:
        # A model with no path / read-only target should not crash the tool.
        pass


def register_archi_tools(mcp: FastMCP) -> None:
    """Register the full ArchiMate authoring tool surface."""

    @mcp.tool(tags={"model"})
    async def archi_model(
        action: str = Field(
            description=(
                "Model action. One of: 'new', 'load', 'save', "
                "'export_exchange', 'import_exchange', 'summary'."
            )
        ),
        params_json: str = Field(
            default="{}",
            description=(
                "JSON arguments, e.g. "
                '{"name": "My Model"} for new, '
                '{"path": "/tmp/m.archimate"} for load/save/export/import.'
            ),
        ),
    ) -> Any:
        """Manage the model lifecycle and Open Exchange import/export."""
        client = get_client()
        p = json.loads(params_json) if params_json else {}
        if action == "new":
            result = client.new_model(
                p.get("name", "ArchiMate Model"),
                p.get("documentation", ""),
            )
            _persist(client)
            return result
        if action == "load":
            return client.load(p.get("path"))
        if action == "save":
            return client.save(p.get("path"))
        if action == "export_exchange":
            return client.export_open_exchange(p["path"])
        if action == "import_exchange":
            result = client.import_open_exchange(p["path"])
            _persist(client)
            return result
        if action == "summary":
            return client.model_summary()
        raise ValueError(f"Unknown model action: {action!r}.")

    @mcp.tool(tags={"element"})
    async def archi_element(
        action: str = Field(
            description=(
                "Element action. One of: 'add', 'get', 'update', 'delete', "
                "'list', 'find'."
            )
        ),
        params_json: str = Field(
            default="{}",
            description=(
                "JSON arguments, e.g. "
                '{"type": "ApplicationComponent", "name": "Billing"} for add, '
                '{"id": "elem-..."} for get/delete, '
                '{"id": "elem-...", "name": "New"} for update, '
                '{"type": "Node"} or {"layer": "Business"} for list, '
                '{"name_substring": "bill"} for find.'
            ),
        ),
    ) -> Any:
        """Create, read, update, delete, list, or search elements."""
        client = get_client()
        p = json.loads(params_json) if params_json else {}
        if action == "add":
            eid = client.add_element(
                p["type"],
                p.get("name", ""),
                p.get("documentation", ""),
                p.get("properties"),
            )
            _persist(client)
            return {"id": eid}
        if action == "get":
            return client.get_element(p["id"])
        if action == "update":
            result = client.update_element(
                p["id"],
                name=p.get("name"),
                documentation=p.get("documentation"),
                properties=p.get("properties"),
                type=p.get("type"),
            )
            _persist(client)
            return result
        if action == "delete":
            result = client.delete_element(p["id"], p.get("cascade", True))
            _persist(client)
            return result
        if action == "list":
            return client.list_elements(p.get("type"), p.get("layer"))
        if action == "find":
            return client.find_elements(p["name_substring"])
        raise ValueError(f"Unknown element action: {action!r}.")

    @mcp.tool(tags={"relationship"})
    async def archi_relationship(
        action: str = Field(
            description=(
                "Relationship action. One of: 'add', 'get', 'update', "
                "'delete', 'list', 'validate'."
            )
        ),
        params_json: str = Field(
            default="{}",
            description=(
                "JSON arguments, e.g. "
                '{"type": "Serving", "source": "elem-a", "target": "elem-b"} '
                'for add, {"id": "rel-..."} for get/delete, '
                '{"type": "...", "source": "...", "target": "..."} for list, '
                '{"type": "Realization", "source_type": "ApplicationComponent",'
                ' "target_type": "ApplicationService"} for validate.'
            ),
        ),
    ) -> Any:
        """Create, read, update, delete, list, or validate relationships."""
        client = get_client()
        p = json.loads(params_json) if params_json else {}
        if action == "add":
            rid = client.add_relationship(
                p["type"],
                p["source"],
                p["target"],
                p.get("name", ""),
                p.get("documentation", ""),
                p.get("properties"),
                p.get("validate", True),
            )
            _persist(client)
            return {"id": rid}
        if action == "get":
            return client.get_relationship(p["id"])
        if action == "update":
            result = client.update_relationship(
                p["id"],
                name=p.get("name"),
                documentation=p.get("documentation"),
                properties=p.get("properties"),
            )
            _persist(client)
            return result
        if action == "delete":
            result = client.delete_relationship(p["id"])
            _persist(client)
            return result
        if action == "list":
            return client.list_relationships(
                p.get("type"), p.get("source"), p.get("target")
            )
        if action == "validate":
            return {
                "valid": client.validate_relationship(
                    p["type"], p["source_type"], p["target_type"]
                )
            }
        raise ValueError(f"Unknown relationship action: {action!r}.")

    @mcp.tool(tags={"view"})
    async def archi_view(
        action: str = Field(
            description=(
                "View action. One of: 'create', 'add_element', "
                "'add_connection', 'list', 'get'."
            )
        ),
        params_json: str = Field(
            default="{}",
            description=(
                "JSON arguments, e.g. "
                '{"name": "Layered"} for create, '
                '{"view_id": "view-...", "element_id": "elem-...", '
                '"x": 10, "y": 20, "w": 120, "h": 55} for add_element, '
                '{"view_id": "view-...", "relationship_id": "rel-..."} for '
                'add_connection, {"id": "view-..."} for get.'
            ),
        ),
    ) -> Any:
        """Create views (diagrams) and place elements/connections on them."""
        client = get_client()
        p = json.loads(params_json) if params_json else {}
        if action == "create":
            vid = client.create_view(p["name"], p.get("documentation", ""))
            _persist(client)
            return {"id": vid}
        if action == "add_element":
            nid = client.add_element_to_view(
                p["view_id"],
                p["element_id"],
                p.get("x", 0),
                p.get("y", 0),
                p.get("w", 120),
                p.get("h", 55),
            )
            _persist(client)
            return {"id": nid}
        if action == "add_connection":
            cid = client.add_connection_to_view(p["view_id"], p["relationship_id"])
            _persist(client)
            return {"id": cid}
        if action == "list":
            return client.list_views()
        if action == "get":
            return client.get_view(p["id"])
        raise ValueError(f"Unknown view action: {action!r}.")

    @mcp.tool(tags={"folder"})
    async def archi_folder(
        action: str = Field(
            description="Folder action. One of: 'add', 'move', 'list'."
        ),
        params_json: str = Field(
            default="{}",
            description=(
                "JSON arguments, e.g. "
                '{"name": "Applications", "type": "application"} for add, '
                '{"folder_id": "folder-...", "element_id": "elem-..."} for '
                "move."
            ),
        ),
    ) -> Any:
        """Manage organizations (folders) and place items in them."""
        client = get_client()
        p = json.loads(params_json) if params_json else {}
        if action == "add":
            fid = client.add_folder(p["name"], p.get("type", ""))
            _persist(client)
            return {"id": fid}
        if action == "move":
            result = client.move_to_folder(p["folder_id"], p["element_id"])
            _persist(client)
            return result
        if action == "list":
            return client.list_folders()
        raise ValueError(f"Unknown folder action: {action!r}.")

    @mcp.tool(tags={"query"})
    async def archi_query(
        action: str = Field(
            description=(
                "Query action. One of: 'neighbors', 'relationships_of', "
                "'by_type', 'element_types', 'relationship_types'."
            )
        ),
        params_json: str = Field(
            default="{}",
            description=(
                "JSON arguments, e.g. "
                '{"element_id": "elem-..."} for neighbors/relationships_of, '
                '{"type": "Node"} for by_type. element_types and '
                "relationship_types take no arguments."
            ),
        ),
    ) -> Any:
        """Traverse and introspect the model and its vocabulary."""
        client = get_client()
        p = json.loads(params_json) if params_json else {}
        if action == "neighbors":
            return client.neighbors(p["element_id"])
        if action == "relationships_of":
            return client.relationships_of(p["element_id"])
        if action == "by_type":
            return client.elements_by_type(p["type"])
        if action == "element_types":
            return client.element_types()
        if action == "relationship_types":
            return client.relationship_types()
        raise ValueError(f"Unknown query action: {action!r}.")
