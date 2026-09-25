import os


def check() -> tuple[dict, int]:
    missing = [
        var
        for var in (
            "GEMINI_API_KEY",
            "TELEGRAM_BOT_TOKEN",
            "TELEGRAM_WEBHOOK_SECRET",
            "TELEGRAM_CHAT_ID",
            "TELEGRAM_PUBLISHED_CHAT_ID",
            "SUPABASE_URL",
            "SUPABASE_SERVICE_ROLE_KEY",
            "GITHUB_TOKEN",
            "GITHUB_OWNER",
            "GITHUB_ARCHIVE_REPO",
        )
        if not os.environ.get(var)
    ]
    if missing:
        return {"status": "misconfigured", "missing_env": missing}, 500
    return {"status": "ok"}, 200
