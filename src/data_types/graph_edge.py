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
    weight: float = 1.0        # legacy alias kept for backward compat
    confidence: float = 1.0    # evidence strength: 1.0=Extracted, ~0.8=Inferred, ~0.6=Ambiguous
    source_file: str = ""      # file containing this relationship (for source validation)

    def to_dict(self) -> dict:
        return self.model_dump()
