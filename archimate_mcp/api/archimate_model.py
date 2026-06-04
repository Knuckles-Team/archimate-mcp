"""In-memory ArchiMate 3.x model and Open Exchange Format (de)serialization.

This module is the heart of ``archimate-mcp``. Archi (the open-source ArchiMate
modeling tool) has no native server API, so instead of an HTTP client this
package ships a self-contained ArchiMate model engine that agents can drive.

The engine round-trips through the Open Group **ArchiMate Model Exchange File
Format** (namespace ``http://www.opengroup.org/xsd/archimate/3.0/``) — the
interoperable XML that Archi reads and writes via
*File > Import/Export > "Model Exchange File Format"*. Only the Python
standard library (``xml.etree.ElementTree``) is used, so there is no lxml
build dependency.
"""

from __future__ import annotations

import uuid
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from typing import Any

# --------------------------------------------------------------------------- #
# Vocabulary — ArchiMate 3.x element types, grouped by layer.
# --------------------------------------------------------------------------- #
ELEMENT_TYPES_BY_LAYER: dict[str, list[str]] = {
    "Strategy": [
        "Resource",
        "Capability",
        "CourseOfAction",
        "ValueStream",
    ],
    "Business": [
        "BusinessActor",
        "BusinessRole",
        "BusinessCollaboration",
        "BusinessInterface",
        "BusinessProcess",
        "BusinessFunction",
        "BusinessInteraction",
        "BusinessEvent",
        "BusinessService",
        "BusinessObject",
        "Contract",
        "Representation",
        "Product",
    ],
    "Application": [
        "ApplicationComponent",
        "ApplicationCollaboration",
        "ApplicationInterface",
        "ApplicationFunction",
        "ApplicationInteraction",
        "ApplicationProcess",
        "ApplicationEvent",
        "ApplicationService",
        "DataObject",
    ],
    "Technology": [
        "Node",
        "Device",
        "SystemSoftware",
        "TechnologyCollaboration",
        "TechnologyInterface",
        "Path",
        "CommunicationNetwork",
        "TechnologyFunction",
        "TechnologyProcess",
        "TechnologyInteraction",
        "TechnologyEvent",
        "TechnologyService",
        "Artifact",
    ],
    "Physical": [
        "Equipment",
        "Facility",
        "DistributionNetwork",
        "Material",
    ],
    "Motivation": [
        "Stakeholder",
        "Driver",
        "Assessment",
        "Goal",
        "Outcome",
        "Principle",
        "Requirement",
        "Constraint",
        "Meaning",
        "Value",
    ],
    "Implementation": [
        "WorkPackage",
        "Deliverable",
        "ImplementationEvent",
        "Plateau",
        "Gap",
    ],
    "Other": [
        "Location",
        "Grouping",
        "Junction",
    ],
}

ELEMENT_TYPES: set[str] = {
    t for types in ELEMENT_TYPES_BY_LAYER.values() for t in types
}

#: Map each element type to its layer name for quick lookup.
LAYER_OF_TYPE: dict[str, str] = {
    t: layer for layer, types in ELEMENT_TYPES_BY_LAYER.items() for t in types
}

#: ArchiMate relationship types.
RELATIONSHIP_TYPES: set[str] = {
    "Composition",
    "Aggregation",
    "Assignment",
    "Realization",
    "Serving",
    "Access",
    "Influence",
    "Triggering",
    "Flow",
    "Specialization",
    "Association",
    "Junction",
}

# Open Exchange Format namespaces.
OEF_NS = "http://www.opengroup.org/xsd/archimate/3.0/"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
LANG_NS = "http://www.w3.org/XML/1998/namespace"


def _new_id(prefix: str = "id") -> str:
    """Return a fresh, Archi-compatible identifier."""
    return f"{prefix}-{uuid.uuid4().hex}"


# --------------------------------------------------------------------------- #
# Data classes
# --------------------------------------------------------------------------- #
@dataclass
class Element:
    """An ArchiMate element (a node in the model)."""

    type: str
    name: str = ""
    documentation: str = ""
    id: str = field(default_factory=lambda: _new_id("elem"))
    properties: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "name": self.name,
            "documentation": self.documentation,
            "properties": dict(self.properties),
            "layer": LAYER_OF_TYPE.get(self.type, "Other"),
        }


@dataclass
class Relationship:
    """An ArchiMate relationship between two elements."""

    type: str
    source: str
    target: str
    name: str = ""
    documentation: str = ""
    id: str = field(default_factory=lambda: _new_id("rel"))
    properties: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "source": self.source,
            "target": self.target,
            "name": self.name,
            "documentation": self.documentation,
            "properties": dict(self.properties),
        }


