# OOP Schema — agent-debate Codebase

Class hierarchy and composition relationships extracted by the graph builder.

## Inheritance Hierarchy

```
object
└── BaseAgent                          (src/agents/base_agent.py)
    ├── ProAgent                       (src/agents/debater_agent.py)
    ├── ConAgent                       (src/agents/debater_agent.py)
    └── JudgeAgent                     (src/agents/judge_agent.py)

Exception
├── BudgetExceededError                (src/core/gatekeeper.py)
├── RateLimitExceededError             (src/core/gatekeeper.py)
├── WatchdogTimeoutError               (src/core/watchdog.py)
└── RuleViolationError                 (src/agents/judge_agent.py)

pydantic.BaseModel
├── Message                            (src/data_types/message.py)
└── DebateResult                       (src/data_types/debate_result.py)
```

## Mermaid Class Diagram

```mermaid
classDiagram

    class BaseAgent {
        +name: str
        +system_prompt: str
        +gatekeeper: Gatekeeper
        +watchdog: Watchdog
        +logger: FIFOLogger
        +model: str
        +history: list
        +_call_api(messages) Message
        +_handle_tool_use(response, depth) str
        +generate_response(user_message) str
        +_extract_text(response) str
        +_strip_markdown(text) str
    }

    class ProAgent {
        +name = "AXIOM (Pro)"
        +tools: [SEARCH_TOOL]
    }

    class ConAgent {
        +name = "NEMESIS (Con)"
        +tools: [SEARCH_TOOL]
    }

    class JudgeAgent {
        +debate_transcript: list
        +violations: list
        +observe(side, argument) str
        +declare_winner() dict
        +_last_opponent_argument(side) str
        +_parse_route_and_check(raw, side, fallback) str
        +_parse_verdict(raw) dict
    }

    class Gatekeeper {
        +token_budget: int
        +total_input_tokens: int
        +total_output_tokens: int
        +_rpm_limit: int
        +_rpm_window: deque
        +execute(api_call, *args, **kwargs) Any
        +check_budget() None
        +record(input_tokens, output_tokens) None
        +status() dict
        +_enforce_rate_limit() None
    }

    class Watchdog {
        +timeout_seconds: int
        +max_retries: int
        +logger: FIFOLogger
        +run(fn, *args, source, **kwargs) Any
    }

    class FIFOLogger {
        +log_dir: Path
        +max_files: int
        +max_lines: int
        +log(level, source, message) None
        +info(source, message) None
        +warning(source, message) None
        +error(source, message) None
        +_open_current() TextIO
        +_rotate() None
        +_log_files() list
    }

    class DebateSDK {
        +cfg: dict
        +run(topic, max_pings, on_argument) dict
        +_build_infrastructure() tuple
        +_open_debate(pro, judge, topic, ...) str
        +_run_rounds(pro, con, judge, ...) None
        +_con_turn(con, judge, pro_arg, ...) str
        +_pro_turn(pro, judge, con_arg, ...) str
        +_save_transcript(transcript, verdict, topic) None
    }

    class Message {
        +round: int
        +sender: AgentRole
        +recipient: AgentRole
        +content: str
        +timestamp: str
        +references: list
        +to_ipc_dict() dict
        +from_ipc_dict(data) Message
        +summary() str
    }

    class DebateResult {
        +winner: str
        +reason: str
        +score_pro: int
        +score_con: int
        +summary: str
        +violations: list
        +scores_in_range() bool
        +winner_must_not_be_tie() str
        +to_dict() dict
    }

    BaseAgent <|-- ProAgent
    BaseAgent <|-- ConAgent
    BaseAgent <|-- JudgeAgent

    BaseAgent *-- Gatekeeper : uses (composition)
    BaseAgent *-- Watchdog   : uses (composition)
    BaseAgent *-- FIFOLogger : uses (composition)

    Watchdog *-- FIFOLogger  : uses (composition)

    DebateSDK ..> ProAgent   : creates
    DebateSDK ..> ConAgent   : creates
    DebateSDK ..> JudgeAgent : creates
    DebateSDK ..> Gatekeeper : creates
    DebateSDK ..> Watchdog   : creates
    DebateSDK ..> FIFOLogger : creates
    DebateSDK ..> Message    : produces
```

## Key OOP Observations

| Pattern | Location | Notes |
|---|---|---|
| Template Method | `BaseAgent` | `generate_response` is the template; subclasses specialise via `system_prompt` and `tools` |
| Facade | `DebateSDK` | Hides all agent/infrastructure wiring from the caller |
| Gateway | `Gatekeeper` | All API calls must go through `execute()` — enforces a single audit point |
| Strategy (implicit) | `JudgeAgent` rule checks | 8 rules encoded as string constants; extractable to a Strategy |
| Value Object | `Message`, `DebateResult` | Immutable Pydantic models for IPC |

## Architectural Bug: Missing Abstraction (God Object)

`DebateSDK` is both a **factory** (creates all agents and infrastructure) and an **orchestrator** (runs rounds, saves transcripts).  
The OOP fix: split into `AgentFactory`, `DebateOrchestrator`, and keep `DebateSDK` as a thin facade.
