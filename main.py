import argparse
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from src.agents.coding_agent import run_agent_task


def main() -> None:
    parser = argparse.ArgumentParser(description="CODING AI AGENT (deepagents)")
    parser.add_argument("--task", help="Natural language coding task to solve", required=True)
    parser.add_argument("--project-root", default="projects", help="Workspace root path for FilesystemBackend")
    args = parser.parse_args()

    os.environ.setdefault("CODING_AGENT_PROJECT_ROOT", args.project_root)

    try:
        result = run_agent_task(args.task)
        print("=== Agent Output ===")
        print(result.get("output"))
        print("=== Workspace State ===")
        print(result.get("state"))
    except Exception as exc:
        print("Agent execution failed:", exc, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
