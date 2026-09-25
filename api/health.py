from http.server import BaseHTTPRequestHandler
import json
import os


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
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
        body = json.dumps({"status": "ok" if not missing else "misconfigured", "missing_env": missing}).encode()
        self.send_response(200 if not missing else 500)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)
