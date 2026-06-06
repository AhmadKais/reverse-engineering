# BaseAgent._call_api

**Kind**: `method`  
**File**: `/home/ahmadk/Desktop/AI_Orchestration_Course/HW2/agent-debate/src/agents/base_agent.py`  
**Lines**: 48–62  
**Betweenness Centrality**: 0.0000  
**In-degree**: 0 | **Out-degree**: 1

> Send messages to Claude via the Gatekeeper API gateway.

All budget checking and token recording happens inside
gatekeeper.execute() — this method never calls the client directly.

## Outgoing Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_gatekeeper_py::Gatekeeper_execute|Gatekeeper.execute]] `Extracted:calls`