@dataclass
class Folder:
    """A model organization (folder)."""

    name: str
    type: str = ""
    id: str = field(default_factory=lambda: _new_id("folder"))
    children: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "children": list(self.children),
        }


@dataclass
class ViewNode:
    """A visual node placed on a diagram referencing a model element."""

    element_ref: str
    x: int = 0
    y: int = 0
    w: int = 120
    h: int = 55
    id: str = field(default_factory=lambda: _new_id("node"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "element_ref": self.element_ref,
            "x": self.x,
            "y": self.y,
            "w": self.w,
            "h": self.h,
        }


@dataclass
class ViewConnection:
    """A visual connection on a diagram referencing a model relationship."""

    relationship_ref: str
    source_node: str = ""
    target_node: str = ""
    id: str = field(default_factory=lambda: _new_id("conn"))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "relationship_ref": self.relationship_ref,
            "source_node": self.source_node,
            "target_node": self.target_node,
        }


@dataclass
class View:
    """A view (diagram) of the model."""

    name: str
    documentation: str = ""
    id: str = field(default_factory=lambda: _new_id("view"))
    nodes: list[ViewNode] = field(default_factory=list)
    connections: list[ViewConnection] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "documentation": self.documentation,
            "nodes": [n.to_dict() for n in self.nodes],
            "connections": [c.to_dict() for c in self.connections],
        }


