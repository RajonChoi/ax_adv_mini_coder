---
name: call-subagent
description: "A skill that demonstrates how to call a subagent from the main agent. The main agent will delegate a specific task to the subagent and handle the response."
---

# Call Subagent Skill
This skill demonstrates how to call a subagent from the main agent. The main agent will delegate a specific task to the subagent and handle the response.

## How to call
**reference**: `src/agents/subagents.py`
- create_planner_agent
- create_coder_agent
- create_reviewer_agent

```python
from src.agents.subagents import create_planner_agent, create_coder_agent, create_reviewer_agent
from deepagents.graph import create_deep_agent

target_sub_agent_spec = create_planner_agent()  # or create_coder_agent(), create_reviewer_agent()

target_sub_agent = create_deep_agent(target_sub_agent_spec)

