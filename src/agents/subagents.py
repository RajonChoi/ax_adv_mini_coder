"""
Subagent Management Module

This module manages the configuration and creation of all compiled subagents
used by the Coding AI Agent. Each subagent is responsible for a specific phase
of the coding workflow: planning, implementation, and review.
"""

from typing import Any, List

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
Your responsibility is to implement the plan by making precise, minimal diffs.

Rules:
- Read files before editing.
- Mimic existing style, naming, and patterns.
- Prefer editing existing files over creating new ones.
- Only make changes that are directly requested — don't add features.
- Do not add comments unless asked.
- Keep responses concise; don't add preamble.

When implementing:
1. Apply file-by-file changes exactly as planned.
2. If something is ambiguous or blocked, stop and request clarification.
3. After changes, run focused tests/commands (if available) and fix one issue at a time.

Output: summarize what changed per file and any commands run."""

REVIEWER_SYSTEM_PROMPT = """You are a Code Review Agent (coder-reviewer).
Your responsibility is to verify correctness, scope, and project conventions.

Review checklist:
- Requirements satisfied (no missing acceptance criteria)
- Changes are minimal and directly requested (no scope creep)
- Consistent style and naming with the existing codebase
- No secrets or .env modifications
- Tests/linters (if present) pass
- No unsafe filesystem/shell behavior outside allowed workspace

Output:
- Pass/Fail
- Issues (must-fix)
- Suggestions (nice-to-have)
- Files reviewed + any commands run"""


# ============================================================================
# Subagent Factory Functions - Create compiled agents for each task
# ============================================================================


def create_planner_agent() -> dict:
    """Create and return a compiled planner subagent.

    The planner subagent is responsible for analyzing user requirements and
    breaking them down into concrete, actionable steps. It produces a detailed
    execution plan that guides the implementation phase.

    Returns:
        Any: Compiled subagent instance ready for use in the main agent.
    """
    ensure_openrouter_config()
    setup_langfuse()

    agent = {
        "model": model_name(),
        "system_prompt": PLANNER_SYSTEM_PROMPT,
        "backend": backend_factory,
        "memory": ["/memory/PLANNER.md"],
        "name": "coder-planner",
        "description": "Planning agent that creates detailed execution plans for coding tasks",
    }

    return agent


def create_coder_agent() -> dict:
    """Create and return a compiled coder subagent.

    The coder subagent is responsible for implementing the plan created by
    the planner. It writes and modifies files according to specifications,
    ensuring code quality and adherence to best practices.

    Returns:
        Any: Compiled subagent instance ready for use in the main agent.
    """
    ensure_openrouter_config()
    setup_langfuse()

    agent = {
        "model": model_name(),
        "system_prompt": CODER_SYSTEM_PROMPT,
        "backend": backend_factory,
        "memory": ["/memory/CODER.md"],
        "name": "coder-implementer",
        "description": "Coding agent that implements the plan by writing and modifying files",
    }

    return agent


def create_reviewer_agent() -> dict:
    """Create and return a compiled reviewer subagent.

    The reviewer subagent is responsible for quality assurance and verification.
    It checks that all code meets syntax requirements, follows best practices,
    and fulfills the original user requirements.

    Returns:
        Any: Compiled subagent instance ready for use in the main agent.
    """

    agent = {
        "model": model_name(),
        "system_prompt": REVIEWER_SYSTEM_PROMPT,
        "backend": backend_factory,
        "memory": ["/memory/REVIEWER.md"],
        "name": "coder-reviewer",
        "description": "Review agent that verifies code quality and requirement compliance",
    }

    return agent


def get_all_subagents() -> List[dict]:
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
        create_planner_agent(),
        create_coder_agent(),
        create_reviewer_agent(),
    ]
