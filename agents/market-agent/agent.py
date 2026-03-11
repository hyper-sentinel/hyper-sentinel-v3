"""
Hyper-Sentinel v3 — MarketAgent Intelligence Layer
====================================================
Upsonic Agent with YFinanceTools and Safety Engine policies.
This is the brain — the subscriber triggers it, this does the thinking.

Pattern: Upsonic Agent + Task (from tobalo/agentic-osint agents.py)
Safety: PIIAnonymizePolicy on inputs, FinancialDataPolicy on outputs
Tools: YFinanceTools for real-time market data
"""

import json
import logging
from typing import Optional

from upsonic import Agent, Task
from upsonic.tools.common_tools import YFinanceTools

# Safety Engine policies
try:
    from upsonic.safety_engine.policies.pii_policies import PIIAnonymizePolicy
    from upsonic.safety_engine.policies.financial_policies import FinancialDataPolicy

    HAS_SAFETY_ENGINE = True
except ImportError:
    HAS_SAFETY_ENGINE = False

from config import AgentConfig, DEFAULT_SYMBOLS
from models import MarketDataRequest, MarketAnalysis, Anomaly, RiskLevel

logger = logging.getLogger(__name__)

# ─── System Instructions ───────────────────────────────────────

MARKET_AGENT_INSTRUCTIONS = """You are MarketAgent, a production-grade financial market surveillance AI.
Your role is to analyze market data and detect anomalies across equity and crypto markets.

RESPONSIBILITIES:
1. Monitor key market indicators (price, volume, volatility, momentum)
2. Detect statistical anomalies and unusual market behavior
3. Assess risk levels for each observed anomaly
4. Produce structured, actionable intelligence reports

OUTPUT FORMAT — You MUST respond with valid JSON matching this structure:
{
    "analysis": "<comprehensive market analysis text>",
    "anomalies": [
        {
            "symbol": "<ticker>",
            "description": "<what was detected>",
            "severity": "low|medium|high|critical",
            "metric": "<which metric triggered this>",
            "value": <observed value or null>,
            "threshold": <expected threshold or null>
        }
    ],
    "risk_level": "low|medium|high|critical",
    "confidence": <0.0-1.0>
}

RULES:
- Always use the YFinanceTools to get REAL market data. Never fabricate prices.
- Flag any single-day move >2% on SPY or QQQ as an anomaly.
- Flag any single-day move >5% on BTC-USD as an anomaly.
- Flag unusual volume (>2x 20-day average) as an anomaly.
- Be precise. Include numbers and percentages.
- Confidence should reflect data quality and analysis certainty.
"""


def _build_agent(config: AgentConfig) -> Agent:
    """
    Construct the Upsonic Agent with tools and safety policies.

    This mirrors the pattern from agentic-osint/agents.py but uses
    Upsonic's Agent class instead of phi.agent.Agent.
    """
    agent_kwargs = {
        "model": config.resolved_model,
        "name": config.agent_name,
    }

    # Apply Safety Engine policies if available
    if HAS_SAFETY_ENGINE:
        agent_kwargs["user_policy"] = PIIAnonymizePolicy
        agent_kwargs["agent_policy"] = FinancialDataPolicy
        logger.info("Safety Engine enabled: PIIAnonymizePolicy + FinancialDataPolicy")
    else:
        logger.warning(
            "Safety Engine not available. Install with: "
            'pip install "upsonic[safety]"'
        )

    agent = Agent(**agent_kwargs)
    logger.info(
        f"MarketAgent initialized: provider={config.llm_provider}, "
        f"model={config.resolved_model}"
    )
    return agent


def _parse_response(raw_response: str) -> dict:
    """
    Parse LLM response, extracting JSON from potential markdown code blocks.
    The LLM sometimes wraps JSON in ```json...``` blocks.
    """
    text = str(raw_response).strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (``` markers)
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # If JSON parsing fails, wrap the raw text as analysis
        return {
            "analysis": text,
            "anomalies": [],
            "risk_level": "low",
            "confidence": 0.3,
        }


async def analyze_market(
    request: MarketDataRequest, config: AgentConfig
) -> MarketAnalysis:
    """
    Run the MarketAgent against a market data request.

    Flow:
        1. Build the Upsonic Agent with tools + safety
        2. Construct task description from the request
        3. Execute the agent
        4. Parse structured response into MarketAnalysis

    Args:
        request: Incoming market data request from NATS
        config: Agent configuration

    Returns:
        MarketAnalysis ready to publish to sentinel.risk.input
    """
    agent = _build_agent(config)

    # Construct the task prompt
    symbols_str = ", ".join(request.symbols)
    task_description = (
        f"Perform a {request.request_type.value} analysis on the following symbols: "
        f"{symbols_str}. Timeframe: {request.timeframe}. "
        f"Use YFinanceTools to get current market data. "
        f"Analyze price action, volume, and momentum. "
        f"Detect any anomalies and assess overall risk."
    )

    task = Task(
        description=task_description,
        tools=[
            YFinanceTools(
                stock_price=True,
                analyst_recommendations=True,
                company_info=True,
                company_news=True,
            )
        ],
    )

    logger.info(f"Executing analysis: {request.request_type.value} on {symbols_str}")

    # Execute the agent
    result = agent.do(task)
    parsed = _parse_response(str(result))

    # Build structured MarketAnalysis
    anomalies = []
    for a in parsed.get("anomalies", []):
        try:
            anomalies.append(
                Anomaly(
                    symbol=a.get("symbol", "UNKNOWN"),
                    description=a.get("description", ""),
                    severity=RiskLevel(a.get("severity", "medium")),
                    metric=a.get("metric"),
                    value=a.get("value"),
                    threshold=a.get("threshold"),
                )
            )
        except (ValueError, KeyError) as e:
            logger.warning(f"Failed to parse anomaly: {e}")

    analysis = MarketAnalysis(
        request_id=request.request_id,
        agent_name=config.agent_name,
        analysis=parsed.get("analysis", str(result)),
        anomalies=anomalies,
        risk_level=RiskLevel(parsed.get("risk_level", "low")),
        confidence=float(parsed.get("confidence", 0.5)),
        symbols_analyzed=request.symbols,
        provider=config.llm_provider,
        model=config.resolved_model,
    )

    logger.info(
        f"Analysis complete: risk={analysis.risk_level.value}, "
        f"anomalies={len(analysis.anomalies)}, "
        f"confidence={analysis.confidence:.2f}"
    )

    return analysis


def analyze_market_chat(user_input: str) -> str:
    """
    Synchronous chat function for the interactive REPL.
    Takes a natural-language question, runs the MarketAgent, returns text.
    """
    config = AgentConfig()
    agent = _build_agent(config)

    task = Task(
        description=user_input,
        tools=[
            YFinanceTools(
                stock_price=True,
                analyst_recommendations=True,
                company_info=True,
                company_news=True,
            )
        ],
    )

    result = agent.do(task)
    return str(result)

