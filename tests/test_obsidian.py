"""Tests for ObsidianExporter and NavigatorAgent."""

from __future__ import annotations

import json
import tempfile
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.agents.base_agent import AgentBudget
from src.graph_builder.ast_parser import parse_file
from src.graph_builder.graph_generator import KnowledgeGraph
from src.graph_builder.obsidian_exporter import ObsidianExporter


def _write_py(content: str, tmpdir: str, filename: str = "mod.py") -> str:
    path = str(Path(tmpdir) / filename)
    Path(path).write_text(textwrap.dedent(content), encoding="utf-8")
    return path


def _make_simple_kg(source: str = "") -> KnowledgeGraph:
    if source:
        with tempfile.TemporaryDirectory() as d:
            nodes, edges = parse_file(_write_py(source, d))
    else:
        nodes, edges = [], []
    kg = KnowledgeGraph()
    kg.build(nodes, edges)
    kg.compute_metrics()
    return kg


class TestObsidianExporter:
    @pytest.fixture
    def simple_kg(self):
        return _make_simple_kg("""
            class Alpha:
                def run(self):
                    pass
            class Beta(Alpha):
                pass
        """)

    def test_graph_json_has_correct_meta_counts(self, simple_kg, tmp_path):
        ObsidianExporter(str(tmp_path)).export(simple_kg)
        data = json.loads((tmp_path / "graph.json").read_text(encoding="utf-8"))
        assert data["meta"]["node_count"] == len(data["nodes"])
        assert data["meta"]["edge_count"] == len(data["edges"])

    def test_graph_json_nodes_have_required_fields(self, simple_kg, tmp_path):
        ObsidianExporter(str(tmp_path)).export(simple_kg)
        data = json.loads((tmp_path / "graph.json").read_text(encoding="utf-8"))
        for node in data["nodes"]:
            assert "id" in node
            assert "kind" in node
            assert "betweenness" in node

    def test_hot_md_has_betweenness_header(self, simple_kg, tmp_path):
        ObsidianExporter(str(tmp_path)).export(simple_kg)
        hot = (tmp_path / "hot.md").read_text(encoding="utf-8")
        assert "Betweenness" in hot

    def test_hot_md_is_markdown_table(self, simple_kg, tmp_path):
        ObsidianExporter(str(tmp_path)).export(simple_kg)
        hot = (tmp_path / "hot.md").read_text(encoding="utf-8")
        lines_with_pipe = [l for l in hot.splitlines() if "|" in l]
        assert len(lines_with_pipe) >= 2

    def test_index_md_has_classes_section(self, simple_kg, tmp_path):
        ObsidianExporter(str(tmp_path)).export(simple_kg)
        index = (tmp_path / "index.md").read_text(encoding="utf-8")
        assert "Class" in index

    def test_node_notes_created_for_every_node(self, simple_kg, tmp_path):
        ObsidianExporter(str(tmp_path)).export(simple_kg)
        notes = list((tmp_path / "nodes").glob("*.md"))
        assert len(notes) == simple_kg.graph.number_of_nodes()

    def test_node_notes_contain_kind_line(self, simple_kg, tmp_path):
        ObsidianExporter(str(tmp_path)).export(simple_kg)
        for note in (tmp_path / "nodes").glob("*.md"):
            assert "**Kind**" in note.read_text(encoding="utf-8")

    def test_export_empty_graph_does_not_crash(self, tmp_path):
        kg = KnowledgeGraph()
        kg.build([], [])
        kg.compute_metrics()
        ObsidianExporter(str(tmp_path)).export(kg)
        assert (tmp_path / "graph.json").exists()
        assert (tmp_path / "hot.md").exists()
        assert (tmp_path / "index.md").exists()

    def test_graph_html_is_generated(self, simple_kg, tmp_path):
        ObsidianExporter(str(tmp_path)).export(simple_kg)
        html_file = tmp_path / "graph.html"
        assert html_file.exists()
        content = html_file.read_text(encoding="utf-8")
        assert "vis.Network" in content
        assert "Knowledge Graph" in content

    def test_graph_html_embeds_node_data(self, simple_kg, tmp_path):
        ObsidianExporter(str(tmp_path)).export(simple_kg)
        content = (tmp_path / "graph.html").read_text(encoding="utf-8")
        assert "Alpha" in content or "Beta" in content

    def test_graph_json_edges_have_confidence_and_source_file(self, tmp_path):
        kg = _make_simple_kg("""
            class A:
                pass
            class B(A):
                pass
        """)
        ObsidianExporter(str(tmp_path)).export(kg)
        data = json.loads((tmp_path / "graph.json").read_text(encoding="utf-8"))
        for edge in data["edges"]:
            assert "confidence" in edge
            assert "source_file" in edge

    def test_node_notes_with_inheritance_show_inherits_from(self, tmp_path):
        kg = _make_simple_kg("""
            class Parent:
                pass
            class Child(Parent):
                pass
        """)
        ObsidianExporter(str(tmp_path)).export(kg)
        all_text = "\n".join(n.read_text(encoding="utf-8") for n in (tmp_path / "nodes").glob("*.md"))
        assert "Inherits From" in all_text


class TestNavigatorAgent:
    def test_navigate_calls_llm_with_summary(self):
        from src.agents.navigator_agent import NavigatorAgent

        budget = AgentBudget(50_000)
        kg = _make_simple_kg("class Hub:\n    def run(self):\n        pass\n")

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="## Architectural Overview\nSimple module.")]
        mock_response.usage.input_tokens = 100
        mock_response.usage.output_tokens = 30

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            agent = NavigatorAgent(budget)
            with patch.object(agent._client.messages, "create", return_value=mock_response):
                result = agent.navigate(kg)

        assert len(result) > 0
        assert budget.total_used == 130

    def test_navigate_resets_history_before_call(self):
        from src.agents.navigator_agent import NavigatorAgent

        budget = AgentBudget(50_000)
        kg = _make_simple_kg("x = 1\n")

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="overview")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 5

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            agent = NavigatorAgent(budget)
            agent.history = [{"role": "user", "content": "stale message"}]
            with patch.object(agent._client.messages, "create", return_value=mock_response):
                agent.navigate(kg)

        assert len(agent.history) == 2
