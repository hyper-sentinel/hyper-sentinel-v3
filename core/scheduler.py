"""
Sentinel Scheduler — Cron-style job runner for autonomous operations.

Runs monitor checks, briefings, and mission actions on configurable schedules.
Uses Python's `schedule` library for lightweight cron-style execution.
"""

import os
import time
import threading
import logging
from datetime import datetime
from typing import Callable

try:
    import schedule
except ImportError:
    # Fallback: minimal scheduler using time.sleep loops
    schedule = None

logger = logging.getLogger("sentinel.scheduler")


class SentinelScheduler:
    """Runs scheduled jobs in a background thread."""

    def __init__(self):
        self.jobs: list[dict] = []
        self._running = False
        self._thread: threading.Thread | None = None

    def every(self, interval_minutes: int, job_fn: Callable, name: str = ""):
        """Schedule a job to run every N minutes."""
        job_info = {
            "name": name or job_fn.__name__,
            "interval": interval_minutes,
            "fn": job_fn,
            "last_run": None,
            "run_count": 0,
        }
        self.jobs.append(job_info)

        if schedule:
            schedule.every(interval_minutes).minutes.do(
                self._run_job, job_info
            )
        logger.info(f"Scheduled '{job_info['name']}' every {interval_minutes}m")

    def cron(self, time_str: str, job_fn: Callable, name: str = ""):
        """Schedule a job at a specific time daily (HH:MM format)."""
        job_info = {
            "name": name or job_fn.__name__,
            "cron": time_str,
            "fn": job_fn,
            "last_run": None,
            "run_count": 0,
        }
        self.jobs.append(job_info)

        if schedule:
            schedule.every().day.at(time_str).do(
                self._run_job, job_info
            )
        logger.info(f"Scheduled '{job_info['name']}' daily at {time_str}")

    def _run_job(self, job_info: dict):
        """Execute a job with error handling."""
        name = job_info["name"]
        try:
            logger.info(f"Running job: {name}")
            job_info["fn"]()
            job_info["last_run"] = datetime.now().isoformat()
            job_info["run_count"] += 1
            logger.info(f"Job '{name}' completed (run #{job_info['run_count']})")
        except Exception as e:
            logger.error(f"Job '{name}' failed: {e}")

    def _loop(self):
        """Main scheduler loop — runs in background thread."""
        logger.info("Scheduler loop started")
        while self._running:
            if schedule:
                schedule.run_pending()
            else:
                # Fallback: manual time-based check
                now = time.time()
                for job in self.jobs:
                    interval = job.get("interval")
                    if interval:
                        last = job.get("_last_ts", 0)
                        if now - last >= interval * 60:
                            job["_last_ts"] = now
                            self._run_job(job)
            time.sleep(10)  # Check every 10 seconds

    def start(self):
        """Start the scheduler in a background thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info("Sentinel scheduler started")

    def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Sentinel scheduler stopped")

    def get_status(self) -> list[dict]:
        """Return status of all scheduled jobs."""
        return [
            {
                "name": j["name"],
                "interval": j.get("interval", j.get("cron", "?")),
                "last_run": j["last_run"],
                "run_count": j["run_count"],
            }
            for j in self.jobs
        ]
