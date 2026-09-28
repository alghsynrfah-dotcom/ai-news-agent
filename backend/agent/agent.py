
import json
import os
import re

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from backend.tools.news_tool import get_news
from backend.tools.article_tool import fetch_article
from backend.tools.summarization_tool import summarize_article
from backend.tools.calculator_tool import calculate
from backend.tools.email_tool import send_email


load_dotenv()


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

    tools = {
        "get_news": get_news,
        "fetch_article": fetch_article,
        "summarize_article": summarize_article,
        "calculate": calculate,
        "send_email": send_email,
    }

    system_prompt = """
You are a ReAct news research assistant.

You MUST use the following exact format when using a tool:

Thought: I need to ...
Action: tool_name
Action Input: tool input

After the tool executes, you will receive:

Observation: tool result

Then continue reasoning.

When you have enough information, finish with:

Final Answer: your answer

AVAILABLE TOOLS:

get_news
- Use this for current or recent news.
- For ANY question asking for latest, recent, current, today's,
  breaking, or newest news, you MUST use get_news FIRST.
- Do NOT answer current-news questions from your own knowledge.

fetch_article
- Use this to read a specific article.

summarize_article
- Use this to summarize article content.

calculate
- Use this for mathematical calculations.

send_email
- Use this ONLY when the user explicitly asks to send an email.

IMPORTANT RULES:

1. Current/recent news MUST use get_news.
IMPORTANT RULES:

1. Current/recent news MUST use get_news.
2. Any mathematical calculation MUST use calculate.
3. Never calculate mathematical expressions yourself.
4. If the user explicitly asks to use a specific tool, you MUST use that tool.
5. Do not invent news or sources.
6. Do not give a generic answer instead of using the required tool.
7. After receiving an Observation, decide whether another tool is needed.
8. Only produce Final Answer after using the required tool.
9. Keep the final answer concise.
"""

    def invoke(question: str):

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": question,
            },
        ]

        tools_used = []
        sources = []

        for _ in range(5):

            response = model.invoke(messages)

            content = response.content

            if not isinstance(content, str):
                content = str(content)

            # --------------------------------------------------
            # FINAL ANSWER
            # --------------------------------------------------

            if "Final Answer:" in content:

                final_answer = content.split(
                    "Final Answer:",
                    1,
                )[1].strip()

                return {
                    "answer": final_answer,
                    "tools_used": tools_used,
                    "sources": sources,
                }

            # --------------------------------------------------
            # FIND ACTION
            # --------------------------------------------------

            action_match = re.search(
                r"Action:\s*([a-zA-Z_]+)",
                content,
                re.IGNORECASE,
            )

            input_match = re.search(
                r"Action Input:\s*(.*)",
                content,
                re.IGNORECASE | re.DOTALL,
            )

            if not action_match or not input_match:

                messages.append(
                    {
                        "role": "assistant",
                        "content": content,
                    }
                )

                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Observation: "
                            "Your response did not follow the "
                            "required ReAct format. "
                            "You must provide Thought, Action, "
                            "and Action Input. "
                            "For current or recent news, "
                            "use get_news first."
                        ),
                    }
                )

                continue

            tool_name = action_match.group(1).strip()
            tool_input = input_match.group(1).strip()

            # --------------------------------------------------
            # CHECK TOOL
            # --------------------------------------------------

            if tool_name not in tools:

                messages.append(
                    {
                        "role": "assistant",
                        "content": content,
                    }
                )

                messages.append(
                    {
                        "role": "user",
                        "content": (
                            f"Observation: Unknown tool "
                            f"'{tool_name}'. "
                            f"Available tools are: "
                            f"{', '.join(tools.keys())}"
                        ),
                    }
                )

                continue

            tool = tools[tool_name]

            # --------------------------------------------------
            # EXECUTE TOOL
            # --------------------------------------------------

            try:

                if hasattr(tool, "invoke"):

                    if tool_name == "get_news":

                        observation = tool.invoke(
                            {
                                "topic": tool_input
                            }
                        )

                    else:

                        observation = tool.invoke(
                            tool_input
                        )

                else:

                    observation = tool(tool_input)

            except Exception as error:

                observation = (
                    f"Tool error: {str(error)}"
                )

            # --------------------------------------------------
            # TRACK TOOL
            # --------------------------------------------------

            if tool_name not in tools_used:

                tools_used.append(tool_name)

            # --------------------------------------------------
            # EXTRACT SOURCES FROM NEWS TOOL
            # --------------------------------------------------

            if tool_name == "get_news":

                try:

                    news_data = json.loads(
                        observation
                    )

                    articles = news_data.get(
                        "articles",
                        [],
                    )

                    if isinstance(
                        articles,
                        list,
                    ):

                        sources.extend(
                            articles
                        )

                except (
                    json.JSONDecodeError,
                    TypeError,
                ):
                    pass

            # --------------------------------------------------
            # ADD REACT MESSAGES
            # --------------------------------------------------

            messages.append(
                {
                    "role": "assistant",
                    "content": content,
                }
            )

            messages.append(
                {
                    "role": "user",
                    "content": (
                        f"Observation: {observation}"
                    ),
                }
            )

        # ------------------------------------------------------
        # MAX STEPS
        # ------------------------------------------------------

        return {
            "answer": (
                "The agent reached the maximum "
                "number of reasoning steps."
            ),
            "tools_used": tools_used,
            "sources": sources,
        }

    class ReActAgent:

        def __init__(self, invoke_function):

            self.invoke_function = (
                invoke_function
            )

        def invoke(
            self,
            input_data,
            config=None,
        ):

            if isinstance(
                input_data,
                dict,
            ):

                topic = input_data.get(
                    "topic"
                )

                if not topic:

                    topic = input_data.get(
                        "question"
                    )

                if not topic:

                    messages = input_data.get(
                        "messages",
                        [],
                    )

                    if messages:

                        last_message = (
                            messages[-1]
                        )

                        if isinstance(
                            last_message,
                            dict,
                        ):

                            topic = (
                                last_message.get(
                                    "content",
                                    "",
                                )
                            )

                        else:

                            topic = str(
                                last_message
                            )

                if not topic:

                    topic = ""

            else:

                topic = str(input_data)

            return self.invoke_function(
                topic
            )

    return ReActAgent(invoke)
