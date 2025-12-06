import requests
from datetime import datetime
import json
import os

# ========== 配置 ==========
ASSETS = {
    "BVIV7D": {"name": "BTC", "threshold": 40},
    "EVIV7D": {"name": "ETH", "threshold": 65},
    "SVIV7D": {"name": "SOL", "threshold": 70},
}

VOLMEX_URL = "https://rest-v1.volmex.finance/public/iv/history"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

STATE_FILE = "iv_status.json"


def load_status():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {symbol: False for symbol in ASSETS}


def save_status(status):
    with open(STATE_FILE, "w") as f:
        json.dump(status, f)


def telegram_push(msg: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Telegram 未配置")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})


def fetch_iv(symbol):
    now = int(datetime.utcnow().timestamp())
    from_time = now - 7 * 24 * 3600

    params = {
        "symbol": symbol,
        "resolution": "D",
        "from": from_time,
        "to": now,
    }

    resp = requests.get(VOLMEX_URL, params=params, timeout=10).json()

    if resp.get("s") != "ok":
        print(f"⚠️ API 错误：{symbol} → {resp}")
        return None

    iv = resp["c"][-1]
    print(f"{datetime.now()} | {symbol} 最新IV: {iv:.2f}")
    return iv


def main():
    status = load_status()

    for symbol, cfg in ASSETS.items():
        name = cfg["name"]
        threshold = cfg["threshold"]

        iv = fetch_iv(symbol)
        if iv is None:
            continue

        if iv < threshold:
            if not status[symbol]:
                msg = f"⚠️ {name} 7D 隐含波动率 {iv:.2f}，低于 {threshold}（阈值）"
                telegram_push(msg)
                print("📨 已推送 Telegram")
                status[symbol] = True
            else:
                print(f"⚠️ {name} 仍低于阈值，但已推送过。")
        else:
            print(f"✅ {name} 正常 IV: {iv:.2f}")
            if status[symbol]:
                status[symbol] = False

    save_status(status)


if __name__ == "__main__":
    main()
