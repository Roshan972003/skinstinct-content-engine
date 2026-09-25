import os


def check() -> tuple[dict, int]:
    missing = [
        var
        for var in (
            "GEMINI_API_KEY",
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_WEBHOOK_SECRET",
            "TELEGRAM_CHAT_ID",
            "SUPABASE_URL",
            "SUPABASE_SERVICE_ROLE_KEY",
        )
        if not os.environ.get(var)
    ]
    if missing:
        return {"status": "misconfigured", "missing_env": missing}, 500
    return {"status": "ok"}, 200
