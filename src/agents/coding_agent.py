from typing import Any, cast
import os
from pathlib import Path
import json
import logging

# Configure basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

from deepagents.graph import create_deep_agent

from .config import (
    backend_factory,
    ensure_openrouter_config,
    model,
    setup_langfuse,
)
from .state_models import WorkspaceState
from .subagents import get_all_subagents, call_dynamic_subagent
from .memory_pg import MemoryManager, save_user_characteristic


SYSTEM_PROMPT = """
You are CODING AI AGENT (deepagents + filesystem + langfuse).
Goal:
- Read requirement documents and generate code.
- Refactor existing code.
- Fix bugs based on error logs.
- Automatically identify personal traits (location, hobbies, etc.) in user prompt and save them via `save_user_characteristic` tool.
- Dynamically generate specialized SubAgents using `call_dynamic_subagent` if a custom role is needed (e.g. data-analysis, design, translation).

Use the workflow:
0) make project-name based on requirement.
1) Planner: create file-by-file plan.
2) Coder: modify or write code accordingly.
3) Reviewer: verify syntax and requirement compliance.

Constraints:
- Use openrouter model from OPENROUTER_MODEL (default openrouter:gpt-5.4-mini).
- Backend must be FilesystemBackend with root /projects, virtual_mode True.
- Save code changes to /projects/{project-name}/.
- Langfuse telemetry uses LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL.
- Recursion / retry limit 5.
"""


def create_coding_ai_agent() -> Any:
    ensure_openrouter_config()
    setup_langfuse()

    # Fetch user profile from PostgreSQL DB
    manager = MemoryManager()
    user_profile = manager.get_user_profile("default_user")

    # Inject memory context
    extended_prompt = SYSTEM_PROMPT
    if user_profile:
        extended_prompt += "\n\nUser Profile & Characteristics:\n" + json.dumps(user_profile, indent=2)

    try:
        agent = create_deep_agent(
            model=model(),
            system_prompt=extended_prompt,
            backend=backend_factory,
            subagents=cast("list[Any]", get_all_subagents()),
            memory=["/memory/AGENTS.md", "/memory/personal.md", "/memory/project.md"],
            tools=[save_user_characteristic, call_dynamic_subagent],
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


def stream_agent_task(requirement: str) -> Any:
    workspace_state = WorkspaceState()
    workspace_state.add_message("user", requirement)

    project_root = os.getenv("CODING_AGENT_PROJECT_ROOT", "projects")
    workspace_state.project_store(root_dir=project_root)

    agent = create_coding_ai_agent()

    state_dict = {
        "messages": workspace_state.messages,
        "input": requirement,
        "current_workspace_state": workspace_state.current_workspace_state,
        "error_logs": workspace_state.error_logs,
    }

    yield {"type": "start", "project_name": "coding-project"}

    try:
        logger.info("Starting agent stream execution...")
        # Check if the agent supports streaming (LangGraph CompiledGraph)
        if hasattr(agent, "stream"):
            logger.info("Agent supports streaming, calling agent.stream()")
            for event in agent.stream(state_dict):
                logger.debug(f"Received stream event from agent: {event.keys()}")
                for node_name, values in event.items():
                    logger.info(f"Node completed: {node_name}")
                    content_str = ""
                    # Extract readable content from LangGraph state updates
                    if isinstance(values, dict):
                        messages = values.get('messages', [])
                        # LangGraph sometimes wraps lists in an Overwrite object
                        if hasattr(messages, 'value'):
                            messages = messages.value
                            
                        if messages and isinstance(messages, list):
                            last_msg = messages[-1]
                            if hasattr(last_msg, 'content'):
                                content_str = last_msg.content
                            elif isinstance(last_msg, dict) and 'content' in last_msg:
                                content_str = str(last_msg['content'])
                            else:
                                content_str = str(last_msg)
                        elif "memory_contents" in values:
                             content_str = f"System Memory Context Updated: {list(values['memory_contents'].keys())}"
                        else:
                             content_str = f"Internal State Updated: {list(values.keys())}"
                    else:
                        content_str = str(values)

                    # Limit the length if it's too huge
                    if len(content_str) > 5000:
                        content_str = content_str[:5000] + "...(truncated)"
                    
                    # Yield clean string for frontend
                    yield {"type": "node", "node_name": node_name, "content": content_str.strip()}
        else:
            logger.info("Agent does not support streaming, falling back to invoke()")
            output = agent.invoke(state_dict)
            yield {"type": "node", "node_name": "final", "content": str(output)}
        logger.info("Agent execution completed successfully.")
    except Exception as e:
        logger.error(f"Error during agent execution: {e}", exc_info=True)
        yield {"type": "node", "node_name": "error", "content": str(e)}

    yield {"type": "end"}
