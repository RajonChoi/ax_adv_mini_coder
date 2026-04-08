# **🤖 Deep-Coding AI Agent Specification (AGENT.md)**

## **1\. Project Overview & Goal**

This project aims to build a **Coding AI Agent that autonomously executes and learns from the actual software development lifecycle**, rather than functioning as a simple code-generation chatbot.

Using the deepagents framework as the core reference, the agent will perform requirement analysis, code writing, refactoring, and bug fixing based on error logs.

### **1.1. Three Core Implementation Goals**

1. **Long-Term Memory & Knowledge Storage System:** Permanently accumulate and reuse user feedback and domain knowledge.  
2. **Dynamic SubAgent Lifecycle Management:** Dynamically generate agents at runtime based on task characteristics, strictly tracking their states and ensuring proper cleanup.  
3. **Agentic Loop Resilience & Safety:** Establish explicit defense and recovery strategies (Fallback/Safe Stop) against LLM response delays, infinite loops, and critical error situations.

## ---

**2\. Environment Configuration & Core Architecture**

* **Execution Environment:** All code execution (testing/linting, etc.) and file system access (FilesystemBackend) must be strictly isolated within the /projects directory to protect the host system. (Utilize the Docker run \-v /my/source/path:/projects ... approach).  
* **Monitoring:** Integrate Langfuse to monitor all prompts, tool calls, and error logs. (Langfuse runs inside Docker at http://localhost:3000; connection info is in .env).  
* **Model Configuration:** Prioritize open-source models (e.g., **Qwen3.5-31B**) via the OpenRouter API (API keys stored in .env).  
* **Tooling:** Do NOT use MCP (Server, Client, Host). All Skills and Tools must be explicitly implemented as Native Functions and registered within deepagents.  
* **Logging:** The /projects/walk\_through.md file must be updated after every review and major task completion to explicitly record **"what you did."**

## ---

**3\. Core Requirement 1: Long-Term Memory & Knowledge Storage System**

Rather than maintaining a simple conversation history, the context must be separated into three distinct tiers. These must be permanently stored in the file system (e.g., src/memory/ or /projects/memory/) and dynamically loaded at runtime.

| Memory Tier | Stored Content | Update Trigger & Correction Policy | Usage |
| :---- | :---- | :---- | :---- |
| **user\_profile** | Developer's preferred language, coding style, frequently used commands, preferred output formats. | Updated when the user explicitly requests a style or provides repetitive feedback. (Overwrite with the latest evidence). | Merged when loading the initial System Prompt to generate personalized responses. |
| **project\_context** | Architecture decisions, directory structures, banned libraries, testing rules. | Recorded when a new requirement document is analyzed or the project structure changes. | Injected into the context of the Code Generation and Review SubAgents. |
| **domain\_knowledge** | Domain-specific knowledge such as business terms, business rules, API contracts, operational procedures. | **Cumulatively added** whenever the user explains new business rules or domain logic. | Loaded via RAG or Memory Search when the Coder implements related business logic. |

* **Implementation Guideline:** Do not delete knowledge simply because it is old (No simple TTL policy). In case of conflicts, update the memory based on the user's most recent feedback.

## ---

**4\. Core Requirement 2: Dynamic SubAgent Lifecycle Management**

SubAgents are not static, hardcoded objects. The Main Orchestrator dynamically generates them at runtime (based on CompiledGraph) by combining Role templates according to the Task's nature. They must follow a strict lifecycle.

### **4.1. SubAgent State Transitions**

Each SubAgent is assigned a unique agent\_id and metadata, transitioning through the following states:

| State | Description & Trigger Condition |
| :---- | :---- |
| created | Instantiated in memory with a specific role (Planner, Coder, Reviewer, etc.) after requirement analysis. |
| assigned | Goals, task scopes, and isolated contexts (only necessary information) are injected. |
| running | Actively executing tool calls (Skills) and reasoning. |
| **blocked** | Unable to proceed autonomously due to lack of information, waiting for external API responses, or insufficient permissions. |
| completed | Successfully finished the assigned Task and returns the result to the Main Agent. |
| failed | Task failed after exceeding the allowed number of retries. |
| cancelled | Forcibly terminated due to timeout or the Main Orchestrator's decision. |
| destroyed | Lifecycle fully terminated; temporary resources and memory are cleared after returning results. |

* **Dynamic Invocation Architecture:** Ensure architectural flexibility. For example, the Planner can divide tasks, instantiate multiple Coder agents for parallel or sequential processing, and subsequently generate a Reviewer agent for validation.

## ---

**5\. Core Requirement 3: Agentic Loop Resilience & Safety**

To prevent the Agentic Loop from breaking due to LLM hallucinations, infinite loops, or external environment errors, the following **Failure Detection and Recovery Matrix** must be implemented at the node/middleware level.

| Failure Type | Detection Signal (Watchdog) | Allowed Retries | Fallback Strategy | Safe Stop Condition |
| :---- | :---- | :---- | :---- | :---- |
| **Model Unresponsive/Delay** | API Timeout, streaming interrupted. | 1\~2 times | Switch to a pre-defined, faster, and more stable model (e.g., a smaller parameter model). | Exceeds retry limit. |
| **No-Progress Loop** | The last *N* actions/code edits are identical, or compilation errors persist. | Max 3 times (Strict Limit) | Change agent role (e.g., Coder \-\> Error Analyst) or reduce task scope. | If no progress occurs after strategy switch, immediately break the loop and stop. |
| **Invalid Tool Call** | Missing parameters, schema mismatch (JSON parsing error). | 1 time | Re-inject prompt instructing the agent to fix the tool call format, including the exact error message. | Same schema error occurs 2+ times. |
| **SubAgent Failure** | SubAgent state transitions to failed or prolonged blocked. | 1 time per role | Subdivide the task and reassign it to a new SubAgent. | Alternative path (SubAgent replacement) also fails. |
| **Dangerous/Unclear Task** | Attempted permission violation, critical file deletion requested, etc. | 0 (No retries) | **None** | Trigger **Safe Stop** immediately; await Human-in-the-loop confirmation. |

* **State Preservation (Resume Metadata):** If the loop halts due to an error or Safe Stop, explicitly record the last successful step, the error logs, and the exact reason for stopping in walk\_through.md or a persistent state dictionary to enable future resumption.

## ---

**6\. Development Constraints & Code Style**

* **Directory Structure (Separation of Concerns):**  
  * Code must be strictly separated by functionality to keep files concise and directories granular.  
  * Examples: src/agents/, src/tools/, src/states/, src/memory/, src/utils/  
* **Naming Convention:**  
  * Use snake\_case by default, strictly adhering to the standard conventions of the chosen programming language.  
* **Graph State Definition:**  
  * The Graph state structure must clearly and explicitly separate messages (conversation history), currentWorkspaceState (list of modified files and their statuses), and errorLogs (compilation/execution error logs). To prevent global context pollution, pass only the necessary state fragments to the SubAgents.