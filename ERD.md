# EX04 — Entity Relationship Diagram

All diagrams are in Mermaid syntax. Render in GitHub, Obsidian, or any Mermaid viewer.

---

## 1. Core Data Models

```mermaid
erDiagram
    GraphNode {
        string id PK
        NodeKind kind
        string name
        string file_path
        int line_start
        int line_end
        string docstring
        string parent_class FK
        list base_classes
        list methods
        list calls
    }

    GraphEdge {
        string source FK
        string target FK
        EdgeKind kind
        EdgeLabel label
        float weight
    }

    GraphMetrics {
        int node_count
        int edge_count
        list top_hubs
        list bridges
        list communities
        dict betweenness
        dict in_degree
        dict out_degree
    }

    KnowledgeGraph {
        DiGraph graph
        dict _nodes
        GraphMetrics _metrics
    }

    GraphNode ||--o{ GraphEdge : "source"
    GraphNode ||--o{ GraphEdge : "target"
    KnowledgeGraph ||--o{ GraphNode : "contains"
    KnowledgeGraph ||--|| GraphMetrics : "computes"
```

---

## 2. Agent Hierarchy

```mermaid
classDiagram
    class AgentBudget {
        +int max_tokens
        +int used_input
        +int used_output
        +int total_used
        +int remaining
        +record(input, output)
        +status() dict
    }

    class BaseAgent {
        +str name
        +str system_prompt
        +AgentBudget budget
        +str model
        +int max_tokens
        +int max_retries
        +list history
        +generate_response(msg) str
        +reset_history()
        -_call_llm(messages) str
        -_extract_text(response) str
        -_load_api_key() str
        -_strip_fences(text) str
    }

    class NavigatorAgent {
        +navigate(kg) str
    }

    class AnalyzerAgent {
        +analyze(kg, source_root) dict
        -_collect_snippets(kg, root) str
        -_parse_report(raw) dict
    }

    class FixerAgent {
        +propose_fixes(bug_report, root) dict
        +apply_fixes(fix_report, root, dry_run) list
        -_read_affected_code(bugs, root) str
        -_parse_fixes(raw) dict
    }

    BaseAgent <|-- NavigatorAgent
    BaseAgent <|-- AnalyzerAgent
    BaseAgent <|-- FixerAgent
    BaseAgent --> AgentBudget : "shares"
    NavigatorAgent --> KnowledgeGraph : "reads summary"
    AnalyzerAgent --> KnowledgeGraph : "reads metrics + snippets"
```

---

## 3. LangGraph Workflow State

```mermaid
classDiagram
    class WorkflowState {
        +str source_root
        +str vault_dir
        +KnowledgeGraph knowledge_graph
        +dict graph_summary
        +dict raw_files
        +str navigation
        +dict bug_report
        +dict fix_report
        +dict token_usage
        +bool is_sparse
        +str error
    }

    class BugReport {
        +list bugs
        +str summary
        +bool parse_error
    }

    class Bug {
        +str type
        +str severity
        +list affected_nodes
        +str evidence
        +str fix_hint
    }

    class FixReport {
        +list fixes
        +str overall_impact
        +bool parse_error
    }

    class Fix {
        +str bug_type
        +str file_path
        +str target_symbol
        +str description
        +str architectural_pattern
        +str new_class_or_method
        +str explanation
    }

    WorkflowState --> BugReport : "bug_report"
    WorkflowState --> FixReport : "fix_report"
    BugReport --> Bug : "bugs[]"
    FixReport --> Fix : "fixes[]"
```

---

## 4. LangGraph Node Flow

```mermaid
flowchart TD
    START((__start__))
    BG[build_graph_node\nAST parse → KG → vault export]
    NAV[navigate_node\nNavigatorAgent\ndense path]
    RAW[raw_reader_node\nBaseAgent\nsparse path]
    ANA[analyze_node\nAnalyzerAgent]
    FIX[fix_node\nFixerAgent]
    END((__end__))

    START --> BG
    BG -->|edge_count ≥ 5| NAV
    BG -->|edge_count < 5 sparse| RAW
    BG -->|error set| ANA
    NAV --> ANA
    RAW --> ANA
    ANA --> FIX
    FIX --> END

    style RAW fill:#f9a,stroke:#c66
    style NAV fill:#9bf,stroke:#36c
    style ANA fill:#bfb,stroke:#393
    style FIX fill:#fbf,stroke:#939
```

---

## 5. Graph Builder Internals

```mermaid
flowchart LR
    PY[".py files"] -->|ast.parse| AP[ast_parser\nparse_file / parse_directory]
    AP -->|GraphNode list| GG[graph_generator\nKnowledgeGraph.build]
    AP -->|GraphEdge list| GG
    GG -->|networkx DiGraph| M[compute_metrics\nbetweenness / bridges / communities]
    M --> OE[obsidian_exporter\nObsidianExporter.export]
    OE --> GJ[graph.json]
    OE --> HM[hot.md]
    OE --> IM[index.md]
    OE --> ND[nodes/*.md]
```

---

## 6. Enum Values

```mermaid
classDiagram
    class NodeKind {
        MODULE
        CLASS
        FUNCTION
        METHOD
        FILE
    }

    class EdgeKind {
        EXTRACTED
        INFERRED
        AMBIGUOUS
    }

    class EdgeLabel {
        IMPORTS
        CALLS
        INHERITS
        COMPOSES
        DEFINES
        REFERENCES
    }

    GraphNode --> NodeKind : kind
    GraphEdge --> EdgeKind : kind
    GraphEdge --> EdgeLabel : label
```

---

## 7. File → Output Mapping

```mermaid
flowchart LR
    subgraph inputs["Input (source_root)"]
        PY1["polygons/polygons.py"]
        PY2["mathsquiz/mathsquiz.py"]
        PYN["…/*.py"]
    end

    subgraph pipeline["Pipeline"]
        AP["ast_parser"]
        KG["KnowledgeGraph"]
        WF["LangGraph workflow"]
    end

    subgraph vault["obsidian/ (vault output)"]
        GJ["graph.json"]
        HM["hot.md"]
        IM["index.md"]
        ND["nodes/*.md"]
        AR["analysis_report.json"]
    end

    subgraph artifacts["artifacts/ (fix output)"]
        FP["fixed_polygons.py"]
        FM["fixed_mathsquiz.py"]
        FB["fixed_mathsquiz.py"]
    end

    inputs --> AP --> KG --> WF
    KG --> GJ
    KG --> HM
    KG --> IM
    KG --> ND
    WF --> AR
    WF -.->|"human writes fixes"| FP
    WF -.->|"human writes fixes"| FM
```
