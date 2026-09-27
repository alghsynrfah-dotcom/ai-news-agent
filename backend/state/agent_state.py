from typing import TypedDict


class AgentState(TypedDict, total=False):
    thread_id: str
    topic: str
    messages: list
    sources: list[dict]
    tools_used: list[str]
    execution_time: float
    final_answer: str