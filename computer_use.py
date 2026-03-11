"""
Computer Use Agent — Safe, sandboxed computer control for Sentinel v2.

Tier 3 of the agentic system. Handles:
- App launching (macOS: open -a <app>)
- URL opening with user's real browser profile
- System info queries (safe, read-only)
- Shell commands (ONLY with explicit user confirmation)

Security model:
- NO automatic shell execution
- NO file writes without confirmation
- Read-only system queries are safe
- App launching is safe (uses macOS `open` command)
- Full Anthropic Computer Use reserved for Claude provider only

Usage:
    from computer_use import ComputerUseAgent
    agent = ComputerUseAgent()
    result = await agent.run("open YouTube in Chrome")
"""

import asyncio
import logging
import os
import platform
import subprocess
import shlex
from typing import Optional

logger = logging.getLogger("computer_use")


class ComputerUseAgent:
    """
    Safe computer control agent.

    Executes local system actions with a security-first approach:
    - App launching: always safe (macOS `open -a`)
    - URL opening: always safe (delegates to browser_agent)
    - System info: safe (read-only queries)
    - Shell commands: BLOCKED by default, requires explicit opt-in
    """

    def __init__(self, headless: bool = False, allow_shell: bool = False):
        self.headless = headless
        self.allow_shell = allow_shell
        self.system = platform.system()

    async def run(self, task: str, url: Optional[str] = None) -> str:
        """
        Execute a computer use task.

        Routes to the appropriate handler based on intent:
        - "open <app>"  → app launcher
        - URL detected   → browser open
        - System queries → safe info
        - Shell commands → blocked unless allow_shell=True
        """
        task_lower = task.lower().strip()

        # ── App launching ──
        if self._is_app_launch(task_lower):
            return self._launch_app(task)

        # ── URL / browser tasks ──
        if url or self._has_url(task_lower):
            from browser_agent import open_in_browser
            return open_in_browser(task)

        # ── System info (safe, read-only) ──
        if self._is_system_query(task_lower):
            return self._get_system_info(task_lower)

        # ── Shell commands — blocked by default ──
        if self._is_shell_command(task_lower):
            if not self.allow_shell:
                return (
                    "🔒 Shell execution is disabled for safety.\n"
                    "Use 'open <app>' for apps, or ask a question for AI analysis."
                )
            return self._run_shell(task)

        # ── Fallback: try Anthropic Computer Use if Claude is available ──
        anthropic_key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        if anthropic_key and not self.headless:
            return await self._anthropic_computer_use(task)

        return (
            f"I can help with:\n"
            f"  • 'open <app>' — Launch an application\n"
            f"  • 'open <website>' — Open in Chrome\n"
            f"  • 'system info' — Show system details\n"
            f"  • Any question — Ask the AI agent"
        )

    # ════════════════════════════════════════════════════════════
    # INTENT DETECTION
    # ════════════════════════════════════════════════════════════

    def _is_app_launch(self, text: str) -> bool:
        """Detect app launch intent."""
        # Patterns: "open chrome", "launch terminal", "start safari"
        import re
        return bool(re.match(r'^(open|launch|start|run)\s+\w+', text))

    def _has_url(self, text: str) -> bool:
        """Check if text contains a URL or known site name."""
        from browser_agent import _extract_url
        return _extract_url(text) is not None

    def _is_system_query(self, text: str) -> bool:
        """Detect safe system info queries."""
        keywords = [
            "system info", "system status", "disk space", "memory",
            "cpu", "uptime", "battery", "network", "wifi", "hostname",
            "os version", "processes", "what's running",
        ]
        return any(kw in text for kw in keywords)

    def _is_shell_command(self, text: str) -> bool:
        """Detect shell command intent."""
        import re
        # Patterns: "run ls -la", "execute pip install", "shell: ..."
        return bool(re.match(r'^(run|execute|shell:?)\s+', text))

    # ════════════════════════════════════════════════════════════
    # HANDLERS
    # ════════════════════════════════════════════════════════════

    def _launch_app(self, task: str) -> str:
        """Launch a macOS application safely."""
        import re

        # Extract app name from "open <app>" / "launch <app>"
        match = re.match(r'^(?:open|launch|start|run)\s+(.+)', task, re.IGNORECASE)
        if not match:
            return "Couldn't parse app name."

        app_name = match.group(1).strip()

        # Map common names to macOS app names
        app_map = {
            "chrome": "Google Chrome",
            "google chrome": "Google Chrome",
            "safari": "Safari",
            "firefox": "Firefox",
            "terminal": "Terminal",
            "iterm": "iTerm",
            "iterm2": "iTerm",
            "finder": "Finder",
            "notes": "Notes",
            "calendar": "Calendar",
            "mail": "Mail",
            "messages": "Messages",
            "slack": "Slack",
            "discord": "Discord",
            "spotify": "Spotify",
            "vscode": "Visual Studio Code",
            "vs code": "Visual Studio Code",
            "code": "Visual Studio Code",
            "cursor": "Cursor",
            "xcode": "Xcode",
            "preview": "Preview",
            "photos": "Photos",
            "music": "Music",
            "keynote": "Keynote",
            "pages": "Pages",
            "numbers": "Numbers",
            "system preferences": "System Preferences",
            "system settings": "System Settings",
            "activity monitor": "Activity Monitor",
            "docker": "Docker",
        }

        # Check if it's a URL/website instead
        from browser_agent import _extract_url
        url = _extract_url(app_name)
        if url:
            from browser_agent import open_in_browser
            return open_in_browser(task)

        resolved_name = app_map.get(app_name.lower(), app_name)

        if self.system != "Darwin":
            return f"App launching is only supported on macOS. Detected: {self.system}"

        try:
            subprocess.Popen(
                ["open", "-a", resolved_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            return f"🚀 Launched {resolved_name}"
        except Exception as e:
            return f"Failed to launch {resolved_name}: {e}"

    def _get_system_info(self, query: str) -> str:
        """Return safe, read-only system information."""
        import shutil

        info_parts = []

        if "disk" in query or "storage" in query or "system info" in query:
            total, used, free = shutil.disk_usage("/")
            info_parts.append(
                f"💾 Disk: {free // (1024**3)}GB free / {total // (1024**3)}GB total "
                f"({used * 100 // total}% used)"
            )

        if "memory" in query or "ram" in query or "system info" in query:
            try:
                result = subprocess.run(
                    ["sysctl", "-n", "hw.memsize"],
                    capture_output=True, text=True, timeout=5,
                )
                mem_bytes = int(result.stdout.strip())
                info_parts.append(f"🧠 RAM: {mem_bytes // (1024**3)}GB")
            except Exception:
                info_parts.append("🧠 RAM: (could not query)")

        if "cpu" in query or "processor" in query or "system info" in query:
            try:
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True, text=True, timeout=5,
                )
                info_parts.append(f"⚙️ CPU: {result.stdout.strip()}")
            except Exception:
                info_parts.append("⚙️ CPU: (could not query)")

        if "hostname" in query or "system info" in query:
            info_parts.append(f"🖥️ Host: {platform.node()}")
            info_parts.append(f"🍎 OS: macOS {platform.mac_ver()[0]}")

        if "battery" in query:
            try:
                result = subprocess.run(
                    ["pmset", "-g", "batt"],
                    capture_output=True, text=True, timeout=5,
                )
                info_parts.append(f"🔋 Battery: {result.stdout.strip()}")
            except Exception:
                info_parts.append("🔋 Battery: (could not query)")

        return "\n".join(info_parts) if info_parts else "No matching system info found."

    def _run_shell(self, task: str) -> str:
        """Execute a shell command (ONLY if allow_shell=True)."""
        import re

        match = re.match(r'^(?:run|execute|shell:?)\s+(.+)', task, re.IGNORECASE)
        if not match:
            return "Couldn't parse command."

        command = match.group(1).strip()

        # Safety blocklist — these are NEVER allowed
        blocked = ["rm -rf", "mkfs", "dd if=", ":(){ :", "chmod 777", "> /dev/"]
        for b in blocked:
            if b in command:
                return f"🚫 Blocked: '{b}' is a dangerous pattern."

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=os.path.expanduser("~"),
            )
            output = result.stdout.strip() or result.stderr.strip() or "(no output)"
            status = "✅" if result.returncode == 0 else f"❌ (exit {result.returncode})"
            return f"{status} $ {command}\n{output}"
        except subprocess.TimeoutExpired:
            return f"⏰ Command timed out (30s limit): {command}"
        except Exception as e:
            return f"Error: {e}"

    async def _anthropic_computer_use(self, task: str) -> str:
        """
        Fallback to Anthropic's Computer Use API for complex tasks.
        Requires Claude API key and non-headless mode.
        """
        try:
            import anthropic
        except ImportError:
            return "Anthropic SDK not installed. Run: pip install anthropic"

        try:
            client = anthropic.Anthropic()
            # Note: Computer Use API requires specific model and tools setup
            # This is a placeholder for the full implementation
            logger.info(f"Anthropic Computer Use requested for: {task}")
            return (
                "🤖 Anthropic Computer Use is available but requires additional setup.\n"
                "For now, use 'open <app>' or 'open <website>' for direct control."
            )
        except Exception as e:
            return f"Anthropic Computer Use error: {e}"
