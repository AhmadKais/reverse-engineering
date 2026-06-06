# Gatekeeper.record

**Kind**: `method`  
**File**: `/home/ahmadk/Desktop/AI_Orchestration_Course/HW2/agent-debate/src/core/gatekeeper.py`  
**Lines**: 86–94  
**Betweenness Centrality**: 0.0000  
**In-degree**: 1 | **Out-degree**: 1

> Accumulate token counts from a completed API response.

Also checks budget after recording — two-phase enforcement:
execute() checks before the call, record() checks after.

## Outgoing Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_gatekeeper_py::Gatekeeper_check_budget|Gatekeeper.check_budget]] `Extracted:calls`

## Incoming Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_gatekeeper_py::Gatekeeper_execute|Gatekeeper.execute]] `Extracted:calls`
