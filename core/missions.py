"""
Sentinel Missions — Standing orders that run continuously.

A mission is a goal you give Sentinel that runs on a schedule:
  • "Monitor BTC and alert me if it drops below $80K"
  • "Send me a morning briefing at 8am"
  • "Trail stop my ETH position at 5% below peak"

Missions persist across restarts via the memory store.
"""

import os
import json
import logging
from datetime import datetime
from typing import Callable, Optional
from pathlib import Path

logger = logging.getLogger("sentinel.missions")


class Mission:
    """A standing order for Sentinel."""

    def __init__(
        self,
        name: str,
        description: str,
        template: str,
        params: dict | None = None,
        interval_minutes: int = 15,
        active: bool = True,
    ):
        self.id = f"mission_{name.lower().replace(' ', '_')}_{int(datetime.now().timestamp())}"
        self.name = name
        self.description = description
        self.template = template
        self.params = params or {}
        self.interval_minutes = interval_minutes
        self.active = active
        self.created_at = datetime.now().isoformat()
        self.last_run = None
        self.run_count = 0
        self.results: list[dict] = []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "template": self.template,
            "params": self.params,
            "interval_minutes": self.interval_minutes,
            "active": self.active,
            "created_at": self.created_at,
            "last_run": self.last_run,
            "run_count": self.run_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Mission":
        m = cls(
            name=data["name"],
            description=data["description"],
            template=data["template"],
            params=data.get("params", {}),
            interval_minutes=data.get("interval_minutes", 15),
            active=data.get("active", True),
        )
        m.id = data.get("id", m.id)
        m.created_at = data.get("created_at", m.created_at)
        m.last_run = data.get("last_run")
        m.run_count = data.get("run_count", 0)
        return m


# ── Mission Templates ────────────────────────────────────────────────

MISSION_TEMPLATES = {
    "price_alert": {
        "name": "Price Alert",
        "description": "Alert when {symbol} crosses ${threshold}",
        "prompt": (
            "Check the current price of {symbol}. "
            "If it's {direction} ${threshold}, alert me with the current price "
            "and 24h change percentage. If not, just note the current price."
        ),
        "default_params": {"symbol": "bitcoin", "threshold": 80000, "direction": "below"},
        "interval": 15,
    },
    "morning_briefing": {
        "name": "Morning Briefing",
        "description": "Daily market summary at {time}",
        "prompt": (
            "Give me a comprehensive morning briefing:\n"
            "1. Top 5 crypto prices and 24h changes\n"
            "2. Significant market news from Y2\n"
            "3. Social sentiment summary from Elfa\n"
            "4. FRED macro indicators (latest)\n"
            "5. My open positions (if any)\n"
            "Keep it concise and actionable."
        ),
        "default_params": {"time": "08:00"},
        "interval": 1440,  # daily
    },
    "position_watch": {
        "name": "Position Watch",
        "description": "Monitor open positions for drawdown > {max_dd}%",
        "prompt": (
            "Check all my Hyperliquid positions. For each:\n"
            "- Report unrealized PnL and percentage\n"
            "- Flag any position down more than {max_dd}%\n"
            "- Flag any position with leverage above {max_leverage}x\n"
            "- Recommend if I should hold, reduce, or close"
        ),
        "default_params": {"max_dd": 5, "max_leverage": 10},
        "interval": 30,
    },
    "sentiment_scan": {
        "name": "Sentiment Scan",
        "description": "Scan social sentiment for {topics}",
        "prompt": (
            "Scan social sentiment for: {topics}\n"
            "Use Y2 news and Elfa social intelligence.\n"
            "Report:\n"
            "- Overall sentiment (bullish/bearish/neutral)\n"
            "- Any significant spikes or shifts\n"
            "- Top trending topics\n"
            "- Notable news items"
        ),
        "default_params": {"topics": "bitcoin, ethereum, solana"},
        "interval": 60,
    },
    "trail_stop": {
        "name": "Trail Stop",
        "description": "Trail stop {symbol} at {trail_pct}% below peak",
        "prompt": (
            "Check the current price of {symbol} on Hyperliquid.\n"
            "Track the highest price seen since this mission started.\n"
            "If the price has dropped {trail_pct}% from the peak, "
            "recommend closing the position immediately.\n"
            "Report: current price, peak price, drawdown from peak."
        ),
        "default_params": {"symbol": "ETH", "trail_pct": 5},
        "interval": 5,
    },
}


