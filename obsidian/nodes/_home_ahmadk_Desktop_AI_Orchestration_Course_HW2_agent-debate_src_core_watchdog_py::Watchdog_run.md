# Watchdog.run

**Kind**: `method`  
**File**: `/home/ahmadk/Desktop/AI_Orchestration_Course/HW2/agent-debate/src/core/watchdog.py`  
**Lines**: 35–62  
**Betweenness Centrality**: 0.0000  
**In-degree**: 0 | **Out-degree**: 3

> Execute fn(*args, **kwargs) with timeout and retry on failure.

Uses ThreadPoolExecutor so the timeout is enforced even on blocking calls.
Back-off: sleeps 2^attempt seconds betwee

## Outgoing Relationships

- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_watchdog_py::WatchdogTimeoutError|WatchdogTimeoutError]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_logger_py::FIFOLogger_warning|FIFOLogger.warning]] `Extracted:calls`
- [[_home_ahmadk_Desktop_AI_Orchestration_Course_HW2_agent-debate_src_core_logger_py::FIFOLogger_error|FIFOLogger.error]] `Extracted:calls`