# --------------------------------------------------------------------------- #
# Model
# --------------------------------------------------------------------------- #
class ArchiMateModel:
    """An in-memory ArchiMate model with Open Exchange (de)serialization."""

    def __init__(self, name: str = "ArchiMate Model", documentation: str = ""):
        self.id: str = _new_id("model")
        self.name: str = name
        self.documentation: str = documentation
        self.elements: dict[str, Element] = {}
        self.relationships: dict[str, Relationship] = {}
        self.folders: dict[str, Folder] = {}
        self.views: dict[str, View] = {}

    # ------------------------------------------------------------------ #
    # Summary
    # ------------------------------------------------------------------ #
    def summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "documentation": self.documentation,
            "counts": {
                "elements": len(self.elements),
                "relationships": len(self.relationships),
                "folders": len(self.folders),
                "views": len(self.views),
            },
        }

    # ------------------------------------------------------------------ #
    # Open Exchange Format serialization
    # ------------------------------------------------------------------ #
    def to_open_exchange(self, path: str) -> str:
        """Serialize the model to an Open Exchange Format XML file."""
        ET.register_namespace("", OEF_NS)
        ET.register_namespace("xsi", XSI_NS)

        model = ET.Element(f"{{{OEF_NS}}}model")
        model.set(
            f"{{{XSI_NS}}}schemaLocation",
            f"{OEF_NS} {OEF_NS}archimate3_Model.xsd",
        )
        model.set("identifier", self.id)

        name_el = ET.SubElement(model, f"{{{OEF_NS}}}name")
        name_el.set(f"{{{LANG_NS}}}lang", "en")
        name_el.text = self.name

        if self.documentation:
            doc_el = ET.SubElement(model, f"{{{OEF_NS}}}documentation")
            doc_el.set(f"{{{LANG_NS}}}lang", "en")
            doc_el.text = self.documentation

        # Property definitions: collect distinct property keys.
        prop_keys: list[str] = []
        for holder in list(self.elements.values()) + list(self.relationships.values()):
            for key in holder.properties:
                if key not in prop_keys:
                    prop_keys.append(key)
        prop_def_id: dict[str, str] = {}
        if prop_keys:
            defs = ET.SubElement(model, f"{{{OEF_NS}}}propertyDefinitions")
            for i, key in enumerate(prop_keys, start=1):
                pid = f"propid-{i}"
                prop_def_id[key] = pid
                pdef = ET.SubElement(defs, f"{{{OEF_NS}}}propertyDefinition")
                pdef.set("identifier", pid)
                pdef.set("type", "string")
                pname = ET.SubElement(pdef, f"{{{OEF_NS}}}name")
                pname.text = key

        # Elements
        if self.elements:
            elements_el = ET.SubElement(model, f"{{{OEF_NS}}}elements")
            for elem in self.elements.values():
                self._write_concept(elements_el, "element", elem, prop_def_id)

        # Relationships
        if self.relationships:
            rels_el = ET.SubElement(model, f"{{{OEF_NS}}}relationships")
            for rel in self.relationships.values():
                node = self._write_concept(rels_el, "relationship", rel, prop_def_id)
                node.set("source", rel.source)
                node.set("target", rel.target)

        # Organizations (folders)
        if self.folders:
            orgs_el = ET.SubElement(model, f"{{{OEF_NS}}}organizations")
            for folder in self.folders.values():
                item = ET.SubElement(orgs_el, f"{{{OEF_NS}}}item")
                label = ET.SubElement(item, f"{{{OEF_NS}}}label")
                label.set(f"{{{LANG_NS}}}lang", "en")
                label.text = folder.name
                item.set("identifier", folder.id)
                if folder.type:
                    item.set("type", folder.type)
                for child_ref in folder.children:
                    child = ET.SubElement(item, f"{{{OEF_NS}}}item")
                    child.set("identifierRef", child_ref)

        # Views / diagrams
        if self.views:
            views_el = ET.SubElement(model, f"{{{OEF_NS}}}views")
            diagrams_el = ET.SubElement(views_el, f"{{{OEF_NS}}}diagrams")
            for view in self.views.values():
                self._write_view(diagrams_el, view)

        tree = ET.ElementTree(model)
        ET.indent(tree, space="  ")
        tree.write(path, encoding="UTF-8", xml_declaration=True)
        return path

    def _write_concept(
        self,
        parent: ET.Element,
        tag: str,
        concept: Element | Relationship,
        prop_def_id: dict[str, str],
    ) -> ET.Element:
        node = ET.SubElement(parent, f"{{{OEF_NS}}}{tag}")
        node.set("identifier", concept.id)
        node.set(f"{{{XSI_NS}}}type", concept.type)
        if concept.name:
            name_el = ET.SubElement(node, f"{{{OEF_NS}}}name")
            name_el.set(f"{{{LANG_NS}}}lang", "en")
            name_el.text = concept.name
        if concept.documentation:
            doc_el = ET.SubElement(node, f"{{{OEF_NS}}}documentation")
            doc_el.set(f"{{{LANG_NS}}}lang", "en")
            doc_el.text = concept.documentation
        if concept.properties:
            props = ET.SubElement(node, f"{{{OEF_NS}}}properties")
            for key, value in concept.properties.items():
                prop = ET.SubElement(props, f"{{{OEF_NS}}}property")
                prop.set("propertyDefinitionRef", prop_def_id.get(key, key))
                val = ET.SubElement(prop, f"{{{OEF_NS}}}value")
                val.set(f"{{{LANG_NS}}}lang", "en")
                val.text = value
        return node

    def _write_view(self, parent: ET.Element, view: View) -> None:
        diagram = ET.SubElement(parent, f"{{{OEF_NS}}}view")
        diagram.set("identifier", view.id)
        diagram.set(f"{{{XSI_NS}}}type", "Diagram")
        name_el = ET.SubElement(diagram, f"{{{OEF_NS}}}name")
        name_el.set(f"{{{LANG_NS}}}lang", "en")
        name_el.text = view.name
        if view.documentation:
            doc_el = ET.SubElement(diagram, f"{{{OEF_NS}}}documentation")
            doc_el.set(f"{{{LANG_NS}}}lang", "en")
            doc_el.text = view.documentation
        for vn in view.nodes:
            node_el = ET.SubElement(diagram, f"{{{OEF_NS}}}node")
            node_el.set("identifier", vn.id)
            node_el.set("elementRef", vn.element_ref)
            node_el.set(f"{{{XSI_NS}}}type", "Element")
            node_el.set("x", str(vn.x))
            node_el.set("y", str(vn.y))
            node_el.set("w", str(vn.w))
            node_el.set("h", str(vn.h))
        for vc in view.connections:
            conn_el = ET.SubElement(diagram, f"{{{OEF_NS}}}connection")
            conn_el.set("identifier", vc.id)
            conn_el.set("relationshipRef", vc.relationship_ref)
            conn_el.set(f"{{{XSI_NS}}}type", "Relationship")
            if vc.source_node:
                conn_el.set("source", vc.source_node)
            if vc.target_node:
                conn_el.set("target", vc.target_node)

    # ------------------------------------------------------------------ #
    # Open Exchange Format deserialization
    # ------------------------------------------------------------------ #
    @classmethod
    def from_open_exchange(cls, path: str) -> ArchiMateModel:
        """Load a model from an Open Exchange Format XML file."""
        tree = ET.parse(path)
        root = tree.getroot()
        model = cls()
        model.id = root.get("identifier") or model.id

        name_el = root.find(f"{{{OEF_NS}}}name")
        if name_el is not None and name_el.text:
            model.name = name_el.text
        doc_el = root.find(f"{{{OEF_NS}}}documentation")
        if doc_el is not None and doc_el.text:
            model.documentation = doc_el.text

        # Property definition id -> name lookup.
        prop_names: dict[str, str] = {}
        defs = root.find(f"{{{OEF_NS}}}propertyDefinitions")
        if defs is not None:
            for pdef in defs.findall(f"{{{OEF_NS}}}propertyDefinition"):
                pid = pdef.get("identifier", "")
                pn = pdef.find(f"{{{OEF_NS}}}name")
                prop_names[pid] = pn.text if pn is not None and pn.text else pid

        def _read_props(node: ET.Element) -> dict[str, str]:
            out: dict[str, str] = {}
            props = node.find(f"{{{OEF_NS}}}properties")
            if props is None:
                return out
            for prop in props.findall(f"{{{OEF_NS}}}property"):
                ref = prop.get("propertyDefinitionRef", "")
                key = prop_names.get(ref, ref)
                val = prop.find(f"{{{OEF_NS}}}value")
                out[key] = val.text or "" if val is not None else ""
            return out

        def _text(node: ET.Element, tag: str) -> str:
            el = node.find(f"{{{OEF_NS}}}{tag}")
            return el.text or "" if el is not None and el.text else ""

        # Elements
        elements_el = root.find(f"{{{OEF_NS}}}elements")
        if elements_el is not None:
            for el in elements_el.findall(f"{{{OEF_NS}}}element"):
                elem = Element(
                    type=el.get(f"{{{XSI_NS}}}type", ""),
                    name=_text(el, "name"),
                    documentation=_text(el, "documentation"),
                    id=el.get("identifier", _new_id("elem")),
                    properties=_read_props(el),
                )
                model.elements[elem.id] = elem

        # Relationships
        rels_el = root.find(f"{{{OEF_NS}}}relationships")
        if rels_el is not None:
            for rl in rels_el.findall(f"{{{OEF_NS}}}relationship"):
                rel = Relationship(
                    type=rl.get(f"{{{XSI_NS}}}type", ""),
                    source=rl.get("source", ""),
                    target=rl.get("target", ""),
                    name=_text(rl, "name"),
                    documentation=_text(rl, "documentation"),
                    id=rl.get("identifier", _new_id("rel")),
                    properties=_read_props(rl),
                )
                model.relationships[rel.id] = rel

        # Organizations (folders)
        orgs_el = root.find(f"{{{OEF_NS}}}organizations")
        if orgs_el is not None:
            for item in orgs_el.findall(f"{{{OEF_NS}}}item"):
                # Top-level items with a label are folders.
                label = item.find(f"{{{OEF_NS}}}label")
                if label is None:
                    continue
                folder = Folder(
                    name=label.text or "",
                    type=item.get("type", ""),
                    id=item.get("identifier", _new_id("folder")),
                )
                for child in item.findall(f"{{{OEF_NS}}}item"):
                    ref = child.get("identifierRef")
                    if ref:
                        folder.children.append(ref)
                model.folders[folder.id] = folder

        # Views / diagrams
        views_el = root.find(f"{{{OEF_NS}}}views")
        if views_el is not None:
            diagrams_el = views_el.find(f"{{{OEF_NS}}}diagrams")
            if diagrams_el is not None:
                for dv in diagrams_el.findall(f"{{{OEF_NS}}}view"):
                    view = View(
                        name=_text(dv, "name"),
                        documentation=_text(dv, "documentation"),
                        id=dv.get("identifier", _new_id("view")),
                    )
                    for nd in dv.findall(f"{{{OEF_NS}}}node"):
                        view.nodes.append(
                            ViewNode(
                                element_ref=nd.get("elementRef", ""),
                                x=int(nd.get("x", "0") or 0),
                                y=int(nd.get("y", "0") or 0),
                                w=int(nd.get("w", "120") or 120),
                                h=int(nd.get("h", "55") or 55),
                                id=nd.get("identifier", _new_id("node")),
                            )
                        )
                    for cn in dv.findall(f"{{{OEF_NS}}}connection"):
                        view.connections.append(
                            ViewConnection(
                                relationship_ref=cn.get("relationshipRef", ""),
                                source_node=cn.get("source", ""),
                                target_node=cn.get("target", ""),
                                id=cn.get("identifier", _new_id("conn")),
                            )
                        )
                    model.views[view.id] = view

        return model
