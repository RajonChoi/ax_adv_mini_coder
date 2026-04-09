from re import sub
from typing import Any, cast
import os
import json
import logging
from dotenv import load_dotenv
from langfuse import observe, get_client


load_dotenv()

# Configure basic logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from deepagents.graph import create_deep_agent
from ._llm import get_llm
from .config import (
    backend_factory,
    ensure_openrouter_config,
)
from .state_models import WorkspaceState
from .subagents import get_all_subagents, call_dynamic_subagent
from .memory_pg import MemoryManager, delete_user_characteristic, save_user_characteristic

from langfuse.langchain import CallbackHandler

SYSTEM_PROMPT = """
# You are CODING AI AGENT (deepagents + filesystem + langfuse).
## Goal:
- Read requirement documents and generate code.
- Refactor existing code.
- Fix bugs based on error logs.
- Automatically identify personal traits (location, hobbies, etc.) in user prompt and save them via `save_user_characteristic` tool.
- Dynamically generate specialized SubAgents using `call_dynamic_subagent` if a custom role is needed (e.g. data-analysis, design, translation).

### Use Subagents for specialized tasks:
- Planner: create file-by-file plan.
- Coder: modify or write code accordingly.
- Reviewer: verify syntax and requirement compliance.

### Workflow:
1. Analyze the requirement and current workspace state.
2. Plan the necessary steps and files to modify or create.
3. Make project-name based on requirement.
4. Execute coding tasks, ensuring all changes are saved to /projects/{project-name}/.
5. If errors occur, analyze error logs and fix the code iteratively.

### Exceptions:
- User send simple messages(under 20 characters), you can answer directly without subagents.
- User can call subagent directly via `call_dynamic_subagent` tool if they want to delegate specific tasks to a specialized agent.
- Also user can call subagents in your reasoning process, then you should run only that subagent to complete the specific task.

### Constraints:
- Use openrouter model from OPENROUTER_MODEL (default openrouter:GLM-5).
- Backend must be FilesystemBackend with root /projects, virtual_mode True.
- Save code changes to /projects/{project-name}/.
- Langfuse telemetry uses LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL.
- Recursion / retry limit 5.

{date}
"""


def create_coding_ai_agent() -> Any:
    langfuse_handler = CallbackHandler()
    main_llm = get_llm("glm")
    main_llm.callbacks = [langfuse_handler]

    ensure_openrouter_config()

    # Fetch user profile from PostgreSQL DB
    manager = MemoryManager()
    user_profile = manager.get_user_profile("default_user")

    # Inject memory context
    extended_prompt = SYSTEM_PROMPT
    if user_profile:
        extended_prompt += "\n\nUser Profile & Characteristics:\n" + json.dumps(
            user_profile, indent=2
        )

    try:
        agent = create_deep_agent(
            model=get_llm("glm"),
            system_prompt=extended_prompt,
            backend=backend_factory,
            subagents=cast("list[Any]", get_all_subagents()),
            memory=["/memory/AGENTS.md", "/memory/personal.md", "/memory/project.md"],
            tools=[save_user_characteristic, delete_user_characteristic, call_dynamic_subagent],
            name="coding-ai-agent",
            debug=True,
        )

    except ImportError as exc:
        raise RuntimeError(
            "Failed to initialize model runtime. Ensure openrouter support is installed: "
            "pip install langchain-openrouter"
        ) from exc

    return agent


@observe(name="Coding-Agent-Workflow")
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

    # langfuse flush
    get_client().flush()

    return {
        "output": output,
        "state": workspace_state,
    }


def stream_agent_task(requirement: str, history: list = []) -> Any:
    workspace_state = WorkspaceState()

    if history:
        for msg in history:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            workspace_state.add_message(role, content)

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
        nodes_executed = []
        final_response = None
        all_messages = []

        # Check if the agent supports streaming (LangGraph CompiledGraph)
        if hasattr(agent, "stream"):
            logger.info("Agent supports streaming, calling agent.stream()")
            for event in agent.stream(state_dict):
                logger.debug(f"Received stream event from agent: {event.keys()}")
                for node_name, values in event.items():
                    nodes_executed.append(node_name)
                    logger.info(f"Node completed: {node_name}")
                    content_str = ""
                    # Extract readable content from LangGraph state updates
                    if isinstance(values, dict):
                        messages = values.get("messages", [])
                        # LangGraph sometimes wraps lists in an Overwrite object
                        if hasattr(messages, "value"):
                            messages = messages.value

                        if messages and isinstance(messages, list):
                            all_messages = messages  # 모든 메시지 저장
                            last_msg = messages[-1]
                            if hasattr(last_msg, "content"):
                                content_str = last_msg.content
                            elif isinstance(last_msg, dict) and "content" in last_msg:
                                content_str = str(last_msg["content"])
                            else:
                                content_str = str(last_msg)
                        elif "memory_contents" in values:
                            content_str = f"System Memory Context Updated: {list(values['memory_contents'].keys())}"
                        else:
                            content_str = (
                                f"Internal State Updated: {list(values.keys())}"
                            )
                    else:
                        content_str = str(values)

                    # Limit the length if it's too huge
                    if len(content_str) > 5000:
                        content_str = content_str[:5000] + "...(truncated)"

                    # Yield clean string for frontend
                    yield {
                        "type": "node",
                        "node_name": node_name,
                        "content": content_str.strip(),
                    }

            # 스트림 완료 후 마지막 메시지 추출
            if all_messages:
                last_message = all_messages[-1]
                if hasattr(last_message, "content"):
                    final_response = last_message.content
                elif isinstance(last_message, dict) and "content" in last_message:
                    final_response = last_message["content"]
                else:
                    final_response = str(last_message)
        else:
            logger.info("Agent does not support streaming, falling back to invoke()")
            output = agent.invoke(state_dict)
            final_response = str(output)
            nodes_executed = ["invoke"]
            yield {"type": "node", "node_name": "final", "content": str(output)}
        logger.info("Agent execution completed successfully.")
    except Exception as e:
        logger.error(f"Error during agent execution: {e}", exc_info=True)
        yield {"type": "node", "node_name": "error", "content": str(e)}

    # Determine response type based on nodes executed
    complex_nodes = {
        "Planner",
        "Coder",
        "Reviewer",
        "GenerateCoding",
        "CodeModifier",
        "planner",
        "coder",
        "reviewer",
    }
    nodes_str = str(nodes_executed)
    logger.info(f"DEBUG: nodes_executed = {nodes_executed}")
    logger.info(f"DEBUG: nodes_str = {nodes_str}")
    is_complex = any(node in nodes_str for node in complex_nodes)
    logger.info(f"DEBUG: is_complex = {is_complex}")

    # Prepare final response message
    if is_complex:
        # 코딩 작업 완료시 메시지
        response_message = (
            "✅ 작업이 완료됐습니다.\n📂 projects/ 아래에 보관하였습니다."
        )
    else:
        # 간단한 응답
        response_message = final_response or "작업이 완료되었습니다."

    yield {
        "type": "end",
        "response_type": "complex" if is_complex else "simple",
        "final_response": response_message,
    }
