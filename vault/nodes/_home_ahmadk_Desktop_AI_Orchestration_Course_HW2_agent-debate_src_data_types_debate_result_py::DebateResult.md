# DebateResult

**Kind**: `class`  
**File**: `/home/ahmadk/Desktop/AI_Orchestration_Course/HW2/agent-debate/src/data_types/debate_result.py`  
**Lines**: 8–41  
**Betweenness Centrality**: 0.0000  
**In-degree**: 0 | **Out-degree**: 0

> Structured verdict produced by the Judge agent.

winner must always be 'Pro' or 'Con' — ties are forbidden by the assignment.

## Inherits From

- [[pydantic.BaseModel]]

## Methods

- `winner_must_not_be_tie`
- `scores_in_range`
- `to_dict`
