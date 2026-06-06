"""Build a networkx DiGraph from parsed AST nodes and edges.

The graph captures three layers:
  Extracted — hard-coded facts (imports, calls, inheritance)
  Inferred  — pattern-based inferences (composition, shared base classes)
  Ambiguous — loose heuristic matches that need human review

This module also computes centrality metrics and community structure used
by the Navigator and Analyzer agents.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import networkx as nx

from src.data_types.graph_edge import EdgeKind, EdgeLabel, GraphEdge
from src.data_types.graph_node import GraphNode, NodeKind


@dataclass
class GraphMetrics:
    """Pre-computed graph metrics for quick agent consumption."""

    node_count: int
    edge_count: int
    # Top nodes by betweenness centrality — these are potential bottlenecks
    top_hubs: list[tuple[str, float]] = field(default_factory=list)
    # Bridges whose removal disconnects the graph — SPOF candidates
    bridges: list[tuple[str, str]] = field(default_factory=list)
    # Communities (densely connected subgraphs)
    communities: list[set[str]] = field(default_factory=list)
    # Centrality dict: node_id → score
    betweenness: dict[str, float] = field(default_factory=dict)
    in_degree: dict[str, int] = field(default_factory=dict)
    out_degree: dict[str, int] = field(default_factory=dict)


class KnowledgeGraph:
    """Wraps a networkx DiGraph and provides domain-aware query methods."""

    def __init__(self) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()
        self._nodes: dict[str, GraphNode] = {}
        self._metrics: GraphMetrics | None = None

    # ------------------------------------------------------------------

    def build(self, nodes: list[GraphNode], edges: list[GraphEdge]) -> None:
        """Populate the graph from parsed nodes and edges, then add inferred edges."""
        for node in nodes:
            self._nodes[node.id] = node
            self.graph.add_node(
                node.id,
                kind=node.kind.value,
                name=node.name,
                file=node.file_path,
                label=node.label,
            )

        known_ids = set(self._nodes.keys())
        name_index = self._build_name_index()

        for edge in edges:
            target_id = self._resolve_target(edge.target, known_ids, name_index)
            if target_id:
                self.graph.add_edge(
                    edge.source,
                    target_id,
                    kind=edge.kind.value,
                    label=edge.label.value,
                    weight=edge.weight,
                )

        self._add_inferred_edges(name_index)

    def _build_name_index(self) -> dict[str, list[str]]:
        """Map short names → list of full node ids (multiple classes can share a name)."""
        index: dict[str, list[str]] = {}
        for node_id, node in self._nodes.items():
            index.setdefault(node.name, []).append(node_id)
        return index

    def _resolve_target(self, target: str, known_ids: set[str], name_index: dict[str, list[str]]) -> str | None:
        """Try to resolve an unresolved edge target to an actual node id."""
        if target in known_ids:
            return target
        # Try the last component of a dotted name (e.g. "src.core.gatekeeper.Gatekeeper" → "Gatekeeper")
        short = target.split(".")[-1]
        candidates = name_index.get(short, [])
        if len(candidates) == 1:
            return candidates[0]
        if candidates:
            return candidates[0]   # ambiguous, take first
        return None

    def _add_inferred_edges(self, name_index: dict[str, list[str]]) -> None:
        """Heuristically infer composition relationships not visible in the AST.

        When a class holds another class as a constructor argument (detected by
        checking __init__ parameter type annotations or default values), we add
        an Inferred COMPOSES edge.  This is a best-effort approximation.
        """
        for node_id, node in self._nodes.items():
            if node.kind != NodeKind.CLASS:
                continue
            for method_name in node.methods:
                if method_name != "__init__":
                    continue
                method_id = f"{node.file_path}::{node.name}.__init__"
                method_node = self._nodes.get(method_id)
                if not method_node:
                    continue
                for callee in method_node.calls:
                    targets = name_index.get(callee, [])
                    for t in targets:
                        if t != node_id and not self.graph.has_edge(node_id, t):
                            self.graph.add_edge(
                                node_id,
                                t,
                                kind=EdgeKind.INFERRED.value,
                                label=EdgeLabel.COMPOSES.value,
                                weight=0.7,
                            )

    # ------------------------------------------------------------------

    def compute_metrics(self) -> GraphMetrics:
        """Compute and cache betweenness centrality, in/out-degree, and communities."""
        undirected = self.graph.to_undirected()

        betweenness = nx.betweenness_centrality(self.graph, normalized=True)
        in_deg = dict(self.graph.in_degree())
        out_deg = dict(self.graph.out_degree())

        top_hubs = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]

        # Bridges: edges whose removal disconnects a component
        try:
            bridge_edges = list(nx.bridges(undirected))
        except nx.NetworkXError:
            bridge_edges = []

        # Communities via greedy modularity (works on undirected)
        try:
            communities = list(nx.community.greedy_modularity_communities(undirected))
            communities_sets = [set(c) for c in communities]
        except Exception:
            communities_sets = []

        self._metrics = GraphMetrics(
            node_count=self.graph.number_of_nodes(),
            edge_count=self.graph.number_of_edges(),
            top_hubs=top_hubs,
            bridges=bridge_edges,
            communities=communities_sets,
            betweenness=betweenness,
            in_degree=in_deg,
            out_degree=out_deg,
        )
        return self._metrics

    @property
    def metrics(self) -> GraphMetrics:
        if self._metrics is None:
            return self.compute_metrics()
        return self._metrics

    def get_node(self, node_id: str) -> GraphNode | None:
        return self._nodes.get(node_id)

    def get_neighbors(self, node_id: str) -> list[str]:
        return list(self.graph.successors(node_id)) + list(self.graph.predecessors(node_id))

    def summary_dict(self) -> dict:
        """Return a JSON-serializable summary for agent consumption."""
        m = self.metrics
        return {
            "node_count": m.node_count,
            "edge_count": m.edge_count,
            "top_hubs": [
                {
                    "id": nid,
                    "name": self._nodes[nid].name if nid in self._nodes else nid,
                    "kind": self._nodes[nid].kind.value if nid in self._nodes else "unknown",
                    "betweenness": round(score, 4),
                    "in_degree": m.in_degree.get(nid, 0),
                    "out_degree": m.out_degree.get(nid, 0),
                }
                for nid, score in m.top_hubs
            ],
            "community_count": len(m.communities),
            "bridge_count": len(m.bridges),
        }
