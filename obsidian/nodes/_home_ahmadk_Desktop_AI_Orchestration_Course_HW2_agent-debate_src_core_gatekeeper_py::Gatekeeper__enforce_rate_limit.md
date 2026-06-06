# Gatekeeper._enforce_rate_limit

**Kind**: `method`  
**File**: `/home/ahmadk/Desktop/AI_Orchestration_Course/HW2/agent-debate/src/core/gatekeeper.py`  
**Lines**: 45–63  
**Betweenness Centrality**: 0.0000  
**In-degree**: 1 | **Out-degree**: 0

> Block until the RPM sliding window has capacity.

Evicts timestamps older than 60 s, then sleeps if at limit.
Uses monotonic time to avoid wall-clock drift issues.

## Incoming Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_gatekeeper_py::Gatekeeper_execute|Gatekeeper.execute]] `Extracted:calls`
