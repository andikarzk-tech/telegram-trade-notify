
# app.py
# Minimal webhook to forward TradingView (or any JSON) alerts to a Telegram channel.
# Deploy on Render/Railway/Fly/Cloud Run/your VPS.
# Env vars required:
# - TELEGRAM_BOT_TOKEN (from @BotFather)
# - TELEGRAM_CHAT_ID (e.g., "@GOLDENPIPSID" or numeric -100...)
# - WEBHOOK_SECRET (shared secret; must match "secret" field in incoming JSON)

import os
import html
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any

import requests
from flask import Flask, request, jsonify, abort

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
SECRET = os.environ.get("WEBHOOK_SECRET", "")

assert BOT_TOKEN, "Missing TELEGRAM_BOT_TOKEN"
assert CHAT_ID, "Missing TELEGRAM_CHAT_ID"
assert SECRET, "Missing WEBHOOK_SECRET"

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

app = Flask(__name__)
app.logger.setLevel(logging.INFO)


def send_telegram_message(text: str, parse_mode: str = "HTML") -> Dict[str, Any]:
    url = f"{TELEGRAM_API}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    r = requests.post(url, json=payload, timeout=10)
    try:
        r.raise_for_status()
    except Exception as e:
        app.logger.exception("Telegram API error: %s - response=%s", e, r.text[:300])
        raise
    return r.json()


def format_signal(payload: Dict[str, Any]) -> str:
    # Quick, robust formatter. Escapes HTML.
    def esc(x):
        return html.escape(str(x)) if x is not None else "-"

    symbol = esc(payload.get("symbol") or payload.get("ticker") or payload.get("pair"))
    side = esc(payload.get("side") or payload.get("direction") or "?")
    price = esc(payload.get("price") or payload.get("entry") or payload.get("close"))
    tm = payload.get("time") or payload.get("timestamp")
    try:
        # If it's epoch ms or s, normalize to ISO UTC
        if isinstance(tm, (int, float)):
            # auto-detect ms vs s
            if tm > 1e12:
                dt = datetime.fromtimestamp(tm/1000, tz=timezone.utc)
            else:
                dt = datetime.fromtimestamp(tm, tz=timezone.utc)
            time_str = dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        elif isinstance(tm, str):
            time_str = esc(tm)
        else:
            time_str = "-"
    except Exception:
        time_str = esc(tm)

    sl = esc(payload.get("sl") or payload.get("stop") or payload.get("stop_loss"))
    tp1 = esc(payload.get("tp1") or payload.get("tp_1"))
    tp2 = esc(payload.get("tp2") or payload.get("tp_2"))
    rr = esc(payload.get("rr") or payload.get("risk_reward"))
    sess = esc(payload.get("session") or payload.get("sess"))
    fib = esc(payload.get("fib_trigger") or payload.get("fib"))
    bos = esc(payload.get("bos") or payload.get("break_of_structure"))
    fvg = esc(payload.get("fvg"))
    ob = esc(payload.get("ob") or payload.get("order_block"))
    reason = esc(payload.get("reason") or payload.get("notes") or payload.get("setup"))

    lines = []
    lines.append(f"🟢 <b>TRADING ALERT</b>")
    lines.append(f"• <b>Symbol</b>: {symbol}")
    lines.append(f"• <b>Side</b>: {side}  @ <b>{price}</b>")
    lines.append(f"• <b>Time</b>: {time_str}")
    if sl != "-" or tp1 != "-" or tp2 != "-":
        lines.append(f"• <b>SL</b>: {sl}  |  <b>TP1</b>: {tp1}  |  <b>TP2</b>: {tp2}")
    extra = []
    if rr != "-": extra.append(f"RR {rr}")
    if sess != "-": extra.append(f"Session {sess}")
    if fib != "-": extra.append(f"Fibo {fib}")
    if bos != "-": extra.append(f"BOS {bos}")
    if fvg != "-": extra.append(f"FVG {fvg}")
    if ob != "-": extra.append(f"OB {ob}")
    if extra:
        lines.append("• " + " · ".join(extra))
    if reason != "-":
        lines.append(f"• <b>Notes</b>: {reason}")
    return "\n".join(lines)


@app.get("/health")
def health():
    return jsonify(ok=True)


@app.post("/webhook")
def webhook():
    if not request.is_json:
        abort(400, description="Expecting JSON")
    data = request.get_json(force=True, silent=True) or {}
    if not data:
        abort(400, description="Empty payload")

    # Simple shared-secret auth (works with TradingView since it sends only JSON)
    if str(data.get("secret", "")) != SECRET:
        abort(401, description="Bad secret")

    # Optionally, collapse noisy duplicate alerts (idempotency key)
    # You can pass "uuid" or "id" from the source to dedupe; skipping persistence for simplicity.

    try:
        text = format_signal(data)
        resp = send_telegram_message(text)
    except Exception as e:
        app.logger.exception("Failed to send alert: %s", e)
        abort(500, description="Telegram send failed")

    return jsonify(ok=True, telegram=resp)
    

if __name__ == "__main__":
    # For local run: python app.py
    # Then expose with ngrok or run behind a reverse proxy in prod.
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
