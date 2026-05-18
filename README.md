# AgentEval + Archal Integration

Test your AI agent against Archal's GitHub clone using AgentEval scenarios.

## What this does

Archal provides a working GitHub clone — same API, same behavior, nothing real affected.
AgentEval provides structured scenarios and pass/fail evaluation.
This integration wires them together.

## Folder structure

```
archal-agenteval/
├── .archal/
│   └── harness.mjs       <- calls your agent
├── .archal.json          <- Archal config
├── scenarios/
│   ├── create-issue.md
│   ├── close-stale-issues.md
│   └── label-and-assign.md
└── README.md
```

## Setup

```bash
npm install -g archal
archal login

export AGENT_ENDPOINT=http://localhost:9001/run
```

## Run

```bash
# Run all scenarios
archal run --docker

# Run a single scenario
archal run scenarios/create-issue.md --docker

# Run without Docker (sandbox mode)
archal run scenarios/create-issue.md --sandbox
```

## Verify harness works first

```bash
ARCHAL_ENGINE_TASK="Reply with OK" node .archal/harness.mjs
```

Should print: `{"text":"Task completed"}`

## How it works

1. Archal starts a GitHub clone
2. For each scenario, Archal sets up the starting state described in "## Setup"
3. Archal runs your harness with the task from "## Prompt"
4. Your harness calls your agent
5. Archal checks the "## Success Criteria" against the clone state
6. Pass/fail result with full trace

---

Built by Fizza Mukhtar
AgentEval: https://github.com/Fizza-Mukhtar/agentEval
Archal: https://archal.ai