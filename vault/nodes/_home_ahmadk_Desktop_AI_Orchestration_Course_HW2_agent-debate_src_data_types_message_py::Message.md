# Message

**Kind**: `class`  
**File**: `/home/ahmadk/Desktop/AI_Orchestration_Course/HW2/agent-debate/src/data_types/message.py`  
**Lines**: 13–41  
**Betweenness Centrality**: 0.0000  
**In-degree**: 4 | **Out-degree**: 0

> Represents one argument in the debate, serializable as JSON for IPC.

Every message flows: sender → Judge → recipient.
The Judge observes, routes, and logs each Message before forw

## Inherits From

- [[pydantic.BaseModel]]

## Methods

- `to_ipc_dict`
- `from_ipc_dict`
- `summary`

## Incoming Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_sdk_py::DebateSDK__open_debate|DebateSDK._open_debate]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_sdk_py::DebateSDK__con_turn|DebateSDK._con_turn]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_sdk_py::DebateSDK__pro_turn|DebateSDK._pro_turn]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_sdk_py::__module__|sdk]] `Extracted:imports`
