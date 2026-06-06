# Block Schema — System Architecture

## High-Level Block Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         DebateSDK (Facade)                      │
│  cfg: topic, max_pings, token_budget, timeout, model            │
└──────────────────────────────┬──────────────────────────────────┘
                               │ creates & orchestrates
          ┌────────────────────┼───────────────────────┐
          ▼                    ▼                       ▼
  ┌───────────────┐   ┌────────────────┐    ┌──────────────────┐
  │  FIFOLogger   │   │   Gatekeeper   │    │    Watchdog      │
  │ (file log,    │   │ (token budget, │    │ (timeout +       │
  │  FIFO rotate) │   │  RPM limiter,  │    │  exponential     │
  │               │   │  audit point)  │    │  retry)          │
  └───────┬───────┘   └───────┬────────┘    └────────┬─────────┘
          │                   │                      │
          └──────────┬────────┘──────────────────────┘
                     │  shared infrastructure (injected)
     ┌───────────────┼────────────────────┐
     ▼               ▼                    ▼
┌─────────┐    ┌──────────┐        ┌────────────┐
│ProAgent │    │ ConAgent │        │ JudgeAgent │
│(AXIOM)  │    │(NEMESIS) │        │(THE ARBITER│
│         │    │          │        │            │
│ extends │    │ extends  │        │  extends   │
│BaseAgent│    │BaseAgent │        │ BaseAgent  │
└────┬────┘    └────┬─────┘        └─────┬──────┘
     │              │                    │
     │              └──────────┐         │
     │    child → papa → child │         │
     └──────────────────────── ┼ ────────┘
                                │
                     ┌──────────▼──────────┐
                     │     BaseAgent       │
                     │  generate_response  │◄── all API calls
                     │  _handle_tool_use   │    via Gatekeeper
                     │  _call_api          │
                     └──────────┬──────────┘
                                │
                     ┌──────────▼──────────┐
                     │   Anthropic API     │
                     │  (claude-sonnet)    │
                     └─────────────────────┘
```

## Message Flow (child → papa → child)

```
Round N:
  ProAgent ──[argument]──► JudgeAgent.observe("Pro", arg)
                                    │
                           [checks 8 rules]
                           [routes to "Con"]
                                    │
  ConAgent ◄──[routed]────────────────
  ConAgent ──[counter]──► JudgeAgent.observe("Con", arg)
                                    │
                           [checks 8 rules]
                           [routes to "Pro"]
                                    │
  ProAgent ◄──[routed]────────────────

  ... after max_pings ...

  JudgeAgent.declare_winner() → DebateResult
```

## Data Flow

```
Config (config.json)
  └─► DebateSDK.__init__
        └─► _build_infrastructure()
              ├─► FIFOLogger    → log files
              ├─► Gatekeeper    → token budget
              └─► Watchdog      → timeout guard

User call: sdk.run(topic)
  └─► _open_debate(pro, judge, topic)
        └─► pro.generate_response(opening_prompt)
              └─► Watchdog.run(_call_api)
                    └─► Gatekeeper.execute(client.messages.create)
                          └─► Anthropic API
                                └─► Message (response)
                    └─► _handle_tool_use (if tool_call)
                          └─► web_search(query)
                                └─► Gatekeeper.execute(...)

  └─► _run_rounds(pro, con, judge, ...)
        └─► [loop] _con_turn / _pro_turn
              └─► judge.observe(side, arg)
                    └─► judge.generate_response(routing_prompt)

  └─► judge.declare_winner()
  └─► _save_transcript(transcript, verdict, topic)
        └─► logs/transcript.json
```

## Architectural Hotspots (from graph analysis)

| Block | Betweenness | Role | Risk |
|---|---|---|---|
| `DebateSDK.run` | 0.0443 | Top orchestrator | God Object (does too much) |
| `BaseAgent.generate_response` | 0.0399 | All LLM calls pass through | Bottleneck + SPOF |
| `JudgeAgent` | 0.0093 | All messages route through it | Bottleneck + SPOF |
| `FIFOLogger._open_current` | 0.0039 | Every log call reopens file | SPOF (no fallback) |
| `DebateSDK.__init__` | 0.0038 | All infra created here | Constructor failure = total failure |
