# Archal-AgentEval

Test your AI agents against Archal twins using AgentEval.

Built by [Fizza Mukhtar](https://github.com/Fizza-Mukhtar) —
founder of [AgentEval](https://github.com/Fizza-Mukhtar/agentEval).

## What this is

A real end-to-end integration between two complementary tools:

**AgentEval** — evaluates whether your agent called the right tools,
in the right order, without looping, within the step limit.

**Archal** — provides working clones of real services (GitHub, Stripe, Slack)
so your agent can make real API calls without touching real production data.

Together: your agent runs against a real GitHub clone, makes real API calls,
and gets a structured pass/fail evaluation with exact failure points.

## This is not a mock

The agent in this repo is powered by Groq (Llama 3.3 70B). It makes real
tool decisions, calls real GitHub API endpoints on the Archal twin, and
gets evaluated by real AgentEval logic.

```
Groq LLM decides which tool to call
    -> create_issue / add_label / list_issues / assign_issue / close_issue
    -> hits Archal GitHub twin (real API, not real GitHub)
    -> AgentEval records trace and evaluates pass/fail
    -> results appear in AgentEval dashboard
```

## Results

70% pass rate on first run against a real GitHub issue management agent:

```
GitHub Issue Manager Agent
==================================================
Pass rate : 70% (7/10)
==================================================
  [PASS] Create issue              2 steps  100% accuracy
  [FAIL] Missing repo              3 steps  exceeded_steps (max: 2)
  [FAIL] Issue with special chars  6 steps  exceeded_steps (max: 5)
  [PASS] List and create           3 steps  100% accuracy
  [PASS] Invalid label             3 steps  100% accuracy
  [PASS] Issue with long title     3 steps  100% accuracy
  [PASS] Missing title             2 steps  100% accuracy
  [PASS] Create and list           3 steps  100% accuracy
  [PASS] Invalid repo              3 steps  100% accuracy
  [FAIL] Multiple labels           3 steps  wrong_tool
```

## Architecture

```
archal-agenteval/
├── github_agent/
│   ├── agent.py      <- Groq-powered GitHub issue manager
│   └── server.py     <- FastAPI wrapper (AgentEval compatible)
├── archal_agenteval/
│   ├── __init__.py
│   └── runner.py     <- Archal twin client
├── scenarios/        <- markdown scenario files
└── demo.py
```

## Setup

```bash
# 1. Clone
git clone https://github.com/Fizza-Mukhtar/archal-agenteval
cd archal-agenteval

# 2. Install
pip install httpx groq fastapi uvicorn

# 3. Start Archal twin
npm install -g archal
archal login
archal twin start github

# 4. Set environment variables
export ARCHAL_TOKEN=archal_xxx
export ARCHAL_SESSION_ID=<session-id-from-above>
export GROQ_API_KEY=gsk_xxx

# 5. Start AgentEval backend (separate terminal)
# git clone https://github.com/Fizza-Mukhtar/agentEval
# docker compose up -d db redis
# uvicorn backend.app.main:app --reload --port 8000
# cd backend && python -m app.worker

# 6. Start the GitHub agent
python -m github_agent.server

# 7. Submit a test run to AgentEval
curl -X POST http://localhost:8000/api/v1/runs \
  -H "Content-Type: application/json" \
  -d '{
    "name": "GitHub Issue Manager Agent",
    "agent_endpoint": "http://localhost:9000/run",
    "task_description": "Create and manage GitHub issues in testuser/test-repo",
    "expected_tools": ["create_issue", "add_label", "list_issues"],
    "max_steps": 10
  }'

# 8. Open AgentEval dashboard
# http://localhost:3000
```

## GitHub Agent tools

The agent can call 5 tools against the Archal GitHub twin:

| Tool | What it does |
|---|---|
| `list_issues` | List open/closed issues in a repo |
| `create_issue` | Create a new issue with title and body |
| `add_label` | Add a label to an existing issue |
| `assign_issue` | Assign an issue to a user |
| `close_issue` | Close an issue with an optional comment |

## Why this matters

Without Archal: testing an agent against GitHub means real issues get created,
real notifications go out, real data gets modified.

Without AgentEval: you have no structured way to know if the agent called
the right tool, in the right order, or if it got stuck in a loop.

With both: clean state before every scenario, full execution trace,
exact failure point when something breaks, safe to run in CI.

---

AgentEval: https://github.com/Fizza-Mukhtar/agentEval
Archal: https://archal.ai
