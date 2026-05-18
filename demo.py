"""
demo.py

AgentEval + Archal integration demo.

Usage:
    # Terminal 1 - start twin
    archal twin start github

    # Terminal 2 - run demo
    export ARCHAL_TOKEN=archal_xxx
    export ARCHAL_SESSION_ID=83b5a9ce-xxxx
    export AGENT_ENDPOINT=http://localhost:9001/run
    python demo.py
"""

import asyncio
import logging
import os

from archal_agenteval import ArchalAgentEvalRunner

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s -- %(message)s",
)


async def main():
    token = os.environ.get("ARCHAL_TOKEN")
    session_id = os.environ.get("ARCHAL_SESSION_ID")
    agent_endpoint = os.environ.get("AGENT_ENDPOINT", "http://localhost:9001/run")

    if not token or not session_id:
        print("ERROR: Set ARCHAL_TOKEN and ARCHAL_SESSION_ID")
        print()
        print("  archal twin start github")
        print("  export ARCHAL_TOKEN=archal_xxx")
        print("  export ARCHAL_SESSION_ID=<session-id-from-above>")
        return

    print("\nAgentEval + Archal Integration")
    print("=" * 50)
    print(f"Session : {session_id[:8]}...")
    print(f"Agent   : {agent_endpoint}")
    print()

    runner = ArchalAgentEvalRunner(
        archal_token=token,
        session_id=session_id,
        agent_endpoint=agent_endpoint,
        twin="github",
    )

    scenarios = [
        {
            "title": "Happy path: create issue",
            "task": "Create a GitHub issue titled 'bug: login fails on mobile' in testuser/test-repo",
        },
        {
            "title": "Happy path: book a flight (mock agent default)",
            "task": "Book a happy flight from Karachi to Dubai",
        },
        {
            "title": "Failure case: missing info",
            "task": "Book a fail flight",
        },
    ]

    results = await runner.run(
        scenarios=scenarios,
        expected_tools=["search_flights", "check_availability", "book_ticket"],
        max_steps=10,
    )

    print(results.summary())


if __name__ == "__main__":
    asyncio.run(main())