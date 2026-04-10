# Coding Agent

DeepAgents 기반 코딩 에이전트를 Flask 웹 UI로 감싼 프로젝트입니다.<br><br>
사용자가 자연어로 작업을 요청하면 에이전트가<br>
`projects/` 워크스페이스를 기준으로 계획/구현/검토를 수행하고,
<br>
진행 로그를 실시간(SSE)으로 스트리밍합니다.

## 1) 주요 기능

Chat을 통해 코드를 생성합니다.

- DeepAgents 오케스트레이션
- SubAgent 구성
- Planner: 작업 계획 수립
- Coder: 코드 생성/수정
- Reviewer: 결과 검토
- 동적 SubAgent 호출 도구 (`call_dynamic_subagent`)
- 사용자 특성 장기 메모리 저장 (PostgreSQL JSONB)
- Flask 기반 웹 UI + 실시간 실행 로그 스트리밍
- LiteLLM Proxy를 통한 모델 라우팅/폴백
- Langfuse 연동(트레이싱)

## 2) 아키텍처

```text
Browser UI (Flask Template)
  -> POST /api/execute (SSE)
  -> stream_agent_task()
  -> create_deep_agent()
     - model: LiteLLM endpoint
     - backend: FilesystemBackend(root_dir=CODING_AGENT_PROJECT_ROOT, virtual_mode=True)
     - subagents: planner/coder/reviewer/simple_coder
     - tools: memory save/delete + dynamic subagent
  -> 결과 스트림(start/node/end)
```

## 3) 디렉토리 구조

```text
.
├── web_app.py                  # Flask 엔트리포인트
├── docker-compose.yml          # 통합 실행 스택(DB/Langfuse/LiteLLM/App)
├── lite_llm_config.yaml        # LiteLLM 모델/폴백 설정
├── src/
│   ├── coding_agent.py         # 메인 에이전트 조립 및 실행/스트리밍
│   ├── subagents.py            # SubAgent 정의
│   ├── _llm.py                 # LLM 초기화(LiteLLM base_url + key)
│   ├── config.py               # 환경 검증 + FilesystemBackend 팩토리
│   ├── memory_pg.py            # 사용자 프로필 저장소(PostgreSQL)
│   └── state_models.py         # WorkspaceState(messages/snapshot/error_logs)
├── templates/index.html        # 웹 UI
└── projects/                   # 에이전트 산출물 저장 디렉토리
```

## 4) 시작

### 사전 준비

- Docker / Docker Compose
- OpenRouter API Key
- install python 3.13 && uv

```bash
uv sync
cp .env.example .env
```

- `.env` 작성
  > 프로젝트 루트의 `.env` 파일에 아래 값을 채워주세요.

```bash
OPENROUTER_BASE_URL="https://openrouter.ai/api/v1"
OPENROUTER_API_KEY=...

OPENAI_API_KEY=...                 # fallback-gpt 사용 시 필요

LITELLM_MASTER_KEY=...

LANGFUSE_BASE_URL="http://localhost:3000"
```

### 실행

```bash
docker compose up -f docker-compose.yml -d --build
```

### 접속

- Langfuse: `http://localhost:3000`
- LiteLLM Proxy: `http://localhost:4000`
- App UI: `http://localhost:5000`
  > AI Chat Service


### `.env` 업데이트
아래 항목 추가 입력
- Langfuse 접속하여 계정, oraganization/project 및 API Key 생성
- LiteLLM > ui에 접속하여 API Key 생성

```bash
LITELLM_API_KEY=...

LANGFUSE_PUBLIC_KEY=...
LANGFUSE_SECRET_KEY=...

```

## 5) API 사용법

### `POST /api/execute`

- Content-Type: `application/json`
- Body:

```json
{
  "task": "요청 내용",
  "history": [
    {"role": "user", "content": "이전 대화"},
    {"role": "assistant", "content": "이전 응답"}
  ]
}
```

응답은 `text/event-stream`이며, 주요 이벤트는 아래 3종류입니다.

- `start`: 실행 시작
- `node`: 중간 노드 로그
- `end`: 최종 응답(`response_type`, `final_response`, `history_response`)

예시:

```bash
curl -N -X POST http://localhost:5000/api/execute \
  -H 'Content-Type: application/json' \
  -d '{"task":"간단한 파이썬 함수 작성해줘","history":[]}'
```

## 7) 환경 변수 정리

| 변수명 | 필수 | 설명 |
|---|---|---|
| `OPENROUTER_API_KEY` | 예 | OpenRouter 호출 키 (`ensure_openrouter_config`에서 확인) |
| `LITELLM_API_KEY` | 조건부 | 앱에서 LiteLLM 호출 시 사용. 없으면 `LITELLM_MASTER_KEY` 또는 `OPENROUTER_API_KEY`로 대체 |
| `LITELLM_MASTER_KEY` | 조건부 | LiteLLM 프록시 master key |
| `LITELLM_BASE_URL` | 아니오 | 기본값: `http://litellm:4000/v1` |
| `LANGFUSE_PUBLIC_KEY` | 권장 | Langfuse 트레이싱 |
| `LANGFUSE_SECRET_KEY` | 권장 | Langfuse 트레이싱 |
| `LANGFUSE_BASE_URL` | 권장 | Langfuse 서버 URL (예: `http://langfuse:3000`) |
| `CODING_AGENT_PROJECT_ROOT` | 아니오 | 에이전트 작업 루트. 기본값: `projects` |
| `DATABASE_URL` | 권장 | 사용자 메모리 저장 PostgreSQL URL |

## 8) 데이터 저장 위치

- 코드 산출물/작업 결과: `projects/`
- 사용자 특성 메모리: PostgreSQL `user_profiles` 테이블(JSONB)
- 트레이싱: Langfuse


## 9) 개발 참고

- Python 요구 버전: `>=3.13`
- 의존성 관리: `uv`
- 웹 서버: `Flask`
- 모델 호출: `LiteLLM Proxy` + `langchain-openai`
