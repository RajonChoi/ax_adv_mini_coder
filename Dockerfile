FROM python:3.13-slim

# 필요한 패키지 및 uv 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install uv

# 작업 디렉토리 설정
WORKDIR /app

# 에이전트가 격리된 공간으로 사용할 /projects 폴더 생성
RUN mkdir -p /projects

# 의존성 정의 파일 복사 및 설치
COPY pyproject.toml uv.lock ./
ENV UV_PROJECT_ENVIRONMENT=/usr/local
RUN uv sync --frozen

# 앱 소스코드 복사
COPY . .

# Flask 서버 5000 포트
EXPOSE 5000

# 애플리케이션 실행
CMD ["uv", "run", "python", "web_app.py"]
