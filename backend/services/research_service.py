
import time

from backend.agent.agent import create_news_agent

from backend.services.observability import (
    log_agent_start,
    log_agent_success,
    log_agent_error,
)

from backend.state.agent_state import AgentState


MAX_HISTORY_MESSAGES = 10


def run_research(
    topic: str,
    conversation_history: list | None = None,
    thread_id: str | None = None,
) -> dict:

    start_time = time.perf_counter()

    state: AgentState = {
        "thread_id": thread_id or "",
        "topic": topic,
        "messages": list(
            conversation_history or []
        ),
        "sources": [],
        "tools_used": [],
        "execution_time": 0,
        "final_answer": "",
    }

    log_agent_start(
        thread_id,
        topic,
    )

    try:

        agent = create_news_agent()

        if agent is None:
            raise RuntimeError(
                "create_news_agent() returned None."
            )

        messages = list(
            conversation_history or []
        )

        if len(messages) > MAX_HISTORY_MESSAGES:

            messages = messages[
                -MAX_HISTORY_MESSAGES:
            ]

        messages.append(
            {
                "role": "user",
                "content": topic,
            }
        )

        state["messages"] = messages

        result = agent.invoke(
            {
                "messages": messages,
            }
        )

        execution_time = (
            time.perf_counter()
            - start_time
        )

        # --------------------------------------------------
        # GET RESULT FROM REACT AGENT
        # --------------------------------------------------

        if isinstance(result, dict):

            final_answer = result.get(
                "answer",
                "",
            )

            tools_used = result.get(
                "tools_used",
                [],
            )

            sources = result.get(
                "sources",
                [],
            )

        else:

            final_answer = str(result)

            tools_used = []

            sources = []

        if not final_answer:

            final_answer = (
                "The agent did not return an answer."
            )

        # --------------------------------------------------
        # UPDATE STATE
        # --------------------------------------------------

        state["sources"] = sources

        state["tools_used"] = tools_used

        state["execution_time"] = (
            execution_time
        )

        state["final_answer"] = (
            final_answer
        )

        # --------------------------------------------------
        # LOG SUCCESS
        # --------------------------------------------------

        log_agent_success(
            thread_id=thread_id,
            tools_used=tools_used,
            execution_time=execution_time,
        )

        # --------------------------------------------------
        # RETURN
        # --------------------------------------------------

        return {
            "answer": final_answer,
            "sources": sources,
            "tools_used": tools_used,
            "execution_time": round(
                execution_time,
                2,
            ),
        }

    except TimeoutError as error:

        log_agent_error(
            thread_id,
            error,
        )

        return {
            "answer": (
                "The research request timed out. "
                "Please try again."
            ),
            "sources": [],
            "tools_used": [],
            "execution_time": round(
                time.perf_counter()
                - start_time,
                2,
            ),
        }

    except Exception as error:

        log_agent_error(
            thread_id,
            error,
        )

        return {
            "answer": (
                f"Agent execution failed: "
                f"{str(error)}"
            ),
            "sources": [],
            "tools_used": [],
            "execution_time": round(
                time.perf_counter()
                - start_time,
                2,
            ),
        }
