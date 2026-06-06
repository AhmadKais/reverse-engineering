# Watchdog

**Kind**: `class`  
**File**: `/home/ahmadk/Desktop/AI_Orchestration_Course/HW2/agent-debate/src/core/watchdog.py`  
**Lines**: 21–62  
**Betweenness Centrality**: 0.0000  
**In-degree**: 5 | **Out-degree**: 0

> Wraps any callable with timeout + exponential back-off retry.

Designed for autonomous agent environments where API calls may stall.
Each failed attempt is logged with elapsed mill

## Methods

- `__init__`
- `run`

## Incoming Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_sdk_py::DebateSDK__build_infrastructure|DebateSDK._build_infrastructure]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_sdk_py::__module__|sdk]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_debater_agent_py::__module__|debater_agent]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_judge_agent_py::__module__|judge_agent]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_base_agent_py::__module__|base_agent]] `Extracted:imports`
