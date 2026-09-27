import requests
from bs4 import BeautifulSoup
from langchain.tools import tool
from urllib.parse import urlparse


ARTICLE_TIMEOUT = 10
MAX_CONTENT_LENGTH = 6000


@tool
def fetch_article(url: str) -> str:
    """
    Fetch readable text from a news article URL.

    Use this tool when the user needs more details from a specific
    news article or when the agent needs to inspect a source.

    Input:
        url: The URL of the article.

    Output:
        Clean article text or an error message.
    """

    if not url or not url.strip():
        return "Error: URL cannot be empty."

    url = url.strip()

    # Validate URL format
    parsed_url = urlparse(url)

    if parsed_url.scheme not in {"http", "https"}:
        return "Error: URL must use http or https."

    if not parsed_url.netloc:
        return "Error: Invalid URL."

    try:
        response = requests.get(
            url,
            timeout=ARTICLE_TIMEOUT,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "AI-News-Research-Agent"
                )
            },
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        # Remove elements that are not useful article content
        for element in soup(
            ["script", "style", "nav", "footer", "header"]
        ):
            element.decompose()

        text = soup.get_text(
            separator=" ",
            strip=True,
        )

        if not text:
            return "Error: No readable article content found."

        # Limit large tool output
        text = text[:MAX_CONTENT_LENGTH]

        return text

    except requests.Timeout:
        return (
            "Error: Article request timed out. "
            "Please try again later."
        )

    except requests.RequestException as error:
        return (
            f"Error: Article request failed: {str(error)}"
        )

    except Exception as error:
        return (
            f"Error: Unexpected article tool failure: "
            f"{str(error)}"
        )