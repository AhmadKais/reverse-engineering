"""Graph edge data type — a directed relationship between two code entities."""

from __future__ import annotations

from enum import StrEnum as Enum

from pydantic import BaseModel


class EdgeKind(Enum):
    """Three relationship types from Grphify's taxonomy."""
    EXTRACTED = "Extracted"    # Hard-coded relationship: import, call, inheritance
    INFERRED = "Inferred"      # LLM-inferred semantic relationship
    AMBIGUOUS = "Ambiguous"    # Relationship needing human verification


class EdgeLabel(Enum):
    IMPORTS = "imports"
    INHERITS = "inherits"
    CALLS = "calls"
    COMPOSES = "composes"        # holds a reference (composition)
    SIMILAR_TO = "similar_to"   # inferred semantic similarity
    MAYBE_RELATED = "maybe_related"


class GraphEdge(BaseModel):
    """A directed edge (source → target) in the knowledge graph."""

    source: str
    target: str
    kind: EdgeKind
    label: EdgeLabel
    weight: float = 1.0   # higher = stronger relationship

    def to_dict(self) -> dict:
        return self.model_dump()