class MissionController:
    """
    Manages, persists, and executes missions.
    """

    def __init__(self, data_dir: str = "data/missions"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.missions: dict[str, Mission] = {}
        self._load_missions()

    # ── CRUD ─────────────────────────────────────────────────────────

    def create_mission(
        self,
        template_key: str,
        params: dict | None = None,
        interval: int | None = None,
    ) -> Mission:
        """Create a mission from a template."""
        if template_key not in MISSION_TEMPLATES:
            raise ValueError(
                f"Unknown template: {template_key}. "
                f"Available: {', '.join(MISSION_TEMPLATES.keys())}"
            )

        tmpl = MISSION_TEMPLATES[template_key]
        merged_params = {**tmpl["default_params"], **(params or {})}

        mission = Mission(
            name=tmpl["name"],
            description=tmpl["description"].format(**merged_params),
            template=template_key,
            params=merged_params,
            interval_minutes=interval or tmpl["interval"],
        )

        self.missions[mission.id] = mission
        self._save_missions()
        logger.info(f"Mission created: {mission.name} ({mission.id})")
        return mission

    def pause_mission(self, mission_id: str) -> bool:
        if mission_id in self.missions:
            self.missions[mission_id].active = False
            self._save_missions()
            return True
        return False

    def resume_mission(self, mission_id: str) -> bool:
        if mission_id in self.missions:
            self.missions[mission_id].active = True
            self._save_missions()
            return True
        return False

    def delete_mission(self, mission_id: str) -> bool:
        if mission_id in self.missions:
            del self.missions[mission_id]
            self._save_missions()
            return True
        return False

    def list_missions(self) -> list[dict]:
        return [m.to_dict() for m in self.missions.values()]

    def get_active_missions(self) -> list[Mission]:
        return [m for m in self.missions.values() if m.active]

    # ── Execution ────────────────────────────────────────────────────

    def execute_mission(self, mission: Mission, agent_chat_fn: Callable) -> str:
        """Execute a mission by sending its prompt to the agent."""
        tmpl = MISSION_TEMPLATES.get(mission.template, {})
        prompt_template = tmpl.get("prompt", mission.description)

        # Build the prompt with params
        try:
            prompt = prompt_template.format(**mission.params)
        except KeyError:
            prompt = prompt_template

        # Execute via agent
        logger.info(f"Executing mission: {mission.name}")
        result = agent_chat_fn(prompt)

        # Update mission state
        mission.last_run = datetime.now().isoformat()
        mission.run_count += 1
        mission.results.append({
            "timestamp": mission.last_run,
            "result": result[:1000],  # truncate for storage
        })
        # Keep only last 10 results
        mission.results = mission.results[-10:]
        self._save_missions()

        return result

    # ── Persistence ──────────────────────────────────────────────────

    def _save_missions(self):
        """Save all missions to disk."""
        data = {mid: m.to_dict() for mid, m in self.missions.items()}
        save_file = self.data_dir / "missions.json"
        save_file.write_text(json.dumps(data, indent=2))

    def _load_missions(self):
        """Load missions from disk."""
        load_file = self.data_dir / "missions.json"
        if load_file.exists():
            try:
                data = json.loads(load_file.read_text())
                for mid, mdata in data.items():
                    self.missions[mid] = Mission.from_dict(mdata)
                logger.info(f"Loaded {len(self.missions)} missions from disk")
            except Exception as e:
                logger.error(f"Failed to load missions: {e}")
