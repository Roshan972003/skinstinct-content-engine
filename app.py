"""
Vercel entrypoint. The current Vercel Python runtime routes every request to
a single WSGI/ASGI `app` object rather than treating each api/*.py file as
its own function — see webhook_logic.py and health_logic.py for the actual
route handlers; this file only wires them to their URL paths.
"""
from flask import Flask, jsonify, request

import health_logic
import webhook_logic

app = Flask(__name__)


@app.route("/api/health", methods=["GET"])
def health():
    body, status = health_logic.check()
    return jsonify(body), status


@app.route("/api/webhook", methods=["POST"])
def webhook():
    body, status = webhook_logic.handle(
        headers=request.headers,
        raw_body=request.get_data(),
    )
    return jsonify(body), status
