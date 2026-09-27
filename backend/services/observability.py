import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


logger = logging.getLogger("ai_news_agent")


def log_agent_start(thread_id: str | None, topic: str) -> None:
    logger.info(
        "Agent run started | thread_id=%s | topic=%s",
        thread_id,
        topic,
    )


def log_agent_success(
    thread_id: str | None,
    tools_used: list[str],
    execution_time: float,
) -> None:
    logger.info(
        "Agent run completed | thread_id=%s | tools=%s | execution_time=%.2fs",
        thread_id,
        tools_used,
        execution_time,
    )


def log_agent_error(
    thread_id: str | None,
    error: Exception,
) -> None:
    logger.error(
        "Agent run failed | thread_id=%s | error=%s",
        thread_id,
        str(error),
    )