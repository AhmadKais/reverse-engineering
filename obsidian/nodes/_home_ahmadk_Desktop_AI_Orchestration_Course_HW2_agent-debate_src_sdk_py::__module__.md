# sdk

**Kind**: `module`  
**File**: `/home/ahmadk/Desktop/AI_Orchestration_Course/HW2/agent-debate/src/sdk.py`  
**Lines**: 1–149  
**Betweenness Centrality**: 0.0000  
**In-degree**: 0 | **Out-degree**: 11

> Public SDK facade — single entry point for all debate logic.
External consumers (CLI, tests, REST) use this only. All messages
flow child→JudgeAgent→child as typed Pydantic Message

## Outgoing Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_debater_agent_py::ConAgent|ConAgent]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_debater_agent_py::ProAgent|ProAgent]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_judge_agent_py::JudgeAgent|JudgeAgent]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_config_py::load_config|load_config]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_config_py::load_rate_limits|load_rate_limits]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_gatekeeper_py::BudgetExceededError|BudgetExceededError]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_gatekeeper_py::Gatekeeper|Gatekeeper]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_gatekeeper_py::RateLimitExceededError|RateLimitExceededError]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_logger_py::FIFOLogger|FIFOLogger]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_watchdog_py::Watchdog|Watchdog]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_data_types_message_py::Message|Message]] `Extracted:imports`
