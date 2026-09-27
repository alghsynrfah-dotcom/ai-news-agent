MAX_TOPIC_LENGTH = 100


def validate_research_topic(topic: str) -> tuple[bool, str]:
    """
    Validate the user's research topic before sending it to the agent.
    """

    if not topic or not topic.strip():
        return False, "Research topic cannot be empty."

    topic = topic.strip()

    if len(topic) > MAX_TOPIC_LENGTH:
        return False, "Research topic is too long. Please keep it under 100 characters."

    return True, ""