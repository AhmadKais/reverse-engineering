# Gatekeeper.execute

**Kind**: `method`  
**File**: `/home/ahmadk/Desktop/AI_Orchestration_Course/HW2/agent-debate/src/core/gatekeeper.py`  
**Lines**: 65–76  
**Betweenness Centrality**: 0.0006  
**In-degree**: 1 | **Out-degree**: 3

> Execute an API call through the gateway.

Enforces RPM rate limit and budget before execution, records tokens after.
All Anthropic API calls must go through this method.

## Outgoing Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_gatekeeper_py::Gatekeeper__enforce_rate_limit|Gatekeeper._enforce_rate_limit]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_gatekeeper_py::Gatekeeper_check_budget|Gatekeeper.check_budget]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_gatekeeper_py::Gatekeeper_record|Gatekeeper.record]] `Extracted:calls`

## Incoming Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_base_agent_py::BaseAgent__call_api|BaseAgent._call_api]] `Extracted:calls`
