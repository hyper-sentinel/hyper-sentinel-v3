"""
Analyst Agent — Market research, macro analysis, sentiment.

Tools: CoinGecko prices, FRED macro, Y2 news, Elfa social, X/Twitter
"""

from agno.agent import Agent

from scrapers.crypto_scraper import get_crypto_price, get_crypto_top_n, search_crypto
from scrapers.fred_scraper import get_fred_series, get_economic_dashboard, search_fred
from scrapers.y2_scraper import (
    get_news_sentiment, get_news_recap,
    get_intelligence_reports, get_report_detail,
)
from scrapers.elfa_scraper import (
    get_trending_tokens, get_top_mentions,
    search_mentions, get_trending_narratives, get_token_news,
)
from scrapers.x_scraper import XScraper


def _search_tweets(query: str, max_tweets: int = 50) -> list:
    """Search recent tweets by keyword."""
    x = XScraper()
    return x.search_tweets(query, max_tweets)


def _get_trending_topics() -> list:
    """Get worldwide trending topics on X/Twitter."""
    x = XScraper()
    return x.get_trending_topics()


def create_analyst_agent(model) -> Agent:
    """Create the Analyst specialist agent."""
    return Agent(
        name="Analyst",
        role="Market Research & Macro Analysis Specialist",
        model=model,
        tools=[
            # Crypto prices
            get_crypto_price,
            get_crypto_top_n,
            search_crypto,
            # FRED macro
            get_fred_series,
            get_economic_dashboard,
            search_fred,
            # Y2 News
            get_news_sentiment,
            get_news_recap,
            get_intelligence_reports,
            get_report_detail,
            # Elfa social
            get_trending_tokens,
            get_top_mentions,
            search_mentions,
            get_trending_narratives,
            get_token_news,
            # X/Twitter
            _search_tweets,
            _get_trending_topics,
        ],
        instructions=[
            "You are the Analyst on a crypto trading team.",
            "Your job: research markets, analyze macro conditions, and surface sentiment signals.",
            "Use FRED for macro (GDP, CPI, rates, VIX). Use CoinGecko for crypto prices.",
            "Use Y2 for news sentiment. Use Elfa for social trending. Use X for tweet analysis.",
            "Be quantitative. Cite specific numbers, changes, and percentages.",
            "Flag anything unusual — divergences, extreme sentiment, macro shifts.",
            "You do NOT execute trades. You provide analysis for the Trader and Risk Manager.",
        ],
        markdown=True,
        add_datetime_to_context=True,
    )
