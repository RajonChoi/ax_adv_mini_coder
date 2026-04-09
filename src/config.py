"""
Configuration Module

This module contains shared configuration functions and factory methods
used by both the main agent and subagents. This separation prevents
circular imports and promotes code reusability.
"""

from dotenv import load_dotenv

load_dotenv()

import os
from typing import Any

from deepagents.backends.filesystem import FilesystemBackend


def ensure_openrouter_config() -> None:
    """Validate and configure OpenRouter API settings.

    Raises:
        EnvironmentError: If OPENROUTER_API_KEY is not set.
        ImportError: If langchain-openrouter package is not installed.
    """
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "OPENROUTER_API_KEY is required in environment for openrouter model."
        )
    os.environ["OPENROUTER_API_KEY"] = api_key

    # Ensure provider package is installed
    try:
        from langchain_openai import ChatOpenAI  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "langchain-openai is required for openrouter models; "
            "install with `pip install langchain-openai`"
        ) from exc


def backend_factory(runtime: Any = None) -> FilesystemBackend:
    """Create a FilesystemBackend instance with configured root directory.

    Args:
        runtime: Optional runtime parameter (unused, for compatibility).

    Returns:
        FilesystemBackend: Configured file system backend with virtual_mode=True.
    """
    project_root = os.getenv("CODING_AGENT_PROJECT_ROOT", "projects")
    return FilesystemBackend(root_dir=project_root, virtual_mode=True)
