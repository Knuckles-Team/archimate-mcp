"""Full-capability ArchiMate model engine façade.

``ArchiApi`` is the equivalent of an HTTP API client in the other ``*-mcp``
packages, but instead of talking to a remote server it drives a local
:class:`~archi_mcp.api.archimate_model.ArchiMateModel`. Agents get the full
ArchiMate authoring surface: model lifecycle, element/relationship/folder/view
CRUD, query/traversal, and Open Exchange Format import/export so the models
open directly in Archi.
"""

from __future__ import annotations

import os
from typing import Any

from archi_mcp.api.archimate_model import (
    ELEMENT_TYPES,
    LAYER_OF_TYPE,
    RELATIONSHIP_TYPES,
    ArchiMateModel,
    Element,
    Folder,
    Relationship,
    View,
    ViewConnection,
    ViewNode,
)

# Relationship validity is decided by :meth:`ArchiApi.validate_relationship`.
# A full ArchiMate derivation matrix is large; that method captures the common,
# high-signal structural rules and defaults to allowing ``Association`` (which
# ArchiMate permits between virtually any two elements). For source/target type
# pairs not otherwise constrained, the relationship is allowed.


class ArchiApi:
    """A stateful façade over a single ArchiMate model file."""

    def __init__(self, model_path: str | None = None, autoload: bool = True):
        self.model_path: str = (
            model_path or os.getenv("ARCHI_MODEL_PATH") or "./model.archimate"
        )
        self.model: ArchiMateModel = ArchiMateModel()
        if autoload and os.path.exists(self.model_path):
            try:
                self.model = ArchiMateModel.from_open_exchange(self.model_path)
            except Exception:
                # Corrupt / non-OEF file: start from an empty model.
                self.model = ArchiMateModel()

    # ------------------------------------------------------------------ #
    # Model lifecycle
    # ------------------------------------------------------------------ #
    def new_model(self, name: str = "ArchiMate Model", documentation: str = "") -> dict:
        self.model = ArchiMateModel(name=name, documentation=documentation)
        return self.model.summary()

    def load(self, path: str | None = None) -> dict:
        target = path or self.model_path
        self.model = ArchiMateModel.from_open_exchange(target)
        self.model_path = target
        return self.model.summary()

    def save(self, path: str | None = None) -> dict:
        target = path or self.model_path
        self.model.to_open_exchange(target)
        self.model_path = target
        return {"status": "saved", "path": target}

    def export_open_exchange(self, path: str) -> dict:
        self.model.to_open_exchange(path)
        return {"status": "exported", "path": path}

    def import_open_exchange(self, path: str) -> dict:
        self.model = ArchiMateModel.from_open_exchange(path)
        self.model_path = path
        return self.model.summary()

    def model_summary(self) -> dict:
        return self.model.summary()

    # ------------------------------------------------------------------ #
    # Elements
    # ------------------------------------------------------------------ #
    def add_element(
        self,
        type: str,
        name: str = "",
        documentation: str = "",
        properties: dict[str, str] | None = None,
    ) -> str:
        if type not in ELEMENT_TYPES:
            raise ValueError(
                f"Unknown element type {type!r}. "
                f"See archi_query/element_types for the vocabulary."
            )
        elem = Element(
            type=type,
            name=name,
            documentation=documentation,
            properties=dict(properties or {}),
        )
        self.model.elements[elem.id] = elem
        return elem.id

    def get_element(self, element_id: str) -> dict:
        elem = self.model.elements.get(element_id)
        if elem is None:
            raise KeyError(f"No element with id {element_id!r}.")
        return elem.to_dict()

    def update_element(
        self,
        element_id: str,
        name: str | None = None,
        documentation: str | None = None,
        properties: dict[str, str] | None = None,
        type: str | None = None,
    ) -> dict:
        elem = self.model.elements.get(element_id)
        if elem is None:
            raise KeyError(f"No element with id {element_id!r}.")
        if name is not None:
            elem.name = name
        if documentation is not None:
            elem.documentation = documentation
        if type is not None:
            if type not in ELEMENT_TYPES:
                raise ValueError(f"Unknown element type {type!r}.")
            elem.type = type
        if properties is not None:
            elem.properties.update(properties)
        return elem.to_dict()

    def delete_element(self, element_id: str, cascade: bool = True) -> dict:
        if element_id not in self.model.elements:
            raise KeyError(f"No element with id {element_id!r}.")
        del self.model.elements[element_id]
        removed_rels = []
        if cascade:
            for rid in list(self.model.relationships):
                rel = self.model.relationships[rid]
                if rel.source == element_id or rel.target == element_id:
                    removed_rels.append(rid)
                    del self.model.relationships[rid]
        # Remove from folders.
        for folder in self.model.folders.values():
            if element_id in folder.children:
                folder.children.remove(element_id)
        return {"deleted": element_id, "removed_relationships": removed_rels}

    def list_elements(
        self, type: str | None = None, layer: str | None = None
    ) -> list[dict]:
        out = []
        for elem in self.model.elements.values():
            if type and elem.type != type:
                continue
            if layer and LAYER_OF_TYPE.get(elem.type) != layer:
                continue
            out.append(elem.to_dict())
        return out

    def find_elements(self, name_substring: str) -> list[dict]:
        needle = name_substring.lower()
        return [
            e.to_dict()
            for e in self.model.elements.values()
            if needle in e.name.lower()
        ]

    # ------------------------------------------------------------------ #
    # Relationships
    # ------------------------------------------------------------------ #
    def validate_relationship(
        self, type: str, source_type: str, target_type: str
    ) -> bool:
        """Return True if ``type`` is plausible between the given endpoints.

        Implements common ArchiMate structural rules and defaults to allowing
        ``Association`` (and any pair not otherwise constrained).
        """
        if type not in RELATIONSHIP_TYPES:
            return False
        if type == "Association":
            return True
        # Specialization requires same layer / compatible concepts.
        if type == "Specialization":
            return (
                LAYER_OF_TYPE.get(source_type) == LAYER_OF_TYPE.get(target_type)
                and source_type == target_type
            )
        # Realization: a more concrete element realizes a more abstract one
        # (e.g. ApplicationComponent realizes ApplicationService / Requirement).
        if type == "Realization":
            abstract = {
                "BusinessService",
                "ApplicationService",
                "TechnologyService",
                "Requirement",
                "Goal",
                "Capability",
                "CourseOfAction",
                "Contract",
            }
            return target_type in abstract
        # Assignment typically connects an active structure to behavior or
        # an interface (actor->role, role->process, node->artifact, ...).
        if type == "Assignment":
            return True
        # Structural composition/aggregation: same layer is the common case.
        if type in {"Composition", "Aggregation"}:
            return LAYER_OF_TYPE.get(source_type) == LAYER_OF_TYPE.get(target_type)
        # Dynamic / dependency relationships are broadly permitted.
        if type in {"Serving", "Access", "Influence", "Triggering", "Flow"}:
            return True
        return True

    def add_relationship(
        self,
        type: str,
        source: str,
        target: str,
        name: str = "",
        documentation: str = "",
        properties: dict[str, str] | None = None,
        validate: bool = True,
    ) -> str:
        if type not in RELATIONSHIP_TYPES:
            raise ValueError(f"Unknown relationship type {type!r}.")
        src = self.model.elements.get(source)
        tgt = self.model.elements.get(target)
        if src is None:
            raise KeyError(f"Source element {source!r} does not exist.")
        if tgt is None:
            raise KeyError(f"Target element {target!r} does not exist.")
        if validate and not self.validate_relationship(type, src.type, tgt.type):
            raise ValueError(f"{type} is not valid between {src.type} and {tgt.type}.")
        rel = Relationship(
            type=type,
            source=source,
            target=target,
            name=name,
            documentation=documentation,
            properties=dict(properties or {}),
        )
        self.model.relationships[rel.id] = rel
        return rel.id

    def get_relationship(self, relationship_id: str) -> dict:
        rel = self.model.relationships.get(relationship_id)
        if rel is None:
            raise KeyError(f"No relationship with id {relationship_id!r}.")
        return rel.to_dict()

    def update_relationship(
        self,
        relationship_id: str,
        name: str | None = None,
        documentation: str | None = None,
        properties: dict[str, str] | None = None,
    ) -> dict:
        rel = self.model.relationships.get(relationship_id)
        if rel is None:
            raise KeyError(f"No relationship with id {relationship_id!r}.")
        if name is not None:
            rel.name = name
        if documentation is not None:
            rel.documentation = documentation
        if properties is not None:
            rel.properties.update(properties)
        return rel.to_dict()

    def delete_relationship(self, relationship_id: str) -> dict:
        if relationship_id not in self.model.relationships:
            raise KeyError(f"No relationship with id {relationship_id!r}.")
        del self.model.relationships[relationship_id]
        return {"deleted": relationship_id}

    def list_relationships(
        self,
        type: str | None = None,
        source: str | None = None,
        target: str | None = None,
    ) -> list[dict]:
        out = []
        for rel in self.model.relationships.values():
            if type and rel.type != type:
                continue
            if source and rel.source != source:
                continue
            if target and rel.target != target:
                continue
            out.append(rel.to_dict())
        return out

    # ------------------------------------------------------------------ #
    # Folders / organizations
    # ------------------------------------------------------------------ #
    def add_folder(self, name: str, type: str = "") -> str:
        folder = Folder(name=name, type=type)
        self.model.folders[folder.id] = folder
        return folder.id

    def move_to_folder(self, folder_id: str, element_id: str) -> dict:
        folder = self.model.folders.get(folder_id)
        if folder is None:
            raise KeyError(f"No folder with id {folder_id!r}.")
        if (
            element_id not in self.model.elements
            and element_id not in self.model.relationships
            and element_id not in self.model.views
        ):
            raise KeyError(f"No model item with id {element_id!r}.")
        # Remove from other folders first.
        for other in self.model.folders.values():
            if element_id in other.children:
                other.children.remove(element_id)
        if element_id not in folder.children:
            folder.children.append(element_id)
        return folder.to_dict()

    def list_folders(self) -> list[dict]:
        return [f.to_dict() for f in self.model.folders.values()]

    # ------------------------------------------------------------------ #
    # Views (diagrams)
    # ------------------------------------------------------------------ #
    def create_view(self, name: str, documentation: str = "") -> str:
        view = View(name=name, documentation=documentation)
        self.model.views[view.id] = view
        return view.id

    def add_element_to_view(
        self,
        view_id: str,
        element_id: str,
        x: int = 0,
        y: int = 0,
        w: int = 120,
        h: int = 55,
    ) -> str:
        view = self.model.views.get(view_id)
        if view is None:
            raise KeyError(f"No view with id {view_id!r}.")
        if element_id not in self.model.elements:
            raise KeyError(f"No element with id {element_id!r}.")
        node = ViewNode(element_ref=element_id, x=x, y=y, w=w, h=h)
        view.nodes.append(node)
        return node.id

    def add_connection_to_view(self, view_id: str, relationship_id: str) -> str:
        view = self.model.views.get(view_id)
        if view is None:
            raise KeyError(f"No view with id {view_id!r}.")
        rel = self.model.relationships.get(relationship_id)
        if rel is None:
            raise KeyError(f"No relationship with id {relationship_id!r}.")
        # Best-effort: bind to existing nodes for the endpoints.
        src_node = next((n.id for n in view.nodes if n.element_ref == rel.source), "")
        tgt_node = next((n.id for n in view.nodes if n.element_ref == rel.target), "")
        conn = ViewConnection(
            relationship_ref=relationship_id,
            source_node=src_node,
            target_node=tgt_node,
        )
        view.connections.append(conn)
        return conn.id

    def list_views(self) -> list[dict]:
        return [v.to_dict() for v in self.model.views.values()]

    def get_view(self, view_id: str) -> dict:
        view = self.model.views.get(view_id)
        if view is None:
            raise KeyError(f"No view with id {view_id!r}.")
        return view.to_dict()

    # ------------------------------------------------------------------ #
    # Query / traversal
    # ------------------------------------------------------------------ #
    def relationships_of(self, element_id: str) -> list[dict]:
        return [
            r.to_dict()
            for r in self.model.relationships.values()
            if r.source == element_id or r.target == element_id
        ]

    def neighbors(self, element_id: str) -> list[dict]:
        out: list[dict] = []
        seen: set[str] = set()
        for rel in self.model.relationships.values():
            other: str | None = None
            if rel.source == element_id:
                other = rel.target
            elif rel.target == element_id:
                other = rel.source
            if other and other not in seen and other in self.model.elements:
                seen.add(other)
                neighbor = self.model.elements[other].to_dict()
                neighbor["via"] = {"relationship_id": rel.id, "type": rel.type}
                out.append(neighbor)
        return out

    def elements_by_type(self, type: str) -> list[dict]:
        return self.list_elements(type=type)

    # ------------------------------------------------------------------ #
    # Vocabulary helpers
    # ------------------------------------------------------------------ #
    def element_types(self) -> dict[str, Any]:
        from archi_mcp.api.archimate_model import ELEMENT_TYPES_BY_LAYER

        return {
            "by_layer": ELEMENT_TYPES_BY_LAYER,
            "all": sorted(ELEMENT_TYPES),
        }

    def relationship_types(self) -> list[str]:
        return sorted(RELATIONSHIP_TYPES)
