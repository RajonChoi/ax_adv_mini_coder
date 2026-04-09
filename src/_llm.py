import os
from pyexpat import model
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

from langfuse.langchain import CallbackHandler

MODEL_ALIAS={
    "big_qwen": "qwen/qwen3.5-122b-a10b",
    "small_qwen": "qwen/qwen3.5-9b",
    "glm": "z-ai/glm-5.1",
}

def get_llm(model_name: str) -> ChatOpenAI:
    model = MODEL_ALIAS.get(model_name, model_name)

    try:
        llm = ChatOpenAI(
            model=model,
            base_url=os.getenv("OPENROUTER_BASE_URL"),
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )

        llm.callbacks = [CallbackHandler()]
        return llm

    except Exception as e:
        raise RuntimeError(f"Failed to initialize LLM '{model}'. with error {str(e)}")


