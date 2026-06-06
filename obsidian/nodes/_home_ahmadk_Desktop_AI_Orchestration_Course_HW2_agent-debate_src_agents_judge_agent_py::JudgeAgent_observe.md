# JudgeAgent.observe

**Kind**: `method`  
**File**: `/home/ahmadk/Desktop/AI_Orchestration_Course/HW2/agent-debate/src/agents/judge_agent.py`  
**Lines**: 51–72  
**Betweenness Centrality**: 0.0028  
**In-degree**: 3 | **Out-degree**: 3

> Receive argument, run all 8 rule checks, log violations, route to next speaker.

Implements child→papa→child with full active moderation:
profanity, ad hominem, off-topic, empty, n

## Outgoing Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_judge_agent_py::JudgeAgent__last_opponent_argument|JudgeAgent._last_opponent_argument]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_base_agent_py::BaseAgent_generate_response|BaseAgent.generate_response]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_judge_agent_py::JudgeAgent__parse_route_and_check|JudgeAgent._parse_route_and_check]] `Extracted:calls`

## Incoming Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_sdk_py::DebateSDK__open_debate|DebateSDK._open_debate]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_sdk_py::DebateSDK__con_turn|DebateSDK._con_turn]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_sdk_py::DebateSDK__pro_turn|DebateSDK._pro_turn]] `Extracted:calls`
