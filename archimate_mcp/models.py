"""Pydantic models for ArchiMate authoring operations."""

from pydantic import BaseModel, Field


class ElementSpec(BaseModel):
    """An ArchiMate element to create or address."""

    type: str = Field(
        description="ArchiMate element type, e.g. 'ApplicationComponent'."
    )
    name: str = Field(default="", description="Element display name.")
    documentation: str = Field(
        default="", description="Free-text documentation for the element."
    )
    properties: dict[str, str] = Field(
        default_factory=dict, description="Custom key/value properties."
    )


class RelationshipSpec(BaseModel):
    """An ArchiMate relationship to create between two elements."""

    type: str = Field(description="ArchiMate relationship type, e.g. 'Serving'.")
    source: str = Field(description="Source element id.")
    target: str = Field(description="Target element id.")
    name: str = Field(default="", description="Optional relationship name.")
    documentation: str = Field(
        default="", description="Free-text documentation for the relationship."
    )
    properties: dict[str, str] = Field(
        default_factory=dict, description="Custom key/value properties."
    )
