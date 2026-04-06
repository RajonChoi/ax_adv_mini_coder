"""
Configuration Module

This module contains shared configuration functions and factory methods
used by both the main agent and subagents. This separation prevents
circular imports and promotes code reusability.
"""

import os
from typing import Any

from deepagents.backends.filesystem import FilesystemBackend
from langfuse import Langfuse


def model_name() -> str:
    """Get the LLM model name from environment or default.

    Returns:
        str: Model identifier string for OpenRouter.
    """
    return os.getenv("OPENROUTER_MODEL", "openrouter:qwen/qwen3.6-plus:free")


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
        from langchain.chat_models import init_chat_model  # noqa: F401
    except ImportError as exc:
        raise ImportError(
            "langchain-openrouter is required for openrouter models; "
            "install with `pip install langchain-openrouter`"
        ) from exc


def setup_langfuse() -> None:
    """Initialize Langfuse telemetry and monitoring service.

    Reads LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY from environment.
    If either is missing, Langfuse integration is skipped gracefully.
    """
    public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
    secret_key = os.getenv("LANGFUSE_SECRET_KEY")
    base_url = os.getenv("LANGFUSE_BASE_URL", "http://localhost:3000")
    if public_key and secret_key:
        Langfuse(public_key=public_key, secret_key=secret_key, base_url=base_url)


def backend_factory(runtime: Any = None) -> FilesystemBackend:
    """Create a FilesystemBackend instance with configured root directory.

    Args:
        runtime: Optional runtime parameter (unused, for compatibility).

    Returns:
        FilesystemBackend: Configured file system backend with virtual_mode=True.
    """
    project_root = os.getenv("CODING_AGENT_PROJECT_ROOT", "projects")
    return FilesystemBackend(root_dir=project_root, virtual_mode=True)
