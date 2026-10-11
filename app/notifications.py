from __future__ import annotations

import os
import requests


class TelegramNotifier:
    def __init__(self) -> None:
        self.token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    @property
    def enabled(self) -> bool:
        return bool(self.token and self.chat_id)

    def send(self, message: str) -> None:
        if not self.enabled:
            return
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        try:
            requests.post(
                url,
                json={"chat_id": self.chat_id, "text": message},
                timeout=10,
            ).raise_for_status()
        except Exception:
            # Notifications must never crash the risk engine.
            pass
