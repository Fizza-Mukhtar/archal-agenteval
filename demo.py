"""
demo.py

End-to-end demo: Real Groq agent + AgentEval + Archal GitHub twin.

This is not a mock. This is a real LLM-powered agent making real
GitHub API calls against an Archal twin — evaluated by AgentEval.

Usage:
    export ARCHAL_TOKEN=archal_xxx
    export ARCHAL_SESSION_ID=a74e5622-xxx
    export GROQ_API_KEY=gsk_xxx
    python demo.py
"""

import asyncio
import logging
import os

from archal_agenteval import ArchalAgentEvalRunner
from github_agent.agent import run_agent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s -- %(message)s",
)

ARCHAL_TOKEN = os.environ.get("ARCHAL_TOKEN", "")
ARCHAL_SESSION_ID = os.environ.get("ARCHAL_SESSION_ID", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GITHUB_API_URL = f"https://control.archal.ai/runtime/{ARCHAL_SESSION_ID}/github/api"


async def run_single_task(task: str, label: str) -> dict:
    """Run one task directly through the agent and return AgentEval-compatible result."""
    print(f"\nRunning: {label}")
    print(f"Task: {task}")
    print("-" * 40)

    result = await run_agent(
        task=task,
        github_api_url=GITHUB_API_URL,
        archal_token=ARCHAL_TOKEN,
        groq_api_key=GROQ_API_KEY,
        max_steps=10,
    )

    print(f"Tools called: {[tc['tool_name'] for tc in result['tool_calls']]}")
    print(f"Completed: {result['completed']}")
    print(f"Output: {result['final_output'][:100]}")
    return result


async def main():
    if not all([ARCHAL_TOKEN, ARCHAL_SESSION_ID, GROQ_API_KEY]):
        print("ERROR: Missing environment variables")
        print("  export ARCHAL_TOKEN=archal_xxx")
        print("  export ARCHAL_SESSION_ID=xxx")
        print("  export GROQ_API_KEY=gsk_xxx")
        return

    print("\nAgentEval + Archal + Real Groq Agent")
    print("=" * 50)
    print(f"LLM     : Groq / llama-3.3-70b-versatile")
    print(f"Twin    : Archal GitHub clone")
    print(f"Session : {ARCHAL_SESSION_ID[:8]}...")
    print()

    # Seed the twin with a repo first
    from archal_agenteval.runner import ArchalTwinClient
    client = ArchalTwinClient(ARCHAL_TOKEN, ARCHAL_SESSION_ID, "github")
    await client.reset()
    await client.seed()
    print("Twin seeded with testuser/test-repo")
    print()

    # Run 3 real tasks through the agent
    scenarios = [
        {
            "label": "Create an issue",
            "task": "Create a GitHub issue titled 'bug: login fails on mobile' in testuser/test-repo. Body should describe that iOS users on version 16+ cannot log in.",
            "expected_tools": ["create_issue"],
        },
        {
            "label": "Create and label an issue",
            "task": "Create a GitHub issue titled 'feature: add dark mode' in testuser/test-repo and add the label 'enhancement' to it.",
            "expected_tools": ["create_issue", "add_label"],
        },
        {
            "label": "List issues",
            "task": "List all open issues in testuser/test-repo and tell me how many there are.",
            "expected_tools": ["list_issues"],
        },
    ]

    all_results = []

    for scenario in scenarios:
        result = await run_single_task(scenario["task"], scenario["label"])

        # Evaluate with AgentEval logic
        actual_tools = [tc["tool_name"] for tc in result["tool_calls"]]
        expected = scenario["expected_tools"]
        missing = [t for t in expected if t not in set(actual_tools)]

        if not result["completed"]:
            status = "FAIL"
            reason = "Agent did not complete the task"
        elif missing:
            status = "FAIL"
            reason = f"Expected tools not called: {missing}"
        else:
            status = "PASS"
            reason = None

        all_results.append({
            "label": scenario["label"],
            "status": status,
            "reason": reason,
            "steps": len(result["tool_calls"]),
            "tools": actual_tools,
        })

        await asyncio.sleep(1)

    # Print final summary
    passed = sum(1 for r in all_results if r["status"] == "PASS")
    total = len(all_results)

    print("\n" + "=" * 50)
    print("AgentEval Results")
    print("=" * 50)
    print(f"Pass rate : {passed}/{total} ({passed/total:.0%})")
    print()

    for r in all_results:
        icon = "PASS" if r["status"] == "PASS" else "FAIL"
        print(f"  [{icon}] {r['label']}")
        print(f"         Tools : {r['tools']}")
        print(f"         Steps : {r['steps']}")
        if r["reason"]:
            print(f"         Reason: {r['reason']}")
    print()


if __name__ == "__main__":
    asyncio.run(main())