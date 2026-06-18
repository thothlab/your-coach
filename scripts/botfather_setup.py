"""One-shot BotFather configuration: commands, menu button (default).

Reads from environment:
    TELEGRAM_BOT_TOKEN        — required
    PUBLIC_BASE_URL           — required, e.g. https://trainbeat.devipad.ru

Optional webhook setup (only when BOT_MODE=webhook in production):
    SETUP_WEBHOOK=1           — enables setWebhook call
    TELEGRAM_WEBHOOK_SECRET   — required when SETUP_WEBHOOK=1

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
    base = _need("PUBLIC_BASE_URL").rstrip("/")
    setup_webhook = os.environ.get("SETUP_WEBHOOK", "").strip() == "1"

    print("[1/2] setMyCommands")
    _api(token, "setMyCommands", {"commands": COMMANDS})

    print("[2/2] setChatMenuButton")
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

    if setup_webhook:
        secret = _need("TELEGRAM_WEBHOOK_SECRET")
        print("[opt] setWebhook (SETUP_WEBHOOK=1)")
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
    else:
        info = _api(token, "getWebhookInfo", {})
        current = info["result"].get("url", "")
        if current:
            print(
                f"[info] webhook is set to {current}; "
                "polling-mode bots should not have a webhook — call deleteWebhook to clear"
            )

    print("ok — BotFather is configured")
    return 0


if __name__ == "__main__":
    sys.exit(main())
