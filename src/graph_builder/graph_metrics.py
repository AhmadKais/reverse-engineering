"""GraphMetrics dataclass — pre-computed graph topology metrics."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GraphMetrics:
    """Pre-computed graph metrics for quick agent consumption."""

    node_count: int
    edge_count: int
    top_hubs: list[tuple[str, float]] = field(default_factory=list)
    bridges: list[tuple[str, str]] = field(default_factory=list)
    communities: list[set[str]] = field(default_factory=list)
    betweenness: dict[str, float] = field(default_factory=dict)
    in_degree: dict[str, int] = field(default_factory=dict)
    out_degree: dict[str, int] = field(default_factory=dict)
