"""Generate graph.html — interactive vis-network visualization of the knowledge graph."""

from __future__ import annotations

import json
from pathlib import Path

_COLORS = {
    "Class": "#4e79a7", "Function": "#f28e2b",
    "Method": "#59a14f", "Module": "#76b7b2", "File": "#edc948",
}
_EDGE_DASH = {"Extracted": False, "Inferred": [5, 5], "Ambiguous": [2, 2]}
_EDGE_CLR = {"Extracted": "#666", "Inferred": "#999", "Ambiguous": "#bbb"}

_TMPL = """\
<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Knowledge Graph</title>
<script src="https://unpkg.com/vis-network@9.1.9/standalone/umd/vis-network.min.js"></script>
<style>
body{margin:0;font-family:monospace;background:#1a1a2e;color:#eee}
__HDR_CSS__
__G_CSS__
.l{display:inline-block;margin:0 6px}.d{display:inline-block;width:10px;height:10px;border-radius:50%;margin-right:3px}
</style></head>
<body>
<div id="hdr"><b>Knowledge Graph</b> &nbsp;SUMMARY &nbsp;&nbsp;LEGEND</div>
<div id="g"></div>
<script>
var N=new vis.DataSet(NODES_JS);
var E=new vis.DataSet(EDGES_JS);
new vis.Network(document.getElementById("g"),{nodes:N,edges:E},{
  nodes:{shape:"dot",size:16,borderWidth:2,font:{color:"#eee"}},
  edges:{smooth:{type:"dynamic"},width:2,font:{color:"#bbb",size:10}},
  physics:{stabilization:{iterations:150},barnesHut:{gravitationalConstant:-3000}},
  interaction:{hover:true,tooltipDelay:100}
});
</script></body></html>"""


def write_graph_html(vault_path: Path, data: dict) -> None:
    """Write graph.html — interactive knowledge-graph visualization from graph.json data."""
    nodes_js = json.dumps(_vis_nodes(data.get("nodes", [])))
    edges_js = json.dumps(_vis_edges(data.get("edges", [])))
    m = data.get("meta", {})
    summary = f"{m.get('node_count', 0)} nodes &middot; {m.get('edge_count', 0)} edges"
    legend = "".join(
        f'<span class="l"><span class="d" style="background:{c}"></span>{k}</span>'
        for k, c in _COLORS.items()
    )
    html = (_TMPL
            .replace("__HDR_CSS__", "#hdr{padding:8px 16px;background:#16213e;border-bottom:1px solid #0f3460;font-size:13px}")
            .replace("__G_CSS__", "#g{width:100%;height:calc(100vh - 38px)}")
            .replace("SUMMARY", summary)
            .replace("LEGEND", legend)
            .replace("NODES_JS", nodes_js)
            .replace("EDGES_JS", edges_js))
    (vault_path / "graph.html").write_text(html, encoding="utf-8")


def _vis_nodes(nodes: list[dict]) -> list[dict]:
    """Convert graph.json node dicts to vis-network node format."""
    return [
        {"id": n["id"],
         "label": n.get("label", n["id"]).split("::")[-1],
         "title": f'{n["id"]}<br>kind: {n.get("kind","")}<br>betweenness: {n.get("betweenness", 0):.4f}',
         "color": _COLORS.get(n.get("kind", ""), "#999")}
        for n in nodes
    ]


def _vis_edges(edges: list[dict]) -> list[dict]:
    """Convert graph.json edge dicts to vis-network edge format with dash/color styles."""
    return [
        {"from": e["source"],
         "to": e["target"],
         "label": e.get("label", ""),
         "title": f'{e.get("kind","")} &middot; conf: {e.get("confidence", e.get("weight", 1.0)):.2f}<br>src: {e.get("source_file","")}',
         "dashes": _EDGE_DASH.get(e.get("kind", "Extracted"), False),
         "color": {"color": _EDGE_CLR.get(e.get("kind", "Extracted"), "#666")},
         "arrows": "to"}
        for e in edges
    ]
