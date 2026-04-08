import os
import logging
logging.basicConfig(level=logging.DEBUG)

os.environ["OPENROUTER_API_KEY"] = "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"

from langchain.chat_models import init_chat_model

try:
    print("Testing init_chat_model with openrouter:openai/gpt-4o-mini...")
    model = init_chat_model("openrouter:openai/gpt-4o-mini", timeout=120, max_retries=3)
    response = model.invoke("hello", timeout=120)
    print("Response:", response.content)
except Exception as e:
    import traceback
    traceback.print_exc()
