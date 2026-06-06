# BaseAgent.generate_response

**Kind**: `method`  
**File**: `/home/ahmadk/Desktop/AI_Orchestration_Course/HW2/agent-debate/src/agents/base_agent.py`  
**Lines**: 127–148  
**Betweenness Centrality**: 0.0399  
**In-degree**: 5 | **Out-degree**: 5

> Send a user message, execute any tool calls, return clean text response.

Budget checking and token recording are handled inside gatekeeper.execute()
via _call_api — no explicit ch

## Outgoing Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_sdk_py::DebateSDK_run|DebateSDK.run]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_logger_py::FIFOLogger_info|FIFOLogger.info]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_base_agent_py::BaseAgent__strip_markdown|BaseAgent._strip_markdown]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_base_agent_py::BaseAgent__handle_tool_use|BaseAgent._handle_tool_use]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_base_agent_py::BaseAgent__extract_text|BaseAgent._extract_text]] `Extracted:calls`

## Incoming Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_sdk_py::DebateSDK__open_debate|DebateSDK._open_debate]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_sdk_py::DebateSDK__con_turn|DebateSDK._con_turn]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_sdk_py::DebateSDK__pro_turn|DebateSDK._pro_turn]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_judge_agent_py::JudgeAgent_observe|JudgeAgent.observe]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_judge_agent_py::JudgeAgent_declare_winner|JudgeAgent.declare_winner]] `Extracted:calls`
