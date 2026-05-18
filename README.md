# archal-agenteval

Test your AI agent against Archal twins using AgentEval scenarios.

Built in a weekend by [Fizza Mukhtar](https://github.com/Fizza-Mukhtar) —
founder of [AgentEval](https://github.com/Fizza-Mukhtar/agentEval), an open-source
behavioral testing framework for AI agents.

## The problem

You want to test whether your agent correctly interacts with GitHub, Stripe, or Slack.
But hitting real APIs during testing means real consequences — real issues created,
real charges made, real messages sent.

Archal solves the environment problem: working clones of real services, same API surface, no real consequences.
AgentEval solves the evaluation problem: did the agent call the right tools, in the right order, without looping?

This integration wires them together.

## How it works

```
AgentEval generates test scenarios
    -> Archal twin starts (GitHub, Stripe, Slack...)
    -> Twin seeded with known starting state
    -> Task sent to your agent
    -> Agent hits twin API (not real API)
    -> AgentEval evaluates: right tools? right order? completed?
    -> Pass/fail result with exact failure point
```

## Results

```
AgentEval + Archal Results
==================================================
Twin      : github
Session   : 14b76daf...
Pass rate : 67% (2/3)
==================================================
  [PASS] Happy path: create issue
         Steps: 3
  [PASS] Happy path: book a flight
         Steps: 3
  [FAIL] Failure case: missing info
         Agent did not signal task completion
         Steps: 1
```

## Setup

```bash
# Install dependencies
pip install httpx
npm install -g archal
archal login

# Start a twin
archal twin start github

# Set environment variables
export ARCHAL_TOKEN=archal_xxx
export ARCHAL_SESSION_ID=<session-id-from-above>
export AGENT_ENDPOINT=http://localhost:9001/run
```

## Run

```bash
python demo.py
```

## Use in your own project

```python
from archal_agenteval import ArchalAgentEvalRunner

runner = ArchalAgentEvalRunner(
    archal_token="archal_xxx",
    session_id="your-session-id",
    agent_endpoint="http://localhost:9000/run",
    twin="github",
)

results = await runner.run(
    scenarios=[
        {
            "title": "Create issue",
            "task": "Create a GitHub issue titled 'bug: login fails' in testuser/test-repo",
        },
    ],
    expected_tools=["create_issue"],
    max_steps=5,
)

print(results.summary())
```

## Folder structure

```
archal-agenteval/
├── archal_agenteval/
│   ├── __init__.py
│   └── runner.py        <- core integration
├── .archal/
│   └── harness.mjs      <- Archal CLI harness
├── scenarios/           <- markdown scenario files
├── demo.py              <- end-to-end demo
└── README.md
```

## Supported twins

github, stripe, slack, linear, supabase, discord, google-workspace

## Why this matters

Most agent testing hits real APIs — which means:
- Real side effects during testing
- Can't reset state between scenarios
- Can't run the same test twice safely

Archal + AgentEval gives you:
- Clean state before every scenario
- Full execution trace
- Exact failure point when something breaks
- Safe to run in CI

---

AgentEval: https://github.com/Fizza-Mukhtar/agentEval
Archal: https://archal.ai
