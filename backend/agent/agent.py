import os

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

from backend.tools.news_tool import get_news
from backend.tools.article_tool import fetch_article
from backend.tools.summarization_tool import summarize_article
from backend.tools.calculator_tool import calculate
from backend.tools.email_tool import send_email
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
- Use summarize_article when you need to summarize article content.
- For research tasks, you may use multiple tools sequentially:
  get_news -> fetch_article -> summarize_article.
- Use calculate only when the user needs a mathematical calculation.
- Do not use calculate for general questions.
- Use send_email only when the user explicitly asks to send a report by email.
- Sending an email is a sensitive external action.
- Never send an email unless the application has received explicit user approval.

"""

    agent = create_agent(
        model=model,
       tools=[
    get_news,
    fetch_article,
    summarize_article,
    calculate,
    send_email,
    ],
    )

    return agent