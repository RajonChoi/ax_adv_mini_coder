"""
Subagent Management Module

This module manages the configuration and creation of all compiled subagents
used by the Coding AI Agent. Each subagent is responsible for a specific phase
of the coding workflow: planning, implementation, and review.
"""

from typing import Any, List

from deepagents.graph import create_deep_agent

from .config import (
    backend_factory,
    ensure_openrouter_config,
    model_name,
    setup_langfuse,
)


# ============================================================================
# Subagent System Prompts - Detailed instructions for each compiled agent
# ============================================================================

PLANNER_SYSTEM_PROMPT = """You are a Planning Agent (coder-planner).
Your responsibility is to analyze user requirements and create a detailed execution plan.

When creating a plan:
1. Break down the coding task into discrete file operations
2. Identify all files that need to be created or modified
3. Specify exact code changes required for each file
4. Provide a logical sequence of implementation steps
5. Consider dependencies between tasks

Format your response as a structured plan with clear sections for each file."""

CODER_SYSTEM_PROMPT = """You are a Coding Agent (coder-implementer).
Your responsibility is to implement code changes based on the provided plan.

When implementing:
1. Write clean, well-documented Python code
2. Follow PEP 8 style guidelines
3. Add comprehensive error handling with try-except blocks
4. Include type hints for function arguments and return values
5. Add docstrings to all functions and classes
6. Use meaningful variable names
7. Create or modify files according to the plan

Ensure all code is production-ready and thoroughly tested."""

REVIEWER_SYSTEM_PROMPT = """You are a Code Review Agent (coder-reviewer).
Your responsibility is to verify implementation quality and requirement compliance.

When reviewing:
1. Check for Python syntax errors
2. Verify all requirements are met
3. Inspect code quality and best practices
4. Identify potential bugs or edge cases
5. Confirm all specified files were created/modified
6. Check error handling is comprehensive
7. Validate type hints and documentation

Provide a detailed review report with:
- ✅ What passed
- ⚠️ Warnings or suggestions
- ❌ Critical issues if any"""


# ============================================================================
# Subagent Factory Functions - Create compiled agents for each task
# ============================================================================


def _create_planner_agent() -> Any:
    """Create and return a compiled planner subagent.

    The planner subagent is responsible for analyzing user requirements and
    breaking them down into concrete, actionable steps. It produces a detailed
    execution plan that guides the implementation phase.

    Returns:
        Any: Compiled subagent instance ready for use in the main agent.
    """
    ensure_openrouter_config()
    setup_langfuse()

    try:
        agent = create_deep_agent(
            model=model_name(),
            system_prompt=PLANNER_SYSTEM_PROMPT,
            backend=backend_factory,
            memory=["/memory/PLANNER.md"],
            name="coder-planner",
            debug=True,
        )
    except ImportError as exc:
        raise RuntimeError(
            "Failed to initialize planner agent. Ensure openrouter support is installed: "
            "pip install langchain-openrouter"
        ) from exc

    return agent


def _create_coder_agent() -> Any:
    """Create and return a compiled coder subagent.

    The coder subagent is responsible for implementing the plan created by
    the planner. It writes and modifies files according to specifications,
    ensuring code quality and adherence to best practices.

    Returns:
        Any: Compiled subagent instance ready for use in the main agent.
    """
    ensure_openrouter_config()
    setup_langfuse()

    try:
        agent = create_deep_agent(
            model=model_name(),
            system_prompt=CODER_SYSTEM_PROMPT,
            backend=backend_factory,
            memory=["/memory/CODER.md"],
            name="coder-implementer",
            debug=True,
        )
    except ImportError as exc:
        raise RuntimeError(
            "Failed to initialize coder agent. Ensure openrouter support is installed: "
            "pip install langchain-openrouter"
        ) from exc

    return agent


def _create_reviewer_agent() -> Any:
    """Create and return a compiled reviewer subagent.

    The reviewer subagent is responsible for quality assurance and verification.
    It checks that all code meets syntax requirements, follows best practices,
    and fulfills the original user requirements.

    Returns:
        Any: Compiled subagent instance ready for use in the main agent.
    """
    ensure_openrouter_config()
    setup_langfuse()

    try:
        agent = create_deep_agent(
            model=model_name(),
            system_prompt=REVIEWER_SYSTEM_PROMPT,
            backend=backend_factory,
            memory=["/memory/REVIEWER.md"],
            name="coder-reviewer",
            debug=True,
        )
    except ImportError as exc:
        raise RuntimeError(
            "Failed to initialize reviewer agent. Ensure openrouter support is installed: "
            "pip install langchain-openrouter"
        ) from exc

    return agent


def get_all_subagents() -> List[Any]:
    """Generate list of compiled subagent instances.

    This function orchestrates the creation of all subagents in the proper
    sequence: planner → implementer → reviewer. Each subagent is created
    as a fully compiled agent instance, ready for integration with the main agent.

    The order is crucial:
    1. Planner: Analyzes requirements and creates execution plan
    2. Implementer: Executes the plan by writing/modifying files
    3. Reviewer: Verifies implementation quality and compliance

    Returns:
        List[Any]: List of compiled subagent instances.
    """
    return [
        _create_planner_agent(),
        _create_coder_agent(),
        _create_reviewer_agent(),
    ]
