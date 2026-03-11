"""
Telegram Client — User-level Telegram integration via Telethon.

Unlike the Bot API (telegram_bot.py), this connects as YOUR Telegram account,
allowing you to:
  • Read messages from channels you're subscribed to
  • Send messages to any chat, group, or bot (e.g. PepeBoost)
  • Monitor trading bot channels for signals
  • Forward messages between chats
  • Search message history

Auth requires: api_id + api_hash from my.telegram.org + phone number (one-time).
Session is persisted so you only need to authenticate once.
"""

import os
import asyncio
import threading
import logging
from datetime import datetime
from typing import Callable, Optional

logger = logging.getLogger("telegram.client")

try:
    from telethon import TelegramClient as TelethonClient
    from telethon import events
    from telethon.tl.types import Channel, Chat, User
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    logger.warning("telethon not installed — run: uv pip install telethon")


class TelegramUserClient:
    """
    Telegram Client API wrapper — connects as your account.

    Usage:
        client = TelegramUserClient(api_id, api_hash)
        await client.start(phone="+1234567890")
        messages = await client.read_channel("pepeboost_channel")
        await client.send_message("@pepeboost_bot", "/buy ETH 0.1")
    """

    def __init__(
        self,
        api_id: int | None = None,
        api_hash: str | None = None,
        session_name: str = "sentinel_session",
        agent_chat_fn: Callable | None = None,
    ):
        self.api_id = api_id or int(os.getenv("TELEGRAM_API_ID", "0"))
        self.api_hash = api_hash or os.getenv("TELEGRAM_API_HASH", "")
        self.session_name = session_name
        self.agent_chat = agent_chat_fn
        self.client: Optional[TelethonClient] = None
        self._running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._monitored_chats: list[str] = []

    @property
    def is_connected(self) -> bool:
        return self.client is not None and self.client.is_connected()

    # ── Connection ───────────────────────────────────────────────────

    async def connect(self, phone: str | None = None):
        """Connect to Telegram. First time requires phone + verification code."""
        if not TELETHON_AVAILABLE:
            raise ImportError("telethon not installed — run: uv pip install telethon")

        if not self.api_id or not self.api_hash:
            raise ValueError(
                "TELEGRAM_API_ID and TELEGRAM_API_HASH required.\n"
                "Get them at https://my.telegram.org → API Development Tools"
            )

        self.client = TelethonClient(self.session_name, self.api_id, self.api_hash)
        await self.client.start(phone=phone)
        me = await self.client.get_me()
        logger.info(f"Connected as: {me.first_name} (@{me.username})")
        return me

    async def disconnect(self):
        """Disconnect from Telegram."""
        if self.client:
            await self.client.disconnect()
            logger.info("Telegram client disconnected")

    # ── Reading ──────────────────────────────────────────────────────

    async def read_channel(self, channel: str, limit: int = 10) -> list[dict]:
        """
        Read recent messages from a channel, group, or DM.

        Args:
            channel: Username (@channel), invite link, or chat ID
            limit: Number of messages to fetch (default 10)

        Returns:
            List of message dicts with sender, text, date
        """
        if not self.client:
            raise RuntimeError("Client not connected")

        messages = []
        async for msg in self.client.iter_messages(channel, limit=limit):
            messages.append({
                "id": msg.id,
                "sender": getattr(msg.sender, "username", None) or str(msg.sender_id),
                "text": msg.text or "[media]",
                "date": msg.date.isoformat() if msg.date else None,
                "reply_to": msg.reply_to_msg_id,
            })

        return messages

    async def search_messages(
        self, channel: str, query: str, limit: int = 20
    ) -> list[dict]:
        """Search for messages containing a query string."""
        if not self.client:
            raise RuntimeError("Client not connected")

        results = []
        async for msg in self.client.iter_messages(channel, search=query, limit=limit):
            results.append({
                "id": msg.id,
                "sender": getattr(msg.sender, "username", None) or str(msg.sender_id),
                "text": msg.text or "[media]",
                "date": msg.date.isoformat() if msg.date else None,
            })

        return results

    # ── Sending ──────────────────────────────────────────────────────

    async def send_message(self, target: str, message: str) -> dict:
        """
        Send a message to a user, group, channel, or bot.

        Args:
            target: Username (@user), phone number, or chat ID
            message: Text to send

        Returns:
            Sent message info
        """
        if not self.client:
            raise RuntimeError("Client not connected")

        sent = await self.client.send_message(target, message)
        logger.info(f"Sent to {target}: {message[:50]}...")
        return {
            "id": sent.id,
            "target": target,
            "text": message,
            "date": sent.date.isoformat() if sent.date else None,
        }

    async def reply_to(self, channel: str, message_id: int, text: str) -> dict:
        """Reply to a specific message."""
        if not self.client:
            raise RuntimeError("Client not connected")

        sent = await self.client.send_message(
            channel, text, reply_to=message_id
        )
        return {
            "id": sent.id,
            "reply_to": message_id,
            "text": text,
        }

    # ── Monitoring ───────────────────────────────────────────────────

    async def monitor_chat(self, channel: str, callback: Callable | None = None):
        """
        Monitor a chat for new messages in real-time.
        Messages are passed to the callback function or logged.
        """
        if not self.client:
            raise RuntimeError("Client not connected")

        entity = await self.client.get_entity(channel)
        self._monitored_chats.append(channel)

        @self.client.on(events.NewMessage(chats=entity))
        async def handler(event):
            sender = await event.get_sender()
            sender_name = getattr(sender, "username", None) or str(sender.id)
            msg_text = event.text or "[media]"

            logger.info(f"[{channel}] {sender_name}: {msg_text[:100]}")

            if callback:
                callback({
                    "channel": channel,
                    "sender": sender_name,
                    "text": msg_text,
                    "date": event.date.isoformat(),
                    "message_id": event.id,
                })

        logger.info(f"Monitoring {channel} for new messages")

    # ── Chat Listing ─────────────────────────────────────────────────

    async def list_dialogs(self, limit: int = 30) -> list[dict]:
        """List your recent chats/channels/groups."""
        if not self.client:
            raise RuntimeError("Client not connected")

        dialogs = []
        async for dialog in self.client.iter_dialogs(limit=limit):
            dtype = "channel" if isinstance(dialog.entity, Channel) else \
                    "group" if isinstance(dialog.entity, Chat) else "user"
            dialogs.append({
                "name": dialog.name,
                "id": dialog.id,
                "type": dtype,
                "unread": dialog.unread_count,
                "username": getattr(dialog.entity, "username", None),
            })

        return dialogs

    # ── Background Thread Runner ─────────────────────────────────────

    def start_background(self, phone: str | None = None):
        """Start the client in a background thread (for use alongside the REPL)."""
        def _run():
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self._async_background(phone))

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        self._running = True
        logger.info("Telegram client started in background thread")

    async def _async_background(self, phone: str | None = None):
        """Async background runner."""
        await self.connect(phone)
        logger.info("Telegram client running in background")
        # Keep running until stopped
        await self.client.run_until_disconnected()

    def run_async(self, coro):
        """Run an async coroutine from sync code using the background loop."""
        if self._loop and self._loop.is_running():
            future = asyncio.run_coroutine_threadsafe(coro, self._loop)
            return future.result(timeout=30)
        else:
            return asyncio.run(coro)

    # ── Convenience Sync Wrappers ────────────────────────────────────

    def read_channel_sync(self, channel: str, limit: int = 10) -> list[dict]:
        """Sync wrapper for read_channel."""
        return self.run_async(self.read_channel(channel, limit))

    def send_message_sync(self, target: str, message: str) -> dict:
        """Sync wrapper for send_message."""
        return self.run_async(self.send_message(target, message))

    def list_dialogs_sync(self, limit: int = 30) -> list[dict]:
        """Sync wrapper for list_dialogs."""
        return self.run_async(self.list_dialogs(limit))
