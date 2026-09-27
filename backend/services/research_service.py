import json
import time

from backend.agent.agent import create_news_agent
from backend.services.observability import (
    log_agent_start,
    log_agent_success,
    log_agent_error,
)
from backend.state.agent_state import AgentState


MAX_HISTORY_MESSAGES = 10
MAX_AGENT_STEPS = 6


def run_research(
    topic: str,
    conversation_history: list | None = None,
    thread_id: str | None = None,
) -> dict:

    start_time = time.perf_counter()

    # Initial agent state
    state: AgentState = {
        "thread_id": thread_id or "",
        "topic": topic,
        "messages": list(conversation_history or []),
        "sources": [],
        "tools_used": [],
        "execution_time": 0,
        "final_answer": "",
    }

    log_agent_start(thread_id, topic)

    try:
        agent = create_news_agent()

        # Copy conversation history
        messages = list(conversation_history or [])

        # Context management:
        # keep only the most recent messages
        if len(messages) > MAX_HISTORY_MESSAGES:
            messages = messages[-MAX_HISTORY_MESSAGES:]

        # Add current user request
        messages.append(
            {
                "role": "user",
                "content": topic,
            }
        )

        # Update state with messages actually sent to the agent
        state["messages"] = messages

        # Limit agent execution
        config = {
            "recursion_limit": MAX_AGENT_STEPS,
        }

        # Keep execution connected to the current session
        if thread_id:
            config["configurable"] = {
                "thread_id": thread_id,
            }

        result = agent.invoke(
            {
                "messages": messages,
            },
            config=config,
        )

        execution_time = time.perf_counter() - start_time

        result_messages = result.get("messages", [])

        final_answer = ""
        tools_used = []
        sources = []

        # Read agent execution messages
        for message in result_messages:

            # Detect tool calls made by the agent
            if hasattr(message, "tool_calls"):

                for tool_call in message.tool_calls:

                    tool_name = tool_call.get("name")

                    if tool_name and tool_name not in tools_used:
                        tools_used.append(tool_name)

            # Detect tool result messages
            if hasattr(message, "name") and message.name:

                if message.name not in tools_used:
                    tools_used.append(message.name)

                # Extract sources from get_news
                if message.name == "get_news":

                    try:
                        tool_data = json.loads(message.content)

                        articles = tool_data.get(
                            "articles",
                            [],
                        )

                        for article in articles:

                            title = article.get(
                                "title",
                                "",
                            )

                            url = article.get(
                                "url",
                                "",
                            )

                            if title and url:
                                sources.append(
                                    {
                                        "title": title,
                                        "url": url,
                                    }
                                )

                    except (
                        json.JSONDecodeError,
                        TypeError,
                    ):
                        pass

            # Keep the latest text response
            if hasattr(message, "content") and message.content:

                if isinstance(message.content, str):
                    final_answer = message.content

        # Update state after execution
        state["sources"] = sources
        state["tools_used"] = tools_used
        state["execution_time"] = execution_time
        state["final_answer"] = final_answer

        log_agent_success(
            thread_id=thread_id,
            tools_used=tools_used,
            execution_time=execution_time,
        )

        return {
            "answer": state["final_answer"],
            "sources": state["sources"],
            "tools_used": state["tools_used"],
            "execution_time": round(
                state["execution_time"],
                2,
            ),
        }

    except TimeoutError as error:

        log_agent_error(thread_id, error)

        return {
            "answer": "The research request timed out. Please try again.",
            "sources": [],
            "tools_used": [],
            "execution_time": round(
                time.perf_counter() - start_time,
                2,
            ),
        }

    except Exception as error:

        log_agent_error(thread_id, error)

        return {
            "answer": f"Agent execution failed: {str(error)}",
            "sources": [],
            "tools_used": [],
            "execution_time": round(
                time.perf_counter() - start_time,
                2,
            ),
        }