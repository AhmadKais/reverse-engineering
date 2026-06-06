# gatekeeper

**Kind**: `module`  
**File**: `/home/ahmadk/Desktop/AI_Orchestration_Course/HW2/agent-debate/src/core/gatekeeper.py`  
**Lines**: 1–107  
**Betweenness Centrality**: 0.0000  
**In-degree**: 0 | **Out-degree**: 0

> API Gatekeeper — central gateway for all external API calls.

Every call to the Anthropic API must go through Gatekeeper.execute().
This enforces token budget and RPM rate limits, 
