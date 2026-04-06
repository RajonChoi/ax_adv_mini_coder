from typing import Any, cast
import os
from pathlib import Path

from deepagents.graph import create_deep_agent

from .config import (
    backend_factory,
    ensure_openrouter_config,
    model_name,
    setup_langfuse,
)
from .state_models import WorkspaceState
from .subagents import get_all_subagents


SYSTEM_PROMPT = """
You are CODING AI AGENT (deepagents + filesystem + langfuse).
Goal:
- Read requirement documents and generate code.
- Refactor existing code.
- Fix bugs based on error logs.

Use the workflow:
0) make project-name based on requirement.
1) Planner: create file-by-file plan.
2) Coder: modify or write code accordingly.
3) Reviewer: verify syntax and requirement compliance.

Constraints:
- Use openrouter model from OPENROUTER_MODEL (default openrouter:gpt-4o-mini).
- Backend must be FilesystemBackend with root /projects, virtual_mode True.
- Save code changes to /projects/{project-name}/.
- Langfuse telemetry uses LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL.
- Recursion / retry limit 3.
"""


def create_coding_ai_agent() -> Any:
    ensure_openrouter_config()
    setup_langfuse()

    try:
        agent = create_deep_agent(
            model=model_name(),
            system_prompt=SYSTEM_PROMPT,
            backend=backend_factory,
            subagents=cast("list[Any]", get_all_subagents()),
            memory=["/memory/AGENTS.md"],
            max_iterations=3,
            name="coding-ai-agent",
            debug=True,
        )
    except ImportError as exc:
        raise RuntimeError(
            "Failed to initialize model runtime. Ensure openrouter support is installed: "
            "pip install langchain-openrouter"
        ) from exc

    return agent


def run_agent_task(requirement: str) -> Any:
    workspace_state = WorkspaceState()
    workspace_state.add_message("user", requirement)

    # 프로젝트 디렉토리 및 app.py 생성
    project_root = os.getenv("CODING_AGENT_PROJECT_ROOT", "projects")

    workspace_state.project_store(root_dir=project_root)

    agent = create_coding_ai_agent()

    # Pass the complete state to the agent, including messages history
    state_dict = {
        "messages": workspace_state.messages,
        "input": requirement,
        "current_workspace_state": workspace_state.current_workspace_state,
        "error_logs": workspace_state.error_logs,
    }
    output = agent.invoke(state_dict)

    workspace_state.add_message("assistant", str(output))

    return {
        "output": output,
        "state": workspace_state,
    }
