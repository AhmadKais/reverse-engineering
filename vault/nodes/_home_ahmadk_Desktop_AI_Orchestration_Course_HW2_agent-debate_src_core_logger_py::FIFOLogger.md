# FIFOLogger

**Kind**: `class`  
**File**: `/home/ahmadk/Desktop/AI_Orchestration_Course/HW2/agent-debate/src/core/logger.py`  
**Lines**: 15–79  
**Betweenness Centrality**: 0.0031  
**In-degree**: 6 | **Out-degree**: 1

> Rotating JSONL logger with configurable file and line limits.

Each log entry is one JSON line: {"ts", "level", "source", "msg"}.
A single corrupt line never breaks the entire file

## Methods

- `__init__`
- `_log_files`
- `_open_current`
- `_rotate`
- `log`
- `info`
- `error`
- `warning`

## Outgoing Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_logger_py::FIFOLogger__open_current|FIFOLogger._open_current]] `Inferred:composes`

## Incoming Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_sdk_py::DebateSDK__build_infrastructure|DebateSDK._build_infrastructure]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_sdk_py::__module__|sdk]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_watchdog_py::__module__|watchdog]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_debater_agent_py::__module__|debater_agent]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_judge_agent_py::__module__|judge_agent]] `Extracted:imports`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_agents_base_agent_py::__module__|base_agent]] `Extracted:imports`
