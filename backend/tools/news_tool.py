import json

import requests
import feedparser
from langchain.tools import tool


NEWS_TIMEOUT = 10


@tool
def get_news(topic: str) -> str:
    """
    Get recent news headlines about a specific topic.

    Use this tool when the user asks for current or recent news.
    Do not use this tool for general questions that do not require
    current news.

    Input:
        topic: The news topic to search for.

    Output:
        JSON string containing recent news articles with title and URL.
    """

    if not topic or not topic.strip():
        return json.dumps(
            {
                "error": "Topic cannot be empty.",
                "articles": [],
            }
        )

    topic = topic.strip()

    if len(topic) > 100:
        return json.dumps(
            {
                "error": "Topic is too long.",
                "articles": [],
            }
        )

    url = (
        "https://news.google.com/rss/search?"
        f"q={requests.utils.quote(topic)}"
        "&hl=en-US&gl=US&ceid=US:en"
    )

    try:
        response = requests.get(
            url,
            timeout=NEWS_TIMEOUT,
        )

        response.raise_for_status()

        feed = feedparser.parse(response.content)

        if not feed.entries:
            return json.dumps(
                {
                    "error": f"No recent news found for: {topic}",
                    "articles": [],
                }
            )

        articles = []

        for entry in feed.entries[:5]:
            articles.append(
                {
                    "title": entry.get("title", "No title"),
                    "url": entry.get("link", ""),
                }
            )

        return json.dumps(
            {
                "topic": topic,
                "articles": articles,
            },
            ensure_ascii=False,
        )

    except requests.Timeout:
        return json.dumps(
            {
                "error": "News service timed out. Please try again later.",
                "articles": [],
            }
        )

    except requests.RequestException as error:
        return json.dumps(
            {
                "error": f"News service request failed: {str(error)}",
                "articles": [],
            }
        )

    except Exception as error:
        return json.dumps(
            {
                "error": f"Unexpected news tool failure: {str(error)}",
                "articles": [],
            }
        )