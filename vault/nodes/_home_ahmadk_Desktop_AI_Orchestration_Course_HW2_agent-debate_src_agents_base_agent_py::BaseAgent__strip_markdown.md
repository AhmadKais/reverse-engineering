# BaseAgent._strip_markdown

**Kind**: `method`  
**File**: `/home/ahmadk/Desktop/AI_Orchestration_Course/HW2/agent-debate/src/agents/base_agent.py`  
**Lines**: 114–125  
**Betweenness Centrality**: 0.0000  
**In-degree**: 1 | **Out-degree**: 0

> Remove markdown code fences that LLMs sometimes wrap JSON responses in.

Agents are prompted to output raw JSON, but occasionally return
```json ... ``` blocks. Stripping keeps his

## Incoming Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_base_agent_py::BaseAgent_generate_response|BaseAgent.generate_response]] `Extracted:calls`
