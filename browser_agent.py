"""
Browser Agent — Three Tiers of Browser Interaction

Tier 1: open_in_browser  — Fast, direct (macOS: open -a Chrome, uses real profile)
Tier 2: browse_url       — LLM-driven (browser-use, any provider)
Tier 3: computer_use     — Full AI computer control (Claude only)

Usage:
    from browser_agent import open_in_browser, is_browser_command
    if is_browser_command(user_input):
        result = open_in_browser(user_input)  # instant, real Chrome
"""

import asyncio
import os
import re
import sys
import logging
import subprocess
import platform
from typing import Optional

logger = logging.getLogger("browser_agent")


# ════════════════════════════════════════════════════════════════
# TIER 1: FAST-PATH — Opens real Chrome with user's profile
# ════════════════════════════════════════════════════════════════

def is_browser_command(text: str) -> bool:
    """Detect if user input is a browser/open command."""
    text_lower = text.lower().strip()
    # Match: open youtube, browse google, go to tradingview, etc.
    if re.match(r'^(open|browse|go\s+to|launch|navigate\s+to)\s+', text_lower):
        return True
    return False


def open_in_browser(text: str) -> str:
    """
    Tier 1: Fast-path browser open — uses the user's REAL Chrome.
    
    Opens the URL in Chrome with the user's existing profile, so all
    accounts (YouTube, Gmail, TradingView, etc.) are already signed in.
    No LLM cost, no Playwright, instant.
    
    Args:
        text: Natural language like "open youtube" or "go to tradingview"
    
    Returns:
        Status message
    """
    url = _extract_url(text)
    if not url:
        return f"Couldn't find a URL in: {text}"
    
    system = platform.system()
    
    try:
        if system == "Darwin":  # macOS
            # open -a opens with the real Chrome app (signed-in profile)
            subprocess.Popen(
                ["open", "-a", "Google Chrome", url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif system == "Linux":
            subprocess.Popen(
                ["xdg-open", url],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        elif system == "Windows":
            subprocess.Popen(
                ["start", "chrome", url],
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            return f"Unsupported OS: {system}"
        
        # Extract the site name for a clean message
        site_name = url.replace("https://", "").replace("http://", "").replace("www.", "").split("/")[0]
        return f"🌐 Opened {site_name} in Chrome"
    except FileNotFoundError:
        return f"Chrome not found. Install Google Chrome or set a custom browser."
    except Exception as e:
        return f"Failed to open browser: {e}"


def _extract_url(text: str) -> Optional[str]:
    """Extract a URL from natural language text.
    
    Handles:
    - Full URLs: https://youtube.com, http://example.com
    - Domain-like: youtube.com, tradingview.com, x.com
    - Common names: youtube, google, twitter, tradingview
    """
    # 1. Check for full URL
    url_match = re.search(r'https?://[^\s"\'<>]+', text, re.IGNORECASE)
    if url_match:
        return url_match.group(0)
    
    # 2. Check for domain-like patterns (word.tld)
    domain_match = re.search(r'\b([a-zA-Z0-9][-a-zA-Z0-9]*\.(com|org|net|io|co|xyz|dev|ai|finance|exchange))\b', text, re.IGNORECASE)
    if domain_match:
        return f"https://{domain_match.group(1)}"
    
    # 3. Common site name mapping
    site_map = {
        # Social / Chat
        "youtube": "https://www.youtube.com",
        "google": "https://www.google.com",
        "twitter": "https://twitter.com",
        "x": "https://x.com",
        "reddit": "https://www.reddit.com",
        "discord": "https://discord.com",
        "telegram": "https://web.telegram.org",
        "signal": "https://signal.org",
        "whatsapp": "https://web.whatsapp.com",
        "instagram": "https://www.instagram.com",
        "facebook": "https://www.facebook.com",
        "linkedin": "https://www.linkedin.com",
        "tiktok": "https://www.tiktok.com",
        # Trading / Finance
        "tradingview": "https://www.tradingview.com",
        "coingecko": "https://www.coingecko.com",
        "coinmarketcap": "https://coinmarketcap.com",
        "binance": "https://www.binance.com",
        "coinbase": "https://www.coinbase.com",
        "robinhood": "https://robinhood.com",
        "asterdex": "https://www.asterdex.com",
        "aster": "https://www.asterdex.com",
        "hyperliquid": "https://app.hyperliquid.xyz",
        "polymarket": "https://polymarket.com",
        "dexscreener": "https://dexscreener.com",
        "dextools": "https://www.dextools.io",
        "uniswap": "https://app.uniswap.org",
        "jupiter": "https://jup.ag",
        "raydium": "https://raydium.io",
        # Dev / Tools
        "github": "https://github.com",
        "chatgpt": "https://chatgpt.com",
        "claude": "https://claude.ai",
        "notion": "https://www.notion.so",
        "figma": "https://www.figma.com",
        # News
        "bloomberg": "https://www.bloomberg.com",
        "cnbc": "https://www.cnbc.com",
        "coindesk": "https://www.coindesk.com",
        "cointelegraph": "https://cointelegraph.com",
    }
    
    text_lower = text.lower()
    for name, url in site_map.items():
        # Match "open youtube", "go to youtube", "youtube.com", etc.
        if re.search(rf'\b{name}\b', text_lower):
            return url
    
    return None


class BrowserUseAgent:
    """
    Browser automation via the browser-use library.
    Works with any LLM provider (Claude, GPT, Gemini).
    """

    def __init__(self):
        self._agent = None

    async def browse(self, task: str, url: Optional[str] = None) -> str:
        """
        Execute a browser task using natural language.

        Args:
            task: What to do (e.g. "Check BTC price on TradingView")
            url: Optional starting URL

        Returns:
            Text result of the task
        """
        try:
            from browser_use import Agent as BUAgent
            from langchain_anthropic import ChatAnthropic
            from langchain_openai import ChatOpenAI
        except ImportError as e:
            return (
                f"Browser-Use not installed: {e}\n"
                "Install with: pip install browser-use langchain-anthropic langchain-openai"
            )

        # Auto-extract URL from task if not explicitly provided
        if not url:
            url = _extract_url(task)

        # Auto-detect LLM provider
        llm = self._get_llm()
        if not llm:
            return "No LLM provider configured. Set ANTHROPIC_API_KEY or OPENAI_API_KEY."

        # Build the full task
        full_task = task
        if url:
            full_task = f"Go to {url}. Then: {task}"

        try:
            agent = BUAgent(task=full_task, llm=llm)
            result = await agent.run()
            return str(result) if result else "Task completed."
        except Exception as e:
            logger.error(f"Browser-Use error: {e}")
            return f"Browser error: {e}"

    def browse_sync(self, task: str, url: Optional[str] = None) -> str:
        """Synchronous wrapper."""
        return asyncio.run(self.browse(task, url))

    def _get_llm(self):
        """Auto-detect and return the best available LLM."""
        # Try Claude first
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        if anthropic_key:
            try:
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(
                    model="claude-sonnet-4-20250514",
                    api_key=anthropic_key,
                )
            except ImportError:
                pass

        # Try OpenAI
        openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        if openai_key:
            try:
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model="gpt-4o",
                    api_key=openai_key,
                )
            except ImportError:
                pass

        # Try Gemini via OpenAI-compatible API
        gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        if gemini_key:
            try:
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(
                    model="gemini-2.0-flash",
                    api_key=gemini_key,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
                )
            except ImportError:
                pass

        return None


class ComputerUseWrapper:
    """
    Wraps ComputerUseAgent with the same interface as BrowserUseAgent.
    Used when Claude is the active provider (preferred).
    """

    def __init__(self, headless: bool = False):
        self.headless = headless

    async def browse(self, task: str, url: Optional[str] = None) -> str:
        # Auto-extract URL from task if not explicitly provided
        if not url:
            url = _extract_url(task)
        
        from computer_use import ComputerUseAgent
        agent = ComputerUseAgent(headless=self.headless)
        return await agent.run(task, url)

    def browse_sync(self, task: str, url: Optional[str] = None) -> str:
        return asyncio.run(self.browse(task, url))


def get_browser_agent(prefer_computer_use: bool = True, headless: bool = False):
    """
    Factory: returns the best browser agent based on available provider.

    - Claude API available + prefer_computer_use → ComputerUseWrapper (most powerful)
    - Claude API available + not prefer → BrowserUseAgent (still uses Claude via langchain)
    - GPT/Gemini only → BrowserUseAgent
    """
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()

    if anthropic_key and prefer_computer_use:
        logger.info("Using Anthropic Computer Use (native)")
        return ComputerUseWrapper(headless=headless)
    else:
        logger.info("Using Browser-Use (LLM-agnostic)")
        return BrowserUseAgent()
