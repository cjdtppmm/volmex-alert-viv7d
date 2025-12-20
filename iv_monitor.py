import requests
from datetime import datetime
import os
import json

# ===== 推送配置（GitHub Secrets）=====
PUSHDEER_KEY = os.getenv("PUSHDEER_KEY")
TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TG_CHAT_ID")

if not all([PUSHDEER_KEY, TG_BOT_TOKEN, TG_CHAT_ID]):
    raise RuntimeError("❌ 推送密钥未配置")

# ===== Volmex API =====
API_URL = "https://rest-v1.volmex.finance/public/iv/history"

ASSETS = {
    "BVIV": 43,  # BTC
    "EVIV": 65,  # ETH
    "SVIV7D": 70,  # SOL
}

STATUS_FILE = "iv_status.json"


# ===== 推送函数 =====
def push_pushdeer(text):
    r = requests.get(
        "https://api2.pushdeer.com/message/push",
        params={"pushkey": PUSHDEER_KEY, "text": text},
        timeout=5,
    )
    print("PushDeer:", r.text)


def push_telegram(text):
    r = requests.post(
        f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
        data={"chat_id": TG_CHAT_ID, "text": text},
        timeout=5,
    )
    print("Telegram:", r.text)


# ===== 状态读写 =====
def load_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_status(status):
    with open(STATUS_FILE, "w") as f:
        json.dump(status, f)


# ===== 核心逻辑 =====
def check_iv(symbol, threshold, status):
    now = int(datetime.utcnow().timestamp())

    params = {
        "symbol": symbol,
        "resolution": "D",
        "from": now - 7 * 24 * 3600,
        "to": now,
    }

    res = requests.get(API_URL, params=params, timeout=10).json()
    if res.get("s") != "ok":
        print(f"{symbol} API 错误:", res)
        return

    iv = res["c"][-1]
    print(f"{symbol} 当前 IV: {iv:.2f}")

    alerted = status.get(symbol, False)

    if iv < threshold and not alerted:
        msg = f"⚠️ {symbol} IV {iv:.2f} < 阈值 {threshold}"
        push_pushdeer(msg)
        push_telegram(msg)
        status[symbol] = True

    elif iv >= threshold and alerted:
        msg = f"✅ {symbol} IV {iv:.2f} 已回到阈值之上"
        push_pushdeer(msg)
        push_telegram(msg)
        status[symbol] = False


def main():
    status = load_status()
    for symbol, threshold in ASSETS.items():
        check_iv(symbol, threshold, status)
    save_status(status)


if __name__ == "__main__":
    main()
