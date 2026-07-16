"""News & Sentiment agent: recent headlines and market sentiment via web search."""

from __future__ import annotations

from .base import Agent

# Server-side tool — Claude executes the search itself; no local implementation needed.
TOOLS = [
    {"type": "web_search_20260209", "name": "web_search", "max_uses": 5},
]

SYSTEM_PROMPT = """You are the News & Sentiment agent in a multi-agent financial analysis system.

Search the web for recent news (ideally within the last 1-2 weeks) about the requested \
company/ticker. Then summarize:
1. Key recent headlines, each with a rough date and source
2. Overall sentiment (Positive / Neutral / Negative) with a brief justification
3. Any material events that could move the stock: earnings, guidance changes, litigation, \
   M&A activity, leadership changes, or regulatory action

Be strictly factual — only report what your searches actually returned. If you find little \
or no recent news, say so rather than inventing headlines. Do not give a buy/sell \
recommendation.
"""


def build_sentiment_agent() -> Agent:
    return Agent(
        name="sentiment",
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        tool_impls={},
        effort="medium",
        max_tokens=2048,
    )
