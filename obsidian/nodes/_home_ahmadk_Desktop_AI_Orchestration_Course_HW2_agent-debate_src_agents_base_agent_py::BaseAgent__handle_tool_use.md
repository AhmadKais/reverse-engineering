# BaseAgent._handle_tool_use

**Kind**: `method`  
**File**: `/home/ahmadk/Desktop/AI_Orchestration_Course/HW2/agent-debate/src/agents/base_agent.py`  
**Lines**: 64–104  
**Betweenness Centrality**: 0.0019  
**In-degree**: 2 | **Out-degree**: 6

> Execute tool calls recursively until Claude returns a text response.

Claude sometimes chains multiple searches before writing the argument.
_MAX_TOOL_ROUNDS depth cap prevents run

## Outgoing Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_sdk_py::DebateSDK_run|DebateSDK.run]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_base_agent_py::BaseAgent__extract_text|BaseAgent._extract_text]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_logger_py::FIFOLogger_warning|FIFOLogger.warning]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_base_agent_py::BaseAgent__handle_tool_use|BaseAgent._handle_tool_use]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_logger_py::FIFOLogger_info|FIFOLogger.info]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_tools_search_py::web_search|web_search]] `Extracted:calls`

## Incoming Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_base_agent_py::BaseAgent__handle_tool_use|BaseAgent._handle_tool_use]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_base_agent_py::BaseAgent_generate_response|BaseAgent.generate_response]] `Extracted:calls`
