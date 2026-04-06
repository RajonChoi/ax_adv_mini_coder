from flask import Flask, render_template, request, jsonify
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from src.agents.coding_agent import run_agent_task

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/execute", methods=["POST"])
def execute_task():
    try:
        data = request.get_json()
        task = data.get("task", "").strip()

        if not task:
            return jsonify({"error": "Task cannot be empty"}), 400

        project_root = os.getenv("CODING_AGENT_PROJECT_ROOT", "projects")
        os.environ.setdefault("CODING_AGENT_PROJECT_ROOT", project_root)

        result = run_agent_task(task)

        return jsonify(
            {
                "success": True,
                "output": str(result.get("output", "")),
                "project_name": result["state"].project_name,
            }
        )
    except Exception as exc:
        return jsonify({"success": False, "error": str(exc)}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
