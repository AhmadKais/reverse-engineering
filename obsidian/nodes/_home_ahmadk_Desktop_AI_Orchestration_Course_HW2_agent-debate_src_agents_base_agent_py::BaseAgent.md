# BaseAgent

**Kind**: `class`  
**File**: `/home/ahmadk/Desktop/AI_Orchestration_Course/HW2/agent-debate/src/agents/base_agent.py`  
**Lines**: 17–148  
**Betweenness Centrality**: 0.0022  
**In-degree**: 5 | **Out-degree**: 2

> Common LLM call logic, tool execution, token tracking, and watchdog wrapping.

All subagents (Pro, Con, Judge) extend this class.
Every API call is routed through Gatekeeper.execut

## Methods

- `__init__`
- `_call_api`
- `_handle_tool_use`
- `_extract_text`
- `_strip_markdown`
- `generate_response`

## Outgoing Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_config_py::load_config|load_config]] `Inferred:composes`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_config_py::get_api_key|get_api_key]] `Inferred:composes`

## Incoming Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_debater_agent_py::ProAgent|ProAgent]] `Extracted:inherits`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_debater_agent_py::ConAgent|ConAgent]] `Extracted:inherits`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_debater_agent_py::__module__|debater_agent]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_judge_agent_py::JudgeAgent|JudgeAgent]] `Extracted:inherits`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_judge_agent_py::__module__|judge_agent]] `Extracted:imports`
