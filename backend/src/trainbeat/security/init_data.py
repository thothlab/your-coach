import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from urllib.parse import parse_qsl


@dataclass(frozen=True)
class InitDataUser:
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None

    @property
    def display_name(self) -> str:
        if self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.first_name


@dataclass(frozen=True)
class InitData:
    user: InitDataUser
    auth_date: int
    start_param: str | None = None


class InitDataError(ValueError):
    pass


def parse_and_validate(
    raw: str, *, bot_token: str, max_age_seconds: int = 86400, now: int | None = None
) -> InitData:
    """Parse and HMAC-validate a Telegram WebApp initData payload.

    Reference: https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    if not raw:
        raise InitDataError("empty init_data")

    pairs = dict(parse_qsl(raw, keep_blank_values=True))
    received_hash = pairs.pop("hash", None)
    if not received_hash:
        raise InitDataError("missing hash")

    data_check_string = "\n".join(f"{key}={pairs[key]}" for key in sorted(pairs))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    expected = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, received_hash):
        raise InitDataError("hash mismatch")

    try:
        auth_date = int(pairs["auth_date"])
    except (KeyError, ValueError) as exc:
        raise InitDataError("invalid auth_date") from exc

    current_time = now if now is not None else int(time.time())
    if current_time - auth_date > max_age_seconds:
        raise InitDataError("init_data is stale")
    if auth_date - current_time > 60:
        raise InitDataError("init_data auth_date is in the future")

    if "user" not in pairs:
        raise InitDataError("missing user payload")
    try:
        user_payload = json.loads(pairs["user"])
    except json.JSONDecodeError as exc:
        raise InitDataError("user payload is not valid JSON") from exc

    try:
        user = InitDataUser(
            id=int(user_payload["id"]),
            first_name=str(user_payload.get("first_name", "")),
            last_name=user_payload.get("last_name"),
            username=user_payload.get("username"),
        )
    except (KeyError, ValueError, TypeError) as exc:
        raise InitDataError("user payload missing required fields") from exc

    return InitData(
        user=user,
        auth_date=auth_date,
        start_param=pairs.get("start_param"),
    )


def build_init_data(
    *, bot_token: str, user: dict, auth_date: int, start_param: str | None = None
) -> str:
    """Generate a valid initData string. Used by tests and tooling — never in production."""
    from urllib.parse import urlencode

    pairs: dict[str, str] = {
        "user": json.dumps(user, separators=(",", ":")),
        "auth_date": str(auth_date),
    }
    if start_param is not None:
        pairs["start_param"] = start_param
    data_check_string = "\n".join(f"{key}={pairs[key]}" for key in sorted(pairs))
    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    pairs["hash"] = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return urlencode(pairs)
