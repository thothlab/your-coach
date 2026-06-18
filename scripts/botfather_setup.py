"""One-shot BotFather configuration: commands, menu button, webhook.

Reads from environment:
    TELEGRAM_BOT_TOKEN        — required
    TELEGRAM_WEBHOOK_SECRET   — required
    PUBLIC_BASE_URL           — required, e.g. https://trainbeat.fly.dev

Idempotent — re-running yields the same final state.
"""

from __future__ import annotations

import json
import os
import sys

import httpx

COMMANDS = [
    {"command": "start", "description": "Begin onboarding"},
    {"command": "invite", "description": "Generate an invite link"},
    {"command": "app", "description": "Open the TrainBeat app"},
]


def _need(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        sys.exit(f"missing env var: {name}")
    return value


def _api(token: str, method: str, payload: dict) -> dict:
    url = f"https://api.telegram.org/bot{token}/{method}"
    response = httpx.post(url, json=payload, timeout=15)
    response.raise_for_status()
    body = response.json()
    if not body.get("ok"):
        sys.exit(f"{method} failed: {body}")
    return body


def main() -> int:
    token = _need("TELEGRAM_BOT_TOKEN")
    secret = _need("TELEGRAM_WEBHOOK_SECRET")
    base = _need("PUBLIC_BASE_URL").rstrip("/")

    print("[1/3] setMyCommands")
    _api(token, "setMyCommands", {"commands": COMMANDS})

    print("[2/3] setChatMenuButton")
    _api(
        token,
        "setChatMenuButton",
        {
            "menu_button": {
                "type": "web_app",
                "text": "Open TrainBeat",
                "web_app": {"url": f"{base}/"},
            }
        },
    )

    print("[3/3] setWebhook")
    _api(
        token,
        "setWebhook",
        {
            "url": f"{base}/api/telegram/webhook",
            "secret_token": secret,
            "drop_pending_updates": False,
            "allowed_updates": ["message", "callback_query"],
        },
    )

    info = _api(token, "getWebhookInfo", {})
    print(json.dumps(info.get("result"), indent=2, ensure_ascii=False))
    if info["result"]["url"] != f"{base}/api/telegram/webhook":
        sys.exit("getWebhookInfo URL mismatch — BotFather did not accept the URL")

    print("ok — BotFather is configured")
    return 0


if __name__ == "__main__":
    sys.exit(main())
