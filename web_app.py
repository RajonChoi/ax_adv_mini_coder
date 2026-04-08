from flask import Flask, render_template, request, Response
import os
import sys
import html
from dotenv import load_dotenv

load_dotenv()

from src.agents.coding_agent import run_agent_task, stream_agent_task

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max


def generate_html_stream(task):
    yield """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>Coding AI Agent - 실행 결과</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; justify-content: center; align-items: flex-start; padding: 20px; margin: 0; }
        .container { background: white; border-radius: 12px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); padding: 40px; width: 100%; max-width: 800px; margin-top: 20px; }
        h1 { color: #333; margin-bottom: 20px; font-size: 24px; border-bottom: 2px solid #f0f0f0; padding-bottom: 10px; }
        .result-header { display: flex; justify-content: space-between; margin-bottom: 20px; }
        .project-name { background: #f0f0f0; color: #666; padding: 4px 12px; border-radius: 20px; font-size: 14px; font-weight: 500; }
        .node-box { background: #f8f8f8; border-left: 4px solid #667eea; padding: 15px; border-radius: 8px; margin-bottom: 15px; font-size: 14px; color: #333; }
        .node-title { font-weight: bold; margin-bottom: 10px; color: #667eea; }
        .whitespace-pre { white-space: pre-wrap; word-break: break-word; font-family: monospace; background: #fff; padding: 10px; border-radius: 4px; border: 1px solid #eee; }
        .end-msg { color: #28a745; font-weight: bold; text-align: center; padding: 10px; }
        .btn-home { display: inline-block; padding: 10px 20px; background: #667eea; color: white; text-decoration: none; border-radius: 8px; font-weight: bold; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 작업 실행 중...</h1>
"""
    try:
        for event in stream_agent_task(task):
            if event["type"] == "start":
                yield f'<div class="result-header"><span class="project-name">프로젝트 ID: {html.escape(event["project_name"])}</span></div>\n'
            elif event["type"] == "node":
                node_name = html.escape(event["node_name"])
                content = html.escape(str(event.get("content", "")))
                yield f'<div class="node-box"><div class="node-title">[{node_name}] 단계 완료</div><div class="whitespace-pre">{content}</div></div>\n'
            elif event["type"] == "end":
                yield '<div class="end-msg">✅ 모든 작업이 완료되었습니다.</div>\n'
    except Exception as exc:
        err = html.escape(str(exc))
        yield f'<div class="node-box" style="border-left-color: #dc3545;"><div class="node-title" style="color: #dc3545;">[오류 발생]</div><div class="whitespace-pre">{err}</div></div>\n'

    yield """
        <div style="text-align: center;">
            <a href="/" class="btn-home">돌아가기 / 새 작업</a>
        </div>
    </div>
</body>
</html>
"""

## OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/execute", methods=["POST"])
def execute_task():
    # form 데이터를 먼저 확인하고, 없으면 json을 확인 (호환성 유지)
    task = request.form.get("task", "").strip()
    if not task and request.is_json:
        task = request.get_json().get("task", "").strip()

    if not task:
        return "Task cannot be empty", 400

    project_root = os.getenv("CODING_AGENT_PROJECT_ROOT", "projects")
    os.environ.setdefault("CODING_AGENT_PROJECT_ROOT", project_root)

    return Response(generate_html_stream(task), mimetype="text/html")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
