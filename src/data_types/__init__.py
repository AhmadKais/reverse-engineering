"""Data types package — GraphNode, GraphEdge, and their enums."""

from src.data_types.graph_edge import EdgeKind, EdgeLabel, GraphEdge
from src.data_types.graph_node import GraphNode, NodeKind

__version__ = "1.00"
__all__ = ["GraphNode", "NodeKind", "GraphEdge", "EdgeKind", "EdgeLabel"]
