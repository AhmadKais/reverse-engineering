# judge_agent

**Kind**: `module`  
**File**: `/home/ahmadk/Desktop/AI_Orchestration_Course/HW2/agent-debate/src/agents/judge_agent.py`  
**Lines**: 1–138  
**Betweenness Centrality**: 0.0000  
**In-degree**: 0 | **Out-degree**: 4

> Judge (Papa) agent — routes all messages and declares the debate winner.

Every argument flows child → JudgeAgent → child.
The Judge enforces 8 debate rules before routing each mes

## Outgoing Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_base_agent_py::BaseAgent|BaseAgent]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_gatekeeper_py::Gatekeeper|Gatekeeper]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_logger_py::FIFOLogger|FIFOLogger]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_watchdog_py::Watchdog|Watchdog]] `Extracted:imports`
