import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
load_dotenv()

from langfuse.langchain import CallbackHandler


def get_llm(model_name: str) -> ChatOpenAI:
    langfuse_handler = CallbackHandler()
    if model_name == "big_qwen":
        llm_with_big_qwen = ChatOpenAI(
            model="qwen/qwen3.5-122b-a10b",
            base_url=os.getenv("OPENROUTER_BASE_URL"),
            api_key=os.getenv("OPENROUTER_API_KEY"),
            callbacks=[langfuse_handler],
        )
        llm = llm_with_big_qwen
    elif model_name == "small_qwen":
        llm_with_small_qwen = ChatOpenAI(
            model="qwen/qwen3.5-9b",
            base_url=os.getenv("OPENROUTER_BASE_URL"),
            api_key=os.getenv("OPENROUTER_API_KEY"),
            callbacks=[langfuse_handler],
        )
        llm = llm_with_small_qwen

    elif model_name == "glm":
        llm_glm = ChatOpenAI(
            model="z-ai/glm-5.1",
            base_url=os.getenv("OPENROUTER_BASE_URL"),
            api_key=os.getenv("OPENROUTER_API_KEY"),
            callbacks=[langfuse_handler],
        )
        llm = llm_glm
    else:
        raise ValueError(f"Unknown model name: {model_name}")

    return llm



