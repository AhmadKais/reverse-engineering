# Gatekeeper

**Kind**: `class`  
**File**: `/home/ahmadk/Desktop/AI_Orchestration_Course/HW2/agent-debate/src/core/gatekeeper.py`  
**Lines**: 24–107  
**Betweenness Centrality**: 0.0000  
**In-degree**: 5 | **Out-degree**: 0

> Centralized API call manager: enforces token budget, RPM rate limit, logs all calls.

All external API calls must be routed through execute() — never call
the Anthropic client dire

## Methods

- `__init__`
- `total_tokens`
- `_enforce_rate_limit`
- `execute`
- `check_budget`
- `record`
- `status`

## Incoming Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_sdk_py::DebateSDK__build_infrastructure|DebateSDK._build_infrastructure]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_sdk_py::__module__|sdk]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_debater_agent_py::__module__|debater_agent]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_judge_agent_py::__module__|judge_agent]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_base_agent_py::__module__|base_agent]] `Extracted:imports`
