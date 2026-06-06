# JudgeAgent.declare_winner

**Kind**: `method`  
**File**: `/home/ahmadk/Desktop/AI_Orchestration_Course/HW2/agent-debate/src/agents/judge_agent.py`  
**Lines**: 74–96  
**Betweenness Centrality**: 0.0033  
**In-degree**: 1 | **Out-degree**: 3

> Evaluate full transcript + all violations and return final verdict.

Violations are shown to the judge so the offending side is penalised.
No ties allowed — always returns winner '

## Outgoing Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_logger_py::FIFOLogger_info|FIFOLogger.info]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_base_agent_py::BaseAgent_generate_response|BaseAgent.generate_response]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_judge_agent_py::JudgeAgent__parse_verdict|JudgeAgent._parse_verdict]] `Extracted:calls`

## Incoming Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_sdk_py::DebateSDK_run|DebateSDK.run]] `Extracted:calls`
