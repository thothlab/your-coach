import os

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token-not-real")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://trainbeat:trainbeat@localhost:5432/trainbeat",
)
os.environ.setdefault("APP_ENV", "test")
