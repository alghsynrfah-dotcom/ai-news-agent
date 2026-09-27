from backend.agent.agent import create_news_agent

agent = create_news_agent()

result = agent.invoke(
    {
        "messages": [
            {
                "role": "user",
                "content": "What are the latest news about artificial intelligence?",
            }
        ]
    },
    config={
        "configurable": {
            "thread_id": "test-thread-1",
        }
    },
)

for message in result["messages"]:
    print(message)