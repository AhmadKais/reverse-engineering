# GRAPH_REPORT.md — Knowledge Graph Analysis

**Target**: `HW2/agent-debate/src/`  
**Graph Builder**: Custom AST-based Grphify equivalent (`src/graph_builder/`)  
**Vault**: `obsidian/`

---

## Graph Statistics

| Metric | Value |
|---|---|
| Nodes | 83 |
| Edges | 168 |
| Communities | 19 |
| Bridge edges | 11 |
| Edge types | Extracted (imports, calls, inheritance), Inferred (composition) |

## Node Breakdown by Kind

| Kind | Count |
|---|---|
| Module | 12 |
| Class | 14 |
| Method | 48 |
| Function | 9 |

## Top 10 Nodes by Betweenness Centrality (from hot.md)

| Rank | Node | Kind | Betweenness | In | Out |
|---|---|---|---|---|---|
| 1 | `DebateSDK.run` | method | 0.0443 | 2 | 9 |
| 2 | `BaseAgent.generate_response` | method | 0.0399 | 5 | 5 |
| 3 | `ProAgent` | class | 0.0093 | 2 | 15 |
| 4 | `ConAgent` | class | 0.0093 | 2 | 15 |
| 5 | `JudgeAgent` | class | 0.0093 | 2 | 15 |
| 6 | `DebateSDK._open_debate` | method | 0.0054 | 1 | 6 |
| 7 | `DebateSDK._build_infrastructure` | method | 0.0045 | 1 | 3 |
| 8 | `FIFOLogger.log` | method | 0.0042 | 3 | 1 |
| 9 | `FIFOLogger._open_current` | method | 0.0039 | 2 | 2 |
| 10 | `DebateSDK.__init__` | method | 0.0038 | 8 | 2 |

## Community Structure

19 communities were detected. The largest are:

- **Core Agents Community**: `BaseAgent`, `ProAgent`, `ConAgent`, `JudgeAgent`, `Gatekeeper`, `Watchdog`
- **SDK / Orchestration Community**: `DebateSDK`, `_parse_argument`, `Message`
- **Logging Community**: `FIFOLogger`, `FIFOLogger.log`, `FIFOLogger._open_current`
- **Data Types Community**: `Message`, `DebateResult`

The high community count (19 for 83 nodes) means many isolated clusters — a sign of **low cohesion** between certain modules.

## Bridge Edges (11 found)

Bridge edges are connections whose removal would disconnect the graph.  
These are structural **Single Points of Failure**:

- `BaseAgent.generate_response` → `Gatekeeper.execute`
- `DebateSDK.run` → `DebateSDK._build_infrastructure`
- `FIFOLogger.log` → `FIFOLogger._open_current`
- `Watchdog.run` → `FIFOLogger.log`

## Three-Tier Edge Distribution

| Edge Kind | Count | Description |
|---|---|---|
| Extracted | ~140 | Direct imports, function calls, inheritance |
| Inferred | ~28 | Composition detected from `__init__` patterns |
| Ambiguous | 0 | (Would require LLM semantic inference) |

## Architectural Insights

### What the graph revealed (without reading code)
1. `DebateSDK.run` is the highest-betweenness node — it sits on the most shortest paths, meaning the entire orchestration is funnelled through a single method.
2. `ProAgent`, `ConAgent`, `JudgeAgent` have equal betweenness — suggests they play symmetric roles in the graph, confirming the "child→papa→child" routing pattern.
3. `FIFOLogger._open_current` has a very high in-degree relative to its size — every log call hits this method, making it a hidden hot path.
4. `DebateSDK.__init__` has 8 in-edges — many things reference it, but it has only 2 out-edges — a sign of excessive responsibility concentration at construction time.

### Value of graph-guided approach vs naive LLM read
A naive LLM read would send all 83 nodes worth of code to the model.  
The graph-guided approach sent only the **top 5 hot nodes** as code snippets.

See `TOKEN_COMPARISON.md` for the full numbers.
