"""
github_agent/server.py

FastAPI server that wraps the GitHub issue manager agent.

AgentEval sends tasks here via POST /run.
This server calls the real Groq-powered agent against the Archal twin.

Usage:
    export ARCHAL_TOKEN=archal_xxx
    export ARCHAL_SESSION_ID=xxx
    export GROQ_API_KEY=gsk_xxx
    python github_agent/server.py

Then point AgentEval at: http://localhost:9000/run
"""

import logging
import os

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from github_agent.agent import run_agent

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s -- %(message)s",
)

logger = logging.getLogger(__name__)
app = FastAPI(title="GitHub Issue Manager Agent")

ARCHAL_TOKEN = os.environ.get("ARCHAL_TOKEN", "")
ARCHAL_SESSION_ID = os.environ.get("ARCHAL_SESSION_ID", "")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

GITHUB_API_URL = (
    f"https://control.archal.ai/runtime/{ARCHAL_SESSION_ID}/github/api"
    if ARCHAL_SESSION_ID
    else ""
)


class AgentRequest(BaseModel):
    task: str
    context: dict = {}


@app.post("/run")
async def run(request: AgentRequest) -> dict:
    """
    Receive a task from AgentEval and run the GitHub agent.
    Uses context.github_api_url if provided, otherwise uses env var.
    """
    github_url = request.context.get("github_api_url") or GITHUB_API_URL

    if not github_url:
        return {
            "tool_calls": [],
            "completed": False,
            "final_output": "Missing ARCHAL_SESSION_ID — cannot connect to GitHub twin",
        }

    if not GROQ_API_KEY:
        return {
            "tool_calls": [],
            "completed": False,
            "final_output": "Missing GROQ_API_KEY",
        }

    result = await run_agent(
        task=request.task,
        github_api_url=github_url,
        archal_token=ARCHAL_TOKEN,
        groq_api_key=GROQ_API_KEY,
        max_steps=10,
    )

    return result


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "agent": "github-issue-manager",
        "twin_connected": bool(ARCHAL_SESSION_ID),
        "llm": "groq/llama-3.3-70b-versatile",
    }


if __name__ == "__main__":
    if not ARCHAL_TOKEN:
        print("ERROR: Set ARCHAL_TOKEN")
    if not ARCHAL_SESSION_ID:
        print("ERROR: Set ARCHAL_SESSION_ID")
    if not GROQ_API_KEY:
        print("ERROR: Set GROQ_API_KEY")

    uvicorn.run("github_agent.server:app", host="0.0.0.0", port=9000, reload=True)