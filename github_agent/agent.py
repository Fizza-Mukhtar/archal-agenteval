"""
github_agent/agent.py

A real AI agent that manages GitHub issues.

Powered by Groq (Llama 3.3 70B) with real GitHub API tool calls.
Runs against Archal's GitHub twin so nothing real is affected.

Tools:
    list_issues    -- list open issues in a repo
    create_issue   -- create a new issue
    add_label      -- add a label to an issue
    assign_issue   -- assign an issue to a user
    close_issue    -- close an issue with a comment
"""

import json
import logging
import time
from typing import Any

import httpx
from groq import Groq

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# GitHub API client (hits Archal twin, not real GitHub)
# ---------------------------------------------------------------------------

class GitHubClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url.rstrip("/")
        self.headers = {
            "Authorization": f"Bearer {token}",
            "x-archal-upstream-authorization": "Bearer ghp_test_bootstrap_token",
            "Content-Type": "application/json",
            "Accept": "application/vnd.github.v3+json",
        }

    async def get(self, path: str) -> Any:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f"{self.base_url}{path}", headers=self.headers)
            return r.json()

    async def post(self, path: str, body: dict) -> Any:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(f"{self.base_url}{path}", headers=self.headers, json=body)
            return r.json()

    async def patch(self, path: str, body: dict) -> Any:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.patch(f"{self.base_url}{path}", headers=self.headers, json=body)
            return r.json()


# ---------------------------------------------------------------------------
# Tool definitions (sent to Groq)
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_issues",
            "description": "List open issues in a GitHub repository",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string", "description": "Repository owner username"},
                    "repo": {"type": "string", "description": "Repository name"},
                    "state": {"type": "string", "enum": ["open", "closed", "all"], "default": "open"},
                },
                "required": ["owner", "repo"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_issue",
            "description": "Create a new issue in a GitHub repository",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "title": {"type": "string", "description": "Issue title"},
                    "body": {"type": "string", "description": "Issue body/description"},
                },
                "required": ["owner", "repo", "title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_label",
            "description": "Add a label to an existing GitHub issue",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "issue_number": {"type": "integer", "description": "Issue number"},
                    "label": {"type": "string", "description": "Label name to add"},
                },
                "required": ["owner", "repo", "issue_number", "label"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "assign_issue",
            "description": "Assign a GitHub issue to a user",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "issue_number": {"type": "integer"},
                    "assignee": {"type": "string", "description": "Username to assign"},
                },
                "required": ["owner", "repo", "issue_number", "assignee"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "close_issue",
            "description": "Close a GitHub issue with an optional comment",
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "issue_number": {"type": "integer"},
                    "comment": {"type": "string", "description": "Comment to add before closing"},
                },
                "required": ["owner", "repo", "issue_number"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Tool executor
# ---------------------------------------------------------------------------

async def execute_tool(name: str, args: dict, github: GitHubClient) -> Any:
    """Execute a tool call against the Archal GitHub twin."""

    if name == "list_issues":
        state = args.get("state", "open")
        return await github.get(f"/repos/{args['owner']}/{args['repo']}/issues?state={state}")

    elif name == "create_issue":
        body = {"title": args["title"], "body": args.get("body", "")}
        return await github.post(f"/repos/{args['owner']}/{args['repo']}/issues", body)

    elif name == "add_label":
        return await github.post(
            f"/repos/{args['owner']}/{args['repo']}/issues/{args['issue_number']}/labels",
            {"labels": [args["label"]]},
        )

    elif name == "assign_issue":
        return await github.patch(
            f"/repos/{args['owner']}/{args['repo']}/issues/{args['issue_number']}",
            {"assignees": [args["assignee"]]},
        )

    elif name == "close_issue":
        if args.get("comment"):
            await github.post(
                f"/repos/{args['owner']}/{args['repo']}/issues/{args['issue_number']}/comments",
                {"body": args["comment"]},
            )
        return await github.patch(
            f"/repos/{args['owner']}/{args['repo']}/issues/{args['issue_number']}",
            {"state": "closed"},
        )

    else:
        return {"error": f"Unknown tool: {name}"}


# ---------------------------------------------------------------------------
# Main agent
# ---------------------------------------------------------------------------

async def run_agent(
    task: str,
    github_api_url: str,
    archal_token: str,
    groq_api_key: str,
    max_steps: int = 10,
) -> dict:
    """
    Run the GitHub issue manager agent on a task.

    Returns AgentEval-compatible response:
    {
        "tool_calls": [...],
        "completed": bool,
        "final_output": str,
    }
    """
    groq = Groq(api_key=groq_api_key)
    github = GitHubClient(base_url=github_api_url, token=archal_token)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a GitHub issue management agent. "
                "Use the available tools to complete the task. "
                "The repository owner is always 'testuser' and repo is 'test-repo' "
                "unless specified otherwise. "
                "Call tools one at a time. When done, say 'Task completed.' and stop."
            ),
        },
        {"role": "user", "content": task},
    ]

    tool_calls_recorded = []
    steps = 0

    logger.info("Agent starting task: %s", task[:80])

    while steps < max_steps:
        steps += 1

        response = groq.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0,
            max_tokens=1024,
        )

        message = response.choices[0].message

        # No more tool calls — agent is done
        if not message.tool_calls:
            final_output = message.content or "Task completed."
            logger.info("Agent finished: %s", final_output[:80])
            return {
                "tool_calls": tool_calls_recorded,
                "completed": True,
                "final_output": final_output,
            }

        # Execute each tool call
        messages.append({"role": "assistant", "content": message.content, "tool_calls": message.tool_calls})

        for tc in message.tool_calls:
            tool_name = tc.function.name
            try:
                args = json.loads(tc.function.arguments)
            except json.JSONDecodeError:
                args = {}

            logger.info("Step %d: calling %s(%s)", steps, tool_name, args)

            start = time.time()
            result = await execute_tool(tool_name, args, github)
            duration_ms = int((time.time() - start) * 1000)

            tool_calls_recorded.append({
                "tool_name": tool_name,
                "parameters": args,
                "response": result,
                "status": "success" if "error" not in str(result)[:50] else "failed",
                "duration_ms": duration_ms,
            })

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, default=str),
            })

    logger.warning("Agent hit max steps (%d)", max_steps)
    return {
        "tool_calls": tool_calls_recorded,
        "completed": False,
        "final_output": "Max steps reached",
    }