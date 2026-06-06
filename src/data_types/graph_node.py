"""Graph node data type — represents a code entity (class, function, module, file)."""

from __future__ import annotations

from enum import StrEnum as Enum

from pydantic import BaseModel, Field


class NodeKind(Enum):
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    FILE = "file"


class GraphNode(BaseModel):
    """A node in the knowledge graph representing one code entity."""

    id: str
    kind: NodeKind
    name: str
    file_path: str
    line_start: int = 0
    line_end: int = 0
    docstring: str = ""
    parent_class: str | None = None   # set for methods
    base_classes: list[str] = Field(default_factory=list)   # set for classes
    methods: list[str] = Field(default_factory=list)        # set for classes
    calls: list[str] = Field(default_factory=list)          # function/method ids this calls

    def to_dict(self) -> dict:
        return self.model_dump()

    @property
    def label(self) -> str:
        """Short display name used in the Obsidian graph."""
        return self.name if self.parent_class is None else f"{self.parent_class}.{self.name}"

    @property
    def obsidian_slug(self) -> str:
        """Filename-safe identifier for Obsidian note."""
        return self.id.replace("/", "_").replace(".", "_").replace(" ", "_")
