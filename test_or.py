import os
import logging
from deepagents import create_deep_agent
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv
load_dotenv()
# from src.config import get_langfuse_handler
# callback = get_langfuse_handler()

from langfuse import get_client
from langfuse.langchain import CallbackHandler

langfuse = get_client()
langfuse_handler = CallbackHandler()

logging.basicConfig(level=logging.DEBUG)

llm = ChatOpenAI(
    model="google/gemma-4-31b-it:free",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)
response = llm.invoke("hello", config={"callbacks": [langfuse_handler]})
print(response.content)
langfuse.flush()

agent = create_deep_agent(
    model=llm,
    system_prompt="You are a genius assistant about stock market.",
    tools=[]
)
response = agent.invoke({"input": "What is the stock price of Apple?"}, config={"callbacks": [langfuse_handler]})
print(response)
langfuse.flush()

