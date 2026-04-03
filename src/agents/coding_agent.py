import os
from typing import Any, cast

from deepagents.backends.filesystem import FilesystemBackend
from deepagents.graph import create_deep_agent
from deepagents.middleware.subagents import SubAgent
from langfuse import Langfuse

from .state_models import WorkspaceState


SYSTEM_PROMPT = """
You are CODING AI AGENT (deepagents + filesystem + langfuse).
Goal:
- Read requirement documents and generate code.
- Refactor existing code.
- Fix bugs based on error logs.

Use the workflow:
1) Planner: create file-by-file plan.
2) Coder: modify or write code accordingly.
3) Reviewer: verify syntax and requirement compliance.

Constraints:
- Use openrouter model from OPENROUTER_MODEL (default openrouter:gpt-4o-mini).
- Backend must be FilesystemBackend with root /projects, virtual_mode True.
- Langfuse telemetry uses LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL.
- Recursion / retry limit 3.
"""


def _model_name() -> str:
    return os.getenv("OPENROUTER_MODEL", "openrouter:qwen/qwen3.6-plus:free")


def _ensure_openrouter_config() -> None:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENROUTER_API_KEY is required in environment for openrouter model."
        )
    os.environ["OPENROUTER_API_KEY"] = api_key

    # Ensure provider package is installed
    try:
        from langchain.chat_models import init_chat_model  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "langchain-openrouter is required for openrouter models; "
            "install with `pip install langchain-openrouter`"
        ) from exc


def _setup_langfuse() -> None:
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    base_url = os.getenv("LANGFUSE_BASE_URL", "http://localhost:3000")
    if public_key and secret_key:
        Langfuse(public_key=public_key, secret_key=secret_key, base_url=base_url)


def _backend_factory(runtime: Any = None):
    project_root = os.getenv("CODING_AGENT_PROJECT_ROOT", "/projects")
    return FilesystemBackend(root_dir=project_root, virtual_mode=True)


def _plan_subagent_definitions() -> list[SubAgent]:
    return [
        {
            "name": "coder-planner",
            "description": "Generate a concrete action plan for coding tasks.",
            "system_prompt": "Planner: produce a list of file operations and code changes.",
        },
        {
            "name": "coder-implementer",
            "description": "Implement code changes from plan and write files.",
            "system_prompt": "Coder: write or edit files with best practices and tests.",
        },
        {
            "name": "coder-reviewer",
            "description": "Review changed files for syntax and requirement compliance.",
            "system_prompt": "Reviewer: check for errors and report issues in the workspace.",
        },
    ]


def create_coding_ai_agent() -> Any:
    _ensure_openrouter_config()
    _setup_langfuse()

    try:
        agent = create_deep_agent(
            model=_model_name(),
            system_prompt=SYSTEM_PROMPT,
            backend=_backend_factory,
            subagents=cast("list[Any]", _plan_subagent_definitions()),
            memory=["/memory/AGENTS.md"],
            name="coding-ai-agent",
            debug=True,
        )
    except ImportError as exc:
        raise RuntimeError(
            "Failed to initialize model runtime. Ensure openrouter support is installed: "
            "pip install langchain-openrouter"
        ) from exc

    return agent.with_retry(stop_after_attempt=3)


def run_agent_task(requirement: str) -> Any:
    workspace_state = WorkspaceState()
    workspace_state.add_message("user", requirement)
    workspace_state.snapshot(
        root_dir=os.getenv("CODING_AGENT_PROJECT_ROOT", "/projects")
    )

    agent = create_coding_ai_agent()
    output = agent.invoke({"input": requirement})

    workspace_state.add_message("assistant", str(output))

    return {
        "output": output,
        "state": workspace_state,
    }
