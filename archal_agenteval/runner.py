"""
archal_agenteval/runner.py

Runs AgentEval scenarios against Archal twins directly.
Uses the two-header pattern from Archal docs.
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ToolCall:
    step: int
    tool_name: str
    parameters: dict
    response: dict
    status: str
    duration_ms: int


@dataclass
class ScenarioResult:
    title: str
    task: str
    status: str
    failure_reason: str | None
    failure_detail: str | None
    tool_calls: list[ToolCall]
    twin_state_before: dict
    twin_state_after: dict
    duration_ms: int


@dataclass
class RunResult:
    twin: str
    task: str
    session_id: str
    started_at: str
    finished_at: str
    total: int
    passed: int
    failed: int
    pass_rate: float
    results: list[ScenarioResult] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"\nAgentEval + Archal Results",
            f"{'='*50}",
            f"Twin      : {self.twin}",
            f"Session   : {self.session_id[:8]}...",
            f"Pass rate : {self.pass_rate:.0%} ({self.passed}/{self.total})",
            f"{'='*50}",
        ]
        for r in self.results:
            icon = "PASS" if r.status == "passed" else "FAIL"
            lines.append(f"  [{icon}] {r.title}")
            if r.failure_detail:
                lines.append(f"         {r.failure_detail}")
            lines.append(f"         Steps: {len(r.tool_calls)}")
        lines.append("")
        return "\n".join(lines)


class ArchalTwinClient:
    def __init__(self, token: str, session_id: str, twin: str):
        self.token = token
        self.session_id = session_id
        self.twin = twin
        self.base_url = f"https://control.archal.ai/runtime/{session_id}/{twin}/api"

    @property
    def headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "x-archal-upstream-authorization": "Bearer ghp_test_bootstrap_token",
            "Content-Type": "application/json",
        }

    async def call(self, method: str, path: str, body: dict | None = None) -> dict:
        url = f"{self.base_url}{path}"
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.request(
                method=method, url=url, headers=self.headers, json=body,
            )
            return response.json()

    async def get_state(self) -> dict:
        try:
            repos = await self.call("GET", "/user/repos")
            issues = []
            if isinstance(repos, list):
                for repo in repos:
                    repo_issues = await self.call("GET", f"/repos/{repo['full_name']}/issues")
                    if isinstance(repo_issues, list):
                        issues.extend(repo_issues)
            return {"repos": repos, "issues": issues}
        except Exception as exc:
            logger.warning("Could not get state: %s", exc)
            return {}

    async def seed(self) -> None:
        result = await self.call("POST", "/user/repos", {
            "name": "test-repo",
            "description": "AgentEval test repo",
            "private": False,
        })
        logger.info("Seeded: %s", result.get("full_name", "unknown"))

    async def reset(self) -> None:
        try:
            repos = await self.call("GET", "/user/repos")
            if isinstance(repos, list):
                for repo in repos:
                    await self.call("DELETE", f"/repos/{repo['full_name']}")
        except Exception as exc:
            logger.warning("Reset failed: %s", exc)


async def call_agent(endpoint: str, task: str, twin_url: str, timeout: int = 30) -> dict | None:
    payload = {"task": task, "context": {"github_api_url": twin_url}}
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(endpoint, json=payload)
            response.raise_for_status()
            return response.json()
    except Exception as exc:
        logger.error("Agent call failed: %s", exc)
        return None


def evaluate(
    agent_response: dict | None,
    expected_tools: list[str],
    max_steps: int,
) -> tuple[str, str | None, str | None]:
    if agent_response is None:
        return "failed", "agent_error", "Agent did not respond"

    tool_calls = agent_response.get("tool_calls", [])
    actual_tools = [c.get("tool_name", "") for c in tool_calls]
    completed = agent_response.get("completed", False)

    if not tool_calls and not completed:
        return "failed", "agent_error", "Agent made no tool calls"

    if len(tool_calls) > max_steps:
        return "failed", "exceeded_steps", f"Used {len(tool_calls)} steps, max is {max_steps}"

    if not completed:
        return "failed", "no_completion", "Agent did not signal task completion"

    if expected_tools:
        missing = [t for t in expected_tools if t not in set(actual_tools)]
        if missing:
            return "failed", "wrong_tool", f"Expected tools not called: {', '.join(missing)}"

    return "passed", None, None


class ArchalAgentEvalRunner:
    def __init__(self, archal_token: str, session_id: str, agent_endpoint: str, twin: str = "github"):
        self.token = archal_token
        self.session_id = session_id
        self.agent_endpoint = agent_endpoint
        self.twin = twin
        self.client = ArchalTwinClient(archal_token, session_id, twin)

    async def run_scenario(self, title: str, task: str, expected_tools: list[str], max_steps: int = 10) -> ScenarioResult:
        logger.info("Running: %s", title)

        await self.client.reset()
        await self.client.seed()
        state_before = await self.client.get_state()

        start_ms = time.time()
        agent_response = await call_agent(
            endpoint=self.agent_endpoint,
            task=task,
            twin_url=self.client.base_url,
        )
        duration_ms = int((time.time() - start_ms) * 1000)
        state_after = await self.client.get_state()

        tool_calls = []
        if agent_response:
            for i, tc in enumerate(agent_response.get("tool_calls", []), 1):
                tool_calls.append(ToolCall(
                    step=i,
                    tool_name=tc.get("tool_name", "unknown"),
                    parameters=tc.get("parameters", {}),
                    response=tc.get("response", {}),
                    status=tc.get("status", "success"),
                    duration_ms=tc.get("duration_ms", 0),
                ))

        status, failure_reason, failure_detail = evaluate(agent_response, expected_tools, max_steps)

        logger.info("'%s': %s", title, status.upper())
        return ScenarioResult(
            title=title, task=task, status=status,
            failure_reason=failure_reason, failure_detail=failure_detail,
            tool_calls=tool_calls, twin_state_before=state_before,
            twin_state_after=state_after, duration_ms=duration_ms,
        )

    async def run(self, scenarios: list[dict], expected_tools: list[str], max_steps: int = 10) -> RunResult:
        started_at = datetime.now(timezone.utc).isoformat()
        results = []

        for scenario in scenarios:
            result = await self.run_scenario(
                title=scenario["title"],
                task=scenario["task"],
                expected_tools=expected_tools,
                max_steps=max_steps,
            )
            results.append(result)
            await asyncio.sleep(0.5)

        passed = sum(1 for r in results if r.status == "passed")
        total = len(results)

        return RunResult(
            twin=self.twin, task="Multiple scenarios", session_id=self.session_id,
            started_at=started_at, finished_at=datetime.now(timezone.utc).isoformat(),
            total=total, passed=passed, failed=total - passed,
            pass_rate=passed / total if total > 0 else 0.0, results=results,
        )