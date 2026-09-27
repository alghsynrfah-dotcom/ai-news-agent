import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

from backend.tools.news_tool import get_news
from backend.tools.article_tool import fetch_article

load_dotenv()


# Checkpointer يحفظ حالة الـ Agent أثناء تشغيل التطبيق.
checkpointer = InMemorySaver()


def create_news_agent():
    api_url = os.getenv("VLLM_API_URL")
    api_key = os.getenv("VLLM_API_KEY")
    model_name = os.getenv("MODEL_NAME")

    if not api_url:
        raise ValueError("VLLM_API_URL is missing from .env")

    if not api_key:
        raise ValueError("VLLM_API_KEY is missing from .env")

    if not model_name:
        raise ValueError("MODEL_NAME is missing from .env")

    model = ChatOpenAI(
        model=model_name,
        temperature=0,
        api_key=api_key,
        base_url=api_url,
    )

    system_prompt = """
You are a news research assistant.

Your job is to answer user requests accurately.

Rules:
- Use get_news when the user asks for current or recent news.
- Do not use get_news for general questions that do not require current news.
- Do not invent news or sources.
- If a tool fails, explain the error clearly.
- Keep the final answer concise.
"""

    agent = create_agent(
        model=model,
        tools=[get_news, fetch_article],
        system_prompt=system_prompt,
        checkpointer=checkpointer,
    )

    return agent