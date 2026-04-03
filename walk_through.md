# walk_through

## Initial implementation
- Created `src/agents` package with agent and state modules.
- Implemented `create_coding_ai_agent` with deepagents and filesystem backend /projects.
- Added OpenRouter and Langfuse setup from environment variables.
- Added retry limits and a run helper `run_agent_task`.
- Kept architecture in mind: Planner/Coder/Reviewer and state separation.
