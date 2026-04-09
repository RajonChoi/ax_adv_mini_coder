from flask import Flask, render_template, request, Response
import os
import sys
import html
import json
from dotenv import load_dotenv

load_dotenv()

from src.coding_agent import run_agent_task, stream_agent_task

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max


def generate_sse_stream(task, history):
    try:
        for event in stream_agent_task(task, history):
            yield f"data: {json.dumps(event)}\n\n"
    except Exception as exc:
        err = {"type": "node", "node_name": "error", "content": str(exc)}
        yield f"data: {json.dumps(err)}\n\n"
        yield f"data: {json.dumps({'type': 'end'})}\n\n"


## OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/execute", methods=["POST"])
def execute_task():
    task = ""
    history = []

    if request.is_json:
        data = request.get_json()
        task = data.get("task", "").strip()
        history = data.get("history", [])
    else:
        task = request.form.get("task", "").strip()

    if not task:
        return "Task cannot be empty", 400

    project_root = os.getenv("CODING_AGENT_PROJECT_ROOT", "projects")
    os.environ.setdefault("CODING_AGENT_PROJECT_ROOT", project_root)

    return Response(generate_sse_stream(task, history), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
