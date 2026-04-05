from flask import Flask, request, jsonify
import requests
import os
import json
from datetime import datetime

app = Flask(__name__)

# === KONFIGURASI — ISI SESUAI PUNYA KAMU ===
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "ISI_TOKEN_TELEGRAM_KAMU")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "ISI_CHAT_ID_KAMU")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "ISI_API_KEY_CLAUDE_KAMU")

def send_telegram(message):
    """Kirim pesan ke Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

def ask_claude(market_data):
    """Kirim data market ke Claude untuk analisa"""
    prompt = f"""Kamu adalah analis trading profesional. Analisa data market berikut dan berikan rekomendasi trading yang jelas.

DATA MARKET:
- Symbol: {market_data.get('symbol', 'N/A')}
- Timeframe: {market_data.get('timeframe', 'N/A')}
- Harga Open: {market_data.get('open', 'N/A')}
- Harga High: {market_data.get('high', 'N/A')}
- Harga Low: {market_data.get('low', 'N/A')}
- Harga Close/Current: {market_data.get('close', 'N/A')}
- Volume: {market_data.get('volume', 'N/A')}
- AC (Accelerator Oscillator): {market_data.get('ac', 'N/A')}
- ADX: {market_data.get('adx', 'N/A')}
- RSI: {market_data.get('rsi', 'N/A')}
- EMA Fast: {market_data.get('ema_fast', 'N/A')}
- EMA Slow: {market_data.get('ema_slow', 'N/A')}
- Waktu: {market_data.get('time', 'N/A')}

Berikan analisa singkat dan rekomendasi:
1. SINYAL: BUY / SELL / HOLD
2. ALASAN: (max 2 kalimat)
3. ENTRY: harga entry yang disarankan
4. STOP LOSS: level SL yang disarankan
5. TAKE PROFIT: level TP yang disarankan
6. CONFIDENCE: LOW / MEDIUM / HIGH

Format output harus ringkas dan jelas."""

    headers = {
        "x-api-key": ANTHROPIC_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": 500,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=30
        )
        data = response.json()
        return data["content"][0]["text"]
    except Exception as e:
        return f"Error analisa Claude: {e}"

@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Fikri Trading Signal Server is running! 🚀"})

@app.route("/signal", methods=["POST"])
def receive_signal():
    """Endpoint utama — terima data dari MT5 EA"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data received"}), 400
        
        print(f"[{datetime.now()}] Data diterima: {json.dumps(data, indent=2)}")
        
        # Kirim ke Claude untuk analisa
        analysis = ask_claude(data)
        
        # Format pesan Telegram
        symbol = data.get('symbol', 'N/A')
        timeframe = data.get('timeframe', 'N/A')
        close_price = data.get('close', 'N/A')
        time_str = data.get('time', datetime.now().strftime('%Y-%m-%d %H:%M'))
        
        telegram_msg = f"""🤖 <b>FIKRI TRADING SIGNAL</b>
━━━━━━━━━━━━━━━━
📊 <b>{symbol}</b> | {timeframe}
💰 Harga: {close_price}
🕐 Waktu: {time_str}
━━━━━━━━━━━━━━━━
<b>ANALISA CLAUDE AI:</b>

{analysis}
━━━━━━━━━━━━━━━━
⚠️ <i>Bukan financial advice. DYOR!</i>"""
        
        send_telegram(telegram_msg)
        
        return jsonify({
            "status": "success",
            "analysis": analysis
        })
        
    except Exception as e:
        error_msg = f"Server error: {e}"
        print(error_msg)
        return jsonify({"error": error_msg}), 500

@app.route("/test", methods=["GET"])
def test():
    """Test endpoint — cek apakah Telegram berjalan"""
    send_telegram("✅ Server Fikri Trading Signal aktif dan siap menerima sinyal dari MT5!")
    return jsonify({"status": "Test message sent to Telegram!"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
