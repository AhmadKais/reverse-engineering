"""Navigator Agent — reads the knowledge graph and maps the architectural landscape.

Implements the 'macro-to-micro' reading strategy from Lecture 07 §10:
start with the hubs, then drill into communities, bridges, and outliers.
The agent is token-efficient: it receives a compact JSON summary, not the
full graph, so the context window stays within budget.
"""

from __future__ import annotations

import json

from src.agents.base_agent import AgentBudget, BaseAgent
from src.graph_builder.graph_generator import KnowledgeGraph

_SYSTEM_PROMPT = """\
You are the Navigator — an expert software architect specializing in reverse engineering.
Given a JSON summary of a codebase's knowledge graph, you produce a structured
architectural overview: which modules are hubs, which are isolated, how the system
is layered, and where the data flows.

Format your response as:
## Architectural Overview
<2-3 sentences on the big picture>

## Hubs (High Centrality Nodes)
<bullet list: name, role, why it's central>

## Communities
<bullet list: each community and what domain it represents>

## Data Flow Summary
<how information/control moves through the system>

## Initial Risk Signals
<list potential concerns visible from topology alone, without reading code>
"""


class NavigatorAgent(BaseAgent):
    """Maps the architectural landscape from the knowledge graph topology."""

    def __init__(self, budget: AgentBudget) -> None:
        super().__init__(
            name="Navigator",
            system_prompt=_SYSTEM_PROMPT,
            budget=budget,
            max_tokens=1500,
        )

    def navigate(self, kg: KnowledgeGraph) -> str:
        """Produce an architectural overview from the graph summary."""
        summary = kg.summary_dict()

        # Enrich with community info
        communities_preview = []
        for i, community in enumerate(kg.metrics.communities[:5], 1):
            sample_names = []
            for nid in list(community)[:4]:
                node = kg.get_node(nid)
                if node:
                    sample_names.append(node.name)
            communities_preview.append({"community": i, "size": len(community), "sample": sample_names})
        summary["communities_preview"] = communities_preview

        prompt = (
            "Analyze this knowledge graph summary of a Python codebase and produce "
            "the architectural overview:\n\n"
            f"```json\n{json.dumps(summary, indent=2)}\n```"
        )
        self.reset_history()
        return self.generate_response(prompt)
