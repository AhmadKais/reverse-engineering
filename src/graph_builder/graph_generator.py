"""Build a networkx DiGraph from parsed AST nodes and edges.

Three edge layers: Extracted (hard facts), Inferred (pattern-based), Ambiguous (heuristic).
Centrality metrics and community structure are computed here for agent consumption.
"""

from __future__ import annotations

import networkx as nx

from src.data_types.graph_edge import GraphEdge
from src.data_types.graph_node import GraphNode
from src.graph_builder.edge_inferrer import infer_composition_edges
from src.graph_builder.graph_metrics import GraphMetrics


class KnowledgeGraph:
    """Wraps a networkx DiGraph and provides domain-aware query methods."""

    def __init__(self) -> None:
        self.graph: nx.DiGraph = nx.DiGraph()
        self._nodes: dict[str, GraphNode] = {}
        self._metrics: GraphMetrics | None = None

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
                    weight=edge.confidence,
                    confidence=edge.confidence,
                    source_file=edge.source_file,
                )

        self._add_inferred_edges(name_index)

    def _build_name_index(self) -> dict[str, list[str]]:
        index: dict[str, list[str]] = {}
        for node_id, node in self._nodes.items():
            index.setdefault(node.name, []).append(node_id)
        return index

    def _resolve_target(
        self, target: str, known_ids: set[str], name_index: dict[str, list[str]]
    ) -> str | None:
        if target in known_ids:
            return target
        short = target.split(".")[-1]
        candidates = name_index.get(short, [])
        if candidates:
            return candidates[0]
        return None

    def _add_inferred_edges(self, name_index: dict[str, list[str]]) -> None:
        infer_composition_edges(self.graph, self._nodes, name_index)

    def compute_metrics(self) -> GraphMetrics:
        """Compute and cache betweenness centrality, in/out-degree, and communities."""
        undirected = self.graph.to_undirected()
        betweenness = nx.betweenness_centrality(self.graph, normalized=True)
        in_deg = dict(self.graph.in_degree())
        out_deg = dict(self.graph.out_degree())
        top_hubs = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]

        try:
            bridge_edges = list(nx.bridges(undirected))
        except nx.NetworkXError:
            bridge_edges = []

        try:
            communities_sets = [set(c) for c in nx.community.greedy_modularity_communities(undirected)]
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
