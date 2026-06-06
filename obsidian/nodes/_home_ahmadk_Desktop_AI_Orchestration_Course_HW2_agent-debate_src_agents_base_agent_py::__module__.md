# base_agent

**Kind**: `module`  
**File**: `/home/ahmadk/Desktop/AI_Orchestration_Course/HW2/agent-debate/src/agents/base_agent.py`  
**Lines**: 1–148  
**Betweenness Centrality**: 0.0000  
**In-degree**: 0 | **Out-degree**: 6

> Base agent: shared LLM call logic, tool execution, token tracking, watchdog.

All API calls go through Gatekeeper.execute() — never call the Anthropic
client directly. This enforce

## Outgoing Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_config_py::get_api_key|get_api_key]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_config_py::load_config|load_config]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_gatekeeper_py::Gatekeeper|Gatekeeper]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_logger_py::FIFOLogger|FIFOLogger]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_watchdog_py::Watchdog|Watchdog]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_tools_search_py::web_search|web_search]] `Extracted:imports`
