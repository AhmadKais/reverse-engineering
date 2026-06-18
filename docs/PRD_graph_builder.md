# PRD — Graph Builder (Grphify Equivalent)

**Component**: `src/graph_builder/`  
**Type**: Central algorithm — AST parsing + knowledge graph construction  
**Status**: Delivered

---

## Algorithm Overview

The graph builder converts a Python source tree into a weighted directed knowledge graph.  
Pipeline: `parse_directory()` → `KnowledgeGraph` → `ObsidianExporter` → vault files.

### Theoretical background

Based on the concepts from Grphify (Lecture 07):
- Each Python entity (module, class, function) becomes a **node** with a `NodeKind` enum
- Relationships (import, call, inheritance, composition) become **edges** with `EdgeKind` enum
- Betweenness centrality identifies **God Nodes** — highly connected components
- Community detection reveals sub-system clusters
- Bridge edges reveal fragile coupling between sub-systems

---

## Requirements

### Functional

| ID | Requirement | Acceptance Criteria |
|----|-------------|---------------------|
| GB-1 | Parse `.py` files to `GraphNode` + `GraphEdge` lists | `parse_file()` returns non-empty list for valid Python |
| GB-2 | Handle `SyntaxError` without crashing | `parse_file()` on broken file returns `([], [])` |
| GB-3 | Build networkx DiGraph from nodes + edges | `KnowledgeGraph.graph` is a `networkx.DiGraph` |
| GB-4 | Compute betweenness centrality for all nodes | `KnowledgeGraph.centrality` dict populated for all nodes |
| GB-5 | Detect sparse graphs (`edge_count < SPARSE_EDGE_THRESHOLD`) | `KnowledgeGraph.is_sparse` is `True` when edges < 5 |
| GB-6 | Export Obsidian vault (`hot.md`, `index.md`, `nodes/`, `graph.json`, `graph.html`) | All 5 output types present after export |
| GB-7 | `graph.html` must be an interactive vis-network visualization | Opens in any browser without server |

### Non-functional

- Parse latency < 2 seconds for a 1,000-line codebase on standard hardware
- No external network calls — pure local AST analysis
- All graph metrics computed using networkx only (no custom centrality)

---

## Inputs / Outputs

| | Type | Description |
|-|------|-------------|
| **Input** | `Path` | Root directory of the Python codebase |
| **Output** | `KnowledgeGraph` | networkx DiGraph + metrics + node/edge lists |
| **Side effect** | vault files | `hot.md`, `index.md`, `nodes/`, `graph.json`, `graph.html` written to vault dir |

---

## Algorithm Detail

```
parse_directory(root)
  └── for each .py file:
        parse_file(path)
          └── ast.parse(source)      → raises SyntaxError → return ([], [])
              _FileVisitor.visit()   → collects Module/Class/Function nodes
              return (nodes, edges)

KnowledgeGraph.build(nodes, edges)
  └── networkx.DiGraph
  └── betweenness_centrality()
  └── greedy_modularity_communities()
  └── bridges()
  └── is_sparse = (edge_count < SPARSE_EDGE_THRESHOLD)

ObsidianExporter.export(kg, vault_dir)
  └── write_hot(kg)       → hot.md
  └── write_index(kg)     → index.md
  └── render_node_note()  → nodes/<id>.md × N
  └── write_graph_json()  → graph.json
  └── write_graph_html()  → graph.html
```

---

## Constraints

- Does not support Python 2 syntax (by design — failed parse is the diagnostic signal)
- Does not support non-Python files
- `graph.html` uses vis-network CDN; requires internet to load the CDN version in a browser

---

## Test Coverage

| Test file | What it covers |
|-----------|---------------|
| `tests/test_ast_parser.py` (10 tests) | `parse_file`, `parse_directory`, SyntaxError fallback |
| `tests/test_graph_builder.py` (7 tests) | `KnowledgeGraph` build, centrality, summary, `is_sparse` |
| `tests/test_obsidian.py` (12 tests) | `ObsidianExporter`, `graph.html`, vault file content |
| `tests/test_kg_extras.py` (5 tests) | `KnowledgeGraph` edge cases, empty graph, community detection |
| `tests/test_data_types.py` (17 tests) | `GraphNode`, `GraphEdge`, `NodeKind`, `EdgeKind` |

---

## Success Metrics

- KPI 1: `is_sparse=True` correctly detected on `data/broken-python` (0 edges)
- KPI 2: `is_sparse=False` on `data/demo-dense` (24 edges)
- KPI 3: vault export produces all 5 output files
- KPI 4: graph.html opens and displays interactive graph in browser
