#!/usr/bin/env bash
set -euo pipefail #

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="${ROOT_DIR}/.env"

info() {
  printf "\n[INFO] %s\n" "$1"
}

warn() {
  printf "\n[WARN] %s\n" "$1"
}

error() {
  printf "\n[ERROR] %s\n" "$1" >&2
}

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    error "필수 명령어가 없습니다: $1"
    exit 1
  fi
}

detect_compose() {
  if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=("docker" "compose")
    return
  fi
  if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=("docker-compose")
    return
  fi
  error "docker compose 또는 docker-compose를 찾지 못했습니다."
  exit 1
}

strip_quotes() {
  local value="$1"
  value="${value%\"}"
  value="${value#\"}"
  value="${value%\'}"
  value="${value#\'}"
  printf "%s" "$value"
}

get_env() {
  local key="$1"
  if [[ ! -f "$ENV_FILE" ]]; then
    printf ""
    return
  fi
  local line
  line="$(grep -E "^${key}=" "$ENV_FILE" | tail -n 1 || true)"
  if [[ -z "$line" ]]; then
    printf ""
    return
  fi
  strip_quotes "${line#*=}"
}

set_env() {
  local key="$1"
  local value="$2"
  local tmp_file
  tmp_file="$(mktemp)"

  awk -v k="$key" -v v="$value" '
    BEGIN { updated = 0 }
    $0 ~ ("^" k "=") {
      print k "=\"" v "\""
      updated = 1
      next
    }
    { print }
    END {
      if (updated == 0) {
        print k "=\"" v "\""
      }
    }
  ' "$ENV_FILE" >"$tmp_file"

  mv "$tmp_file" "$ENV_FILE"
}

is_placeholder() {
  local value="${1:-}"
  value="$(echo "$value" | tr -d '[:space:]')"
  if [[ -z "$value" ]]; then
    return 0
  fi
  if [[ "$value" == *"..."* ]]; then
    return 0
  fi
  if [[ "$value" =~ ^(changeme|change_me|your_key|your-api-key|sk-\.\.\.)$ ]]; then
    return 0
  fi
  return 1
}

generate_master_key() {
  if command -v openssl >/dev/null 2>&1; then
    printf "litellm-master-%s" "$(openssl rand -hex 12)"
  else
    printf "litellm-master-%s" "$(date +%s)"
  fi
}

wait_for_update_and_validate() {
  local title="$1"
  shift
  local required_keys=("$@")

  info "$title"
  printf "필수 값: %s\n" "${required_keys[*]}"

  while true; do
    read -r -p "업데이트를 완료했나요? [y/n]: " yn
    case "$yn" in
      y|Y)
        local missing=()
        local k
        for k in "${required_keys[@]}"; do
          local v
          v="$(get_env "$k")"
          if is_placeholder "$v"; then
            missing+=("$k")
          fi
        done
        if [[ ${#missing[@]} -eq 0 ]]; then
          info "입력 확인 완료. 다음 단계로 이동합니다."
          break
        fi
        warn "아직 값이 비어 있거나 placeholder 인 항목: ${missing[*]}"
        ;;
      n|N)
        printf ".env를 업데이트한 뒤 다시 y를 입력해 주세요.\n"
        ;;
      *)
        printf "y 또는 n만 입력해 주세요.\n"
        ;;
    esac
  done
}

wait_for_litellm_key_update() {
  info "LiteLLM 키 업데이트 확인"
  printf "필수 값: LITELLM_API_KEY 또는 LITELLM_VIRTUAL_KEY\n"

  while true; do
    read -r -p "업데이트를 완료했나요? [y/n]: " yn
    case "$yn" in
      y|Y)
        local api_key
        local virtual_key
        api_key="$(get_env "LITELLM_API_KEY")"
        virtual_key="$(get_env "LITELLM_VIRTUAL_KEY")"
        if ! is_placeholder "$api_key" || ! is_placeholder "$virtual_key"; then
          info "입력 확인 완료. 다음 단계로 이동합니다."
          break
        fi
        warn "LITELLM_API_KEY 또는 LITELLM_VIRTUAL_KEY 중 하나를 입력해 주세요."
        ;;
      n|N)
        printf ".env를 업데이트한 뒤 다시 y를 입력해 주세요.\n"
        ;;
      *)
        printf "y 또는 n만 입력해 주세요.\n"
        ;;
    esac
  done
}

