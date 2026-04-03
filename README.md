# 🤖 CODING AI AGENT (코딩 AI 에이전트)

LangGraph와 deepagents를 기반으로 한 자동 코드 생성, 리팩토링, 버그 수정 AI 에이전트입니다.

---

## 📋 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [핵심 기능](#핵심-기능)
3. [아키텍처](#아키텍처)
4. [설치 및 환경 설정](#설치-및-환경-설정)
5. [빠른 시작](#빠른-시작)
6. [사용 방법](#사용-방법)
7. [환경 변수](#환경-변수)
8. [Docker 실행](#docker-실행)
9. [기술 스택](#기술-스택)
10. [제약사항 및 설정](#제약사항-및-설정)
11. [FAQ 및 문제 해결](#faq-및-문제-해결)

---

## 프로젝트 개요

CODING AI AGENT는 OpenRouter의 오픈소스 모델(기본값: Qwen)을 활용하여, 다음과 같은 소프트웨어 개발 작업을 자동화하는 AI 에이전트입니다:

- **코드 생성**: 요구사항 문서를 읽고 자동으로 코드 작성
- **코드 리팩토링**: 기존 코드 최적화 및 구조 개선
- **버그 수정**: 에러 로그 기반 자동 버그 수정

전체 작업은 **Langfuse** 플랫폼에 의해 자동으로 모니터링되며, **FilesystemBackend**가 `/projects` 디렉토리를 안전하게 격리된 작업 공간으로 사용합니다.

---

## 핵심 기능

### 1. **3단계 워크플로우**
   - **Planner (계획자)**: 요구사항을 분석하여 파일별 실행 계획 생성
   - **Coder (코더)**: 계획에 따라 코드 작성/수정
   - **Reviewer (검토자)**: 구문 및 요구사항 준수 여부 확인

### 2. **안전한 파일 작업**
   - FilesystemBackend와 `virtual_mode=True`로 `/projects` 이하만 접근 가능
   - 시스템 파일 접근 방지

### 3. **무한 재귀 방지**
   - 최대 3회 재시도 제한으로 토큰 낭비 방지
   - `agent.with_retry(stop_after_attempt=3)`

### 4. **모니터링 및 추적**
   - Langfuse와의 자동 통합으로 모든 에이전트 실행 추적
   - `/walk_through.md`에 작업 기록 자동 저장

### 5. **오픈소스 모델 지원**
   - OpenRouter를 통해 무료 오픈소스 모델(Qwen, Mistral 등) 사용
   - 사유 모델 의존성 제거

---

## 아키텍처

### 핵심 시스템 흐름

```
📝 CLI 입력 (main.py --task "...")
    ↓
🔧 WorkspaceState 초기화 및 파일 스냅샷
    ↓
🤖 create_coding_ai_agent() 에이전트 생성
    ├─ OpenRouter 모델 초기화
    ├─ FilesystemBackend 설정 (/projects)
    ├─ Langfuse 모니터링 활성화
    └─ 3개 SubAgent 등록 (Planner/Coder/Reviewer)
    ↓
⚡ agent.invoke() 작업 실행
    ├─ Planner SubAgent: 작업 계획 생성
    ├─ Coder SubAgent: 코드 작성/수정
    └─ Reviewer SubAgent: 검토 및 확인
    ↓
📊 결과 저장 및 모니터링
    ├─ WorkspaceState 업데이트
    ├─ Langfuse 대시보드 전송
    └─ walk_through.md 자동 기록
    ↓
✅ 사용자에게 결과 반환
```

### 프로젝트 디렉토리 구조

```
coding_agent/
│
├── 📄 main.py                      # CLI 엔트리포인트 (커맨드라인 인터페이스)
├── 📄 README.md                    # 이 파일 (프로젝트 설명서)
├── 📄 walk_through.md              # 작업 기록 로그 (자동 생성/업데이트)
├── 📄 pyproject.toml               # Python 프로젝트 설정 및 의존성
├── 📄 .env                         # 환경 변수 (Git 제외, 로컬만 관리)
├── 📁 .venv/                       # Python 가상 환경
│
└── 📁 src/                         # 소스 코드
    └── 📁 agents/                  # 에이전트 패키지
        ├── 📄 __init__.py          # 패키지 초기화
        │
        ├── 📄 coding_agent.py      # 핵심 에이전트 로직
        │   ├── SYSTEM_PROMPT       # 에이전트 시스템 프롬프트
        │   ├── create_coding_ai_agent() → 에이전트 생성 함수
        │   ├── run_agent_task()    → 작업 실행 함수
        │   ├── _model_name()       → 모델명 조회
        │   ├── _ensure_openrouter_config() → API 검증
        │   ├── _setup_langfuse()   → 모니터링 설정
        │   ├── _backend_factory()  → 파일 시스템 초기화
        │   └── _plan_subagent_definitions() → SubAgent 정의
        │
        └── 📄 state_models.py      # 상태 관리 클래스
            └── WorkspaceState      # LangGraph 상태 정의
                ├── messages        # 대화 기록
                ├── current_workspace_state # 파일 상태
                ├── error_logs      # 에러 로그
                ├── add_message()
                ├── add_error()
                └── snapshot()      # 파일 스냅샷
```

---

## 설치 및 환경 설정

### 사전 요구사항

- **Python**: 3.13 이상
- **패키지 관리자**: uv
- **API 계정**: OpenRouter 계정 (무료 또는 유료)
- **모니터링** (선택): Langfuse 인스턴스 (Docker 또는 클라우드)

### 1단계: 저장소 클론

```bash
git clone <repository-url>
cd coding_agent
```

### 2단계: Python 가상 환경 생성

```bash
# Linux / macOS
uv init
source .venv/bin/activate

# Windows
uv init
.venv\Scripts\activate
```

### 3단계: 의존성 설치

```bash
# uv 사용
uv sync
```

**주요 의존성:**
- `deepagents>=0.4.12` - LangGraph 기반 에이전트 프레임워크
- `langfuse>=4.0.6` - 모니터링 및 추적 플랫폼
- `langchain-openrouter>=0.2.1` - OpenRouter 모델 통합

### 4단계: 환경 변수 설정

프로젝트 루트에 `.env` 파일 생성:

```bash
cat > .env << 'EOF'
# OpenRouter API 설정 (필수)
OPENROUTER_API_KEY=sk-or-v1-your_actual_key_here

# Langfuse 설정 (필수)
LANGFUSE_PUBLIC_KEY=pk-your_actual_public_key
LANGFUSE_SECRET_KEY=sk-your_actual_secret_key

# Langfuse 설정 (선택사항)
LANGFUSE_BASE_URL=http://localhost:3000

# 에이전트 설정 (선택사항)
OPENROUTER_MODEL=openrouter:qwen/qwen3.6-plus:free
CODING_AGENT_PROJECT_ROOT=/projects
EOF
```

**⚠️ 보안 주의사항:**
- `.env` 파일은 절대 Git에 커밋하지 마세요
- `.gitignore`에 `.env` 추가 확인

---

## 빠른 시작

### 기본 사용법

```bash
# 가상 환경 활성화
source .venv/bin/activate

# 간단한 코딩 작업 실행
python main.py --task "Python으로 간단한 TODO 관리 CLI를 작성해"

# 프로젝트 루트 명시
python main.py --task "FastAPI에서 /users POST 엔드포인트 추가" --project-root /my/project
```

### 예제 1: 새 모듈 생성

```bash
python main.py --task "utils.py 모듈을 만들어서 문자열 유틸리티 함수 3개 구현"
```

**에이전트 자동 실행 과정:**

1. **Planner**: `utils.py` 파일 생성 및 함수 목록 계획
2. **Coder**: 3개의 문자열 유틸리티 함수 작성
3. **Reviewer**: 코드 문법 및 요구사항 검사

### 예제 2: 버그 수정

```bash
python main.py --task "app.py의 라인 45에서 IndexError가 발생해. 예외 처리를 추가해"
```

### 예제 3: 코드 리팩토링

```bash
python main.py --task "main.py를 리팩토링해서 함수를 분리하고 가독성을 좋게 해"
```

---

## 사용 방법

### 1. 커맨드라인 인터페이스 (CLI)

#### 기본 명령어 형식

```bash
python main.py --task "작업 설명" [--project-root 경로]
```

#### 옵션 설명

| 옵션 | 설명 | 기본값 | 필수 여부 |
|------|------|--------|---------|
| `--task` | 코딩 작업을 설명하는 자연어 텍스트 | N/A | ✅ 필수 |
| `--project-root` | 에이전트가 접근할 프로젝트 루트 디렉토리 경로 | `/projects` | ❌ 선택 |

#### CLI 반환값

```
=== Agent Output ===
생성된 코드 및 에이전트의 작업 결과

=== Workspace State ===
수정된 파일 목록, 에러 로그, 상태 정보
```

### 2. Python API로 직접 사용

```python
from src.agents.coding_agent import run_agent_task
import os

# 환경 변수 설정
os.environ['OPENROUTER_API_KEY'] = 'sk-or-v1-...'
os.environ['LANGFUSE_PUBLIC_KEY'] = 'pk-...'
os.environ['LANGFUSE_SECRET_KEY'] = 'sk-...'

# 작업 실행
result = run_agent_task("Create a function to calculate factorial")

# 결과 확인
print(result['output'])        # 에이전트 결과
print(result['state'])         # 작업 공간 상태
print(result['state'].messages) # 대화 기록
print(result['state'].error_logs) # 에러 로그
```

### 3. 에이전트 인스턴스 직접 생성

```python
from src.agents.coding_agent import create_coding_ai_agent
import os

# 환경 변수 설정
os.environ['OPENROUTER_API_KEY'] = 'sk-or-v1-...'
os.environ['LANGFUSE_PUBLIC_KEY'] = 'pk-...'
os.environ['LANGFUSE_SECRET_KEY'] = 'sk-...'

# 에이전트 생성
agent = create_coding_ai_agent()

# 직접 호출
response = agent.invoke({"input": "작업 설명"})
print(response)
```

---

## 환경 변수 상세 설정

### 필수 환경 변수

#### `OPENROUTER_API_KEY` ⭐ 필수

- **설명**: OpenRouter API 키 (HTTP 요청 인증용)
- **획득 방법**:
  1. https://openrouter.ai 방문
  2. 계정 가입/로그인
  3. Dashboard → API Keys → Create Key
- **예시**: `sk-or-v1-abc123def456...`
- **주의사항**: 공개되면 안 되는 민감 정보 (Github에 절대 커밋 금지)

#### `LANGFUSE_PUBLIC_KEY` ⭐ 필수

- **설명**: Langfuse 공개 인증 키
- **획득 방법**: Langfuse 프로젝트 → Settings → API Keys
- **예시**: `pk-lf-...`

#### `LANGFUSE_SECRET_KEY` ⭐ 필수

- **설명**: Langfuse 비밀 인증 키
- **획득 방법**: Langfuse 프로젝트 → Settings → API Keys
- **예시**: `sk-lf-...`

### 선택사항 환경 변수

#### `LANGFUSE_BASE_URL`

- **설명**: Langfuse 서버 주소
- **기본값**: `http://localhost:3000`
- **옵션**:
  - 로컬 Docker: `http://localhost:3000`
  - 클라우드: `https://cloud.langfuse.com`
  - Docker 컨테이너 간: `http://langfuse:3000` (서비스명)

#### `OPENROUTER_MODEL`

- **설명**: 사용할 LLM 모델 (OpenRouter)
- **기본값**: `openrouter:qwen/qwen3.6-plus:free`
- **추천 모델**:
  - 빠름: `openrouter:mistralai/mistral-7b:free` (~0.5초)
  - 균형: `openrouter:qwen/qwen3.6-plus:free` (~1-2초, 기본)
  - 고품질: `openrouter:meta-llama/llama-2-70b-chat` (~3초)
  - 프리미엄: `openrouter:openai/gpt-4o-mini` (유료, 최고 품질)

#### `CODING_AGENT_PROJECT_ROOT`

- **설명**: 에이전트가 접근할 프로젝트 루트 경로
- **기본값**: `/projects`
- **보안**: 이 경로 이하의 파일만 접근 가능
- **예시**:
  - 로컬: `/home/user/my-project`
  - Docker: `/app` 또는 `/projects`

### 환경 변수 설정 방법 3가지

**방법 1: .env 파일 사용 (권장)**

```bash
cat > .env << EOF
OPENROUTER_API_KEY=sk-or-v1-...
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_BASE_URL=http://localhost:3000
EOF

python main.py --task "..."
```

**방법 2: Shell 환경 변수 설정**

```bash
export OPENROUTER_API_KEY=sk-or-v1-...
export LANGFUSE_PUBLIC_KEY=pk-...
export LANGFUSE_SECRET_KEY=sk-...
python main.py --task "..."
```

**방법 3: 인라인 환경 변수**

```bash
OPENROUTER_API_KEY=sk-or-v1-... python main.py --task "..."
```

---

## Docker 실행

### 간단한 Docker 실행

```bash
# 이미지 빌드
docker build -t coding-agent:latest .

# 컨테이너 실행
docker run --rm \
  -v /my/source:/projects \
  -e OPENROUTER_API_KEY=sk-or-v1-... \
  -e LANGFUSE_PUBLIC_KEY=pk-... \
  -e LANGFUSE_SECRET_KEY=sk-... \
  -e LANGFUSE_BASE_URL=http://host.docker.internal:3000 \
  coding-agent:latest \
  python main.py --task "작업 설명"
```

### Docker Compose로 전체 스택 실행 (권장)

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  # Langfuse 모니터링 플랫폼
  langfuse:
    image: langfuse/langfuse:latest
    container_name: langfuse
    ports:
      - "3000:3000"
    environment:
      DATABASE_URL: sqlite://./langfuse.db
      NEXTAUTH_URL: http://localhost:3000
    volumes:
      - langfuse_data:/app/data

  # CODING AI AGENT
  coding-agent:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: coding-agent
    volumes:
      - /my/source:/projects          # 프로젝트 경로
      - ./walk_through.md:/app/walk_through.md
    environment:
      OPENROUTER_API_KEY: ${OPENROUTER_API_KEY}
      LANGFUSE_PUBLIC_KEY: ${LANGFUSE_PUBLIC_KEY}
      LANGFUSE_SECRET_KEY: ${LANGFUSE_SECRET_KEY}
      LANGFUSE_BASE_URL: http://langfuse:3000  # 내부 통신
      CODING_AGENT_PROJECT_ROOT: /projects
    depends_on:
      - langfuse
    stdin_open: true
    tty: true

volumes:
  langfuse_data:
```

**실행 명령어:**

```bash
# .env 파일 생성
cat > .env << EOF
OPENROUTER_API_KEY=sk-or-v1-...
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
EOF

# Docker Compose 시작
docker-compose up -d

# 에이전트 작업 실행
docker-compose exec coding-agent python main.py --task "작업 설명"

# 로그 확인
docker-compose logs -f coding-agent

# Langfuse 대시보드 접속
# http://localhost:3000

# 정리
docker-compose down
```

---

## 기술 스택

### 코어 라이브러리

| 라이브러리 | 버전 | 목적 |
|-----------|------|------|
| **deepagents** | ≥0.4.12 | LangGraph 기반 멀티-에이전트 프레임워크 |
| **langfuse** | ≥4.0.6 | LLM 모니터링 및 추적 플랫폼 |
| **langchain-core** | ≥1.2.23 | LLM 체인 기본 인터페이스 |
| **langchain-openrouter** | ≥0.2.1 | OpenRouter API 통합 |
| **openrouter** | ≥0.7.11 | OpenRouter HTTP 클라이언트 |

### 아키텍처 기반 기술

- **LangGraph**: StateGraph 기반 DAG 구성
- **FilesystemBackend**: 안전한 가상 파일 시스템 접근 (virtual_mode=True)
- **OpenRouter**: 오픈소스/사유 모델 통합 플랫폼
- **Langfuse**: 엔터프라이즈급 LLM 관찰성(Observability)

---

## 제약사항 및 설정

### 설계 제약

#### 1. MCP 미사용 ❌
- Model Context Protocol 사용 금지
- 이유: 단순 아키텍처, 직접 제어 가능
- 구현: 네이티브 Python 함수 기반

#### 2. 파일 접근 격리 🔒
- `/projects` 이하 디렉토리만 접근 가능
- `virtual_mode=True`로 경로 격리
- 보안 이점:
  - 시스템 파일 접근 불가
  - 상위 디렉토리(`..`) 접근 차단
  - 절대 경로 접근 제한

#### 3. 재시도 제한 🔄
- 최대 3회 재시도 (`stop_after_attempt=3`)
- 목적: 무한 루프 방지, 토큰 낭비 방지, 비용 절감

#### 4. 오픈소스 모델만 사용 🎯
- OpenRouter를 통한 오픈소스 모델
- 기본값: Qwen (빠르고 효율적)
- 이유: 비용 효율성, 투명성

---

## FAQ 및 문제 해결

### Q1: Langfuse 없이 사용 가능한가요?

**A**: 네, Langfuse 환경 변수를 설정하지 않으면 모니터링만 비활성화됩니다.

```bash
# Langfuse 없이 실행
python main.py --task "작업 설명"
# (LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY 미설정)
```

### Q2: 다른 모델을 사용하려면?

**A**: `.env`에서 `OPENROUTER_MODEL` 변수를 변경하세요.

```bash
# Mistral 7B 사용
OPENROUTER_MODEL=openrouter:mistralai/mistral-7b:free

# Llama 2 70B 사용
OPENROUTER_MODEL=openrouter:meta-llama/llama-2-70b-chat

# GPT-4 Omni (유료)
OPENROUTER_MODEL=openrouter:openai/gpt-4o
```

### Q3: 특정 디렉토리만 접근하도록 제한할 수 있나요?

**A**: `CODING_AGENT_PROJECT_ROOT` 환경 변수로 설정 가능합니다.

```bash
export CODING_AGENT_PROJECT_ROOT=/home/user/my-project
python main.py --task "..."
```

### Q4: 작업 기록은 어떻게 확인하나요?

**A**: `walk_through.md` 파일에 자동 기록되며, Langfuse 대시보드에서도 확인 가능합니다.

```bash
# walk_through.md 확인
cat walk_through.md

# Langfuse 대시보드
# http://localhost:3000
```

### Q5: 에이전트가 코드를 작성하지 않아요.

**A**: 요구사항이 명확하지 않을 수 있습니다.

```bash
# ❌ 나쁜 예
python main.py --task "코드 작성"

# ✓ 좋은 예
python main.py --task "Python에서 문자열을 정렬된 단어 리스트로 변환하는 함수 작성해. 예: 'hello world' → ['hello', 'world']"
```

### 에러: `OPENROUTER_API_KEY is required`

**원인**: 환경 변수 미설정

**해결책**:
```bash
export OPENROUTER_API_KEY=sk-or-v1-your_key
python main.py --task "..."
```

### 에러: `langchain-openrouter is required`

**원인**: 패키지 미설치

**해결책**:
```bash
pip install langchain-openrouter
```

### 에러: Langfuse 연결 실패

**원인**: Langfuse 서버 미구동

**해결책**:
```bash
# Docker로 Langfuse 시작
docker run -p 3000:3000 langfuse/langfuse:latest

# 또는 클라우드 사용
LANGFUSE_BASE_URL=https://cloud.langfuse.com
```

---

## 성능 최적화 팁

### 1. 모델 선택
- **초고속**: `mistral-7b` (~0.5초)
- **균형** (추천): `qwen3.6-plus` (~1-2초)
- **고품질**: `llama-70b` (~3초)
- **최고 품질**: `gpt-4-omni` (~5초, 유료)

### 2. 요구사항 명확히
```bash
✓ 좋은 예:
python main.py --task "
Flask API에 JWT 인증 추가.
파일: app.py, auth.py
기능: 로그인 엔드포인트, 토큰 검증 미들웨어
기술: JWT, httponly cookies
"
```

### 3. 작은 작업으로 분해
```bash
# Step 1: 모듈 구조
python main.py --task "project_module 구조 생성"

# Step 2: 기본 기능
python main.py --task "CRUD 함수 구현"

# Step 3: 테스트
python main.py --task "단위 테스트 작성"
```

---

## 참고 자료

- [DeepAgents 공식 문서](https://docs.deepseek.com)
- [LangGraph 가이드](https://python.langchain.com/docs/langgraph)
- [OpenRouter 모델 목록](https://openrouter.ai/models)
- [Langfuse 소개](https://langfuse.com)

---

## 라이선스 및 연락

- **라이선스**: MIT License
- **버그 리포트**: GitHub Issues
- **기능 제안**: GitHub Discussions

---

**최종 업데이트**: 2026년 4월 3일 | **버전**: 0.1.0
