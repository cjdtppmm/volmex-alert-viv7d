import requests
from datetime import datetime
import time

# ===== 推送配置 =====
PUSHDEER_KEY = "YOUR_PUSHDEER_KEY"

TG_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"
TG_CHAT_ID = "YOUR_TELEGRAM_CHAT_ID"

# ===== Volmex API =====
API_URL = "https://rest-v1.volmex.finance/public/iv/history"

ASSETS = [
    ("BVIV", 50),  # BTC
    ("EVIV", 65),  # ETH
    ("SVIV7D", 75),  # SOL
]

def push_pushdeer(text):
    try:
        url = f"https://api2.pushdeer.com/message/push?pushkey={PUSHDEER_KEY}&text={text}"
        requests.get(url, timeout=5)
    except:
        pass

def push_telegram(text):
    try:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        params = {"chat_id": TG_CHAT_ID, "text": text}
        requests.get(url, params=params, timeout=5)
    except:
        pass

def check_iv(symbol, threshold):
    now = int(datetime.utcnow().timestamp())
    days_ago_7 = now - 7 * 24 * 3600

    params = {
        "symbol": symbol,
        "resolution": "D",
        "from": days_ago_7,
        "to": now
    }

    res = requests.get(API_URL, params=params, timeout=10).json()

    if res.get("s") != "ok":
        print(f"API 返回错误: {res}")
        return

    iv = res["c"][-1]
    date = datetime.utcfromtimestamp(res["t"][-1]).strftime("%Y-%m-%d")

    print(f"{date} {symbol} 最新 IV: {iv:.2f}")

    if iv < threshold:
        alert = f"⚠️ {symbol} 隐含波动率 {iv:.2f} < 阈值 {threshold}"
        push_pushdeer(alert)
        push_telegram(alert)
        print("📲 已推送通知")

def main():
    for symbol, threshold in ASSETS:
        check_iv(symbol, threshold)

if __name__ == "__main__":
    main()
