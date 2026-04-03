# Deep Agent maker
## GOAL
- This Project is to make a CODING Agent
- **Main Capabilities**:
  - Read requirement documents and generate code.
  - Refactor existing code.
  - Fix bugs based on error logs.

## Requirements
- use deepagents
- backend is FilesystemBackend to `/projects`
  - I will run this project using `Docker run -v /my/source/path:/projects ...`
- make monitoring with langfuse
  - langfuse is running in docker with 'http://localhost:3000'
  - `.env` has all information to connect langfuse
- Execution Environment: Code execution (if required for testing/linting) must be strictly isolated to the `/projects` directory to prevent system tampering.
- make walk_through.md and update after every review to **WRITE** `what you did`.

## Architecture & State Management
- **State Definition**: Graph state must clearly separate `messages`, `currentWorkspaceState` (files modified), and `errorLogs`.
- **Agent Workflow**:
  - `Planner`: Analyzes requirements and creates a file-by-file action plan.
  - `Coder`: Executes the plan by writing/modifying code.
  - `Reviewer`: Checks for syntax errors or requirement mismatches.

## Constraints
- select opensource model via openrouter
  - API KEY for openrouter is in `.env`
- do not use MCP(Server, Client, Host ALL)
  - use skills and tools **[UPDATED]** implemented as native functions.
- if you need to make SubAgent, Always with CompiledGraph
  - and make skill to call that CompliedGraph
- **Loop Limits**: Set a strict recursion limit (e.g., maximum 3 retries for fixing a compilation error) to prevent infinite loops and token waste.

## Code Style
- only use `snake_case` depending on the language convention.
- many folders, less lines
- **Separation of Concerns**: Isolate `nodes`, `edges`, `states`, and `tools` into separate directories (e.g., `src/agents/`, `src/tools/`, `src/states/`).
