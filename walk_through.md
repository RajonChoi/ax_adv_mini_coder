# walk_through

## Phase 1: Initial implementation
- Created `src/agents` package with agent and state modules.
- Implemented `create_coding_ai_agent` with deepagents and filesystem backend /projects.
- Added OpenRouter and Langfuse setup from environment variables.
- Added retry limits and a run helper `run_agent_task`.
- Kept architecture in mind: Planner/Coder/Reviewer and state separation.

## Phase 2: State Management Improvements
- Updated `WorkspaceState.messages` to use LangGraph's `Annotated[list, add_messages]`
  - Automatic message reducer for conversation history management
  - Proper typing for LangGraph graph state
- Added required imports: `Annotated` from typing, `add_messages` from langgraph.graph
- Added default factory for messages field to prevent initialization errors
- Renamed `snapshot()` method to `project_store()` for clarity

## Phase 3: Automatic Project Management
- Added `project_name` field to `WorkspaceState` with UUID-based generation
  - Format: `project_xxxxxxxx` (8 hex chars from UUID)
  - Ensures unique project isolation across multiple runs
- Updated `run_agent_task()` to:
  - Auto-generate project folder: `{project_root}/{project_name}/`
  - Create initial `app.py` file in project directory
  - Include `project_name` in agent state dictionary
  - Added pathlib.Path import for robust file operations

## Phase 4: Web Service Implementation (Flask)
- Created `web_app.py` Flask application
  - GET `/` - Serves HTML UI
  - POST `/api/execute` - JSON endpoint for task execution
  - Returns: success status, output, and project_name
  - Error handling with proper HTTP status codes

- Created `templates/index.html` with modern UI:
  - Large textarea for task input
  - "입력" (Submit) and "초기화" (Reset) buttons
  - Real-time result display with loading animation
  - Project name badge showing generated project ID
  - Responsive design for mobile/desktop
  - Keyboard shortcut: Ctrl+Enter to submit
  - HTML escaping for XSS protection
  - Smooth animations and gradient styling

- Features:
  - Max upload size: 16MB
  - Localhost:5000 default configuration

## Phase 5: Server-Side Streaming UI (No JS)
- Modified `coding_agent.py` to add a generator `stream_agent_task(requirement)` utilizing `agent.stream()`.
- Yields chunked output grouped by LangGraph Nodes (Node-by-Node progression).
- Updated `web_app.py` to utilize Flask's native chunked response: `Response(generate_html_stream(task), mimetype='text/html')`.
- Refactored `templates/index.html`:
  - Removed all JavaScript / `fetch()` processing APIs.
  - Replaced the interface with a standard HTML `<form action="/api/execute" method="POST">`.
- Benefit: Live progression rendering inside the browser without involving client-side JS runtime.
