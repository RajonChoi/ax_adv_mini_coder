import os
import logging
logging.basicConfig(level=logging.DEBUG)

from dotenv import load_dotenv
load_dotenv()


from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="openrouter:google/gemma-4-31b-it:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
response = llm.invoke("hello")
print(response)



# try:
#     print("Testing init_chat_model with openrouter:openai/gpt-4o-mini...")
#     model = init_chat_model("openrouter:openai/gpt-5.4-mini", max_retries=3)
#     response = model.invoke("hello")
#     print("Response:", response.content)
# except Exception as e:
#     import traceback
#     traceback.print_exc()
