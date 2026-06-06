# _parse_argument

**Kind**: `function`  
**File**: `/home/ahmadk/Desktop/AI_Orchestration_Course/HW2/agent-debate/src/sdk.py`  
**Lines**: 24–48  
**Betweenness Centrality**: 0.0014  
**In-degree**: 3 | **Out-degree**: 1

> Extract argument text and references from agent JSON response.
Three-stage: json.loads → embedded scan → regex fallback for malformed JSON.

## Outgoing Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_tools_search_py::__module__|search]] `Extracted:calls`

## Incoming Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_sdk_py::DebateSDK__open_debate|DebateSDK._open_debate]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_sdk_py::DebateSDK__con_turn|DebateSDK._con_turn]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_sdk_py::DebateSDK__pro_turn|DebateSDK._pro_turn]] `Extracted:calls`
