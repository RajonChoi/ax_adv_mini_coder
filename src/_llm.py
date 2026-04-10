import os
from pyexpat import model
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableWithFallbacks
from dotenv import load_dotenv
load_dotenv()

from langfuse.langchain import CallbackHandler

MODEL_ALIAS={
    "big_qwen": "qwen/qwen3.5-122b-a10b",
    "small_qwen": "qwen/qwen3.5-9b",
    "glm": "z-ai/glm-5.1",
}

def _resolve_litellm_api_key() -> str:
    # Priority: explicit LiteLLM key -> master key -> fallback OpenRouter key.
    return (
        os.getenv("LITELLM_API_KEY")
        or os.getenv("LITELLM_MASTER_KEY")
        or os.getenv("OPENROUTER_API_KEY")
        or ""
    )

def get_llm(model_name: str) -> ChatOpenAI:
    model = "openrouter/" + MODEL_ALIAS.get(model_name, model_name)
    litellm_api_key = _resolve_litellm_api_key()
    if not litellm_api_key:
        raise RuntimeError(
            "LiteLLM API key is missing. Set LITELLM_API_KEY or LITELLM_MASTER_KEY."
        )

    try:
        llm = ChatOpenAI(
            model=model,
            base_url=os.getenv("LITELLM_BASE_URL", "http://litellm:4000/v1"),
            api_key=litellm_api_key,
            max_retries=0,
        )

        llm.callbacks = [CallbackHandler()]

        return llm

    except Exception as e:
        raise RuntimeError(f"Failed to initialize LLM '{model}'. with error {str(e)}")


# 2. 장애 발생 시 연결할 OpenAI 모델