prepare_env_file() {
  if [[ -f "$ENV_FILE" ]]; then
    info ".env 파일을 사용합니다: $ENV_FILE"
    return
  fi

  if [[ -f "${ROOT_DIR}/.env.example" ]]; then
    cp "${ROOT_DIR}/.env.example" "$ENV_FILE"
    info ".env.example을 복사해 .env를 생성했습니다."
  else
    touch "$ENV_FILE"
    warn ".env.example이 없어 빈 .env 파일을 생성했습니다."
  fi
}

sync_litellm_api_key() {
  local api_key
  local virtual_key
  api_key="$(get_env "LITELLM_API_KEY")"
  virtual_key="$(get_env "LITELLM_VIRTUAL_KEY")"

  if is_placeholder "$api_key" && ! is_placeholder "$virtual_key"; then
    set_env "LITELLM_API_KEY" "$virtual_key"
    info "LITELLM_VIRTUAL_KEY 값을 LITELLM_API_KEY로 동기화했습니다."
  fi
}

main() {
  require_cmd docker
  detect_compose
  prepare_env_file

  info "Step 1/5: OpenRouter 키 확인"
  cat <<'EOF'
[안내]
1) https://openrouter.ai/ 에 접속해 API Key를 생성합니다.
2) 프로젝트 루트의 .env 파일에 OPENROUTER_API_KEY를 입력합니다.
EOF
  wait_for_update_and_validate "OpenRouter 키 업데이트 확인" "OPENROUTER_API_KEY"

  local master_key
  master_key="$(get_env "LITELLM_MASTER_KEY")"
  if is_placeholder "$master_key"; then
    master_key="$(generate_master_key)"
    set_env "LITELLM_MASTER_KEY" "$master_key"
    info "LITELLM_MASTER_KEY가 없어 자동 생성했습니다."
    printf "생성된 값: %s\n" "$master_key"
  fi

  info "Step 2/5: 키 발급용 서비스 기동"
  "${COMPOSE_CMD[@]}" up -d db clickhouse redis minio langfuse langfuse-worker litellm

  info "Step 3/5: Langfuse 키 생성"
  cat <<'EOF'
[안내]
1) http://localhost:3000 에 접속합니다.
2) 로그인 후 Organization/Project를 생성합니다.
3) Project Settings에서 API Key를 생성합니다.
4) .env에 LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY를 입력합니다.
EOF
  wait_for_update_and_validate "Langfuse 키 업데이트 확인" "LANGFUSE_PUBLIC_KEY" "LANGFUSE_SECRET_KEY"

  info "Step 4/5: LiteLLM 키 생성"
  cat <<EOF
[안내]
1) http://localhost:4000/ui 에 접속합니다.
2) Master Key(${master_key})로 로그인합니다.
3) Virtual Key를 생성합니다.
4) .env에 LITELLM_API_KEY를 입력합니다.
   (LITELLM_VIRTUAL_KEY에 입력해도 자동 동기화됩니다.)
EOF
  wait_for_litellm_key_update
  sync_litellm_api_key

  info "Step 5/5: 전체 스택 실행"
  "${COMPOSE_CMD[@]}" up -d --build

  info "기동 상태"
  "${COMPOSE_CMD[@]}" ps

  cat <<'EOF'

[완료]
- App UI:       http://localhost:5000
- Langfuse:     http://localhost:3000
- LiteLLM UI:   http://localhost:4000/ui

문제가 있으면 아래 로그를 확인하세요:
  docker compose logs -f jrue-coder
EOF
}

main "$@"
