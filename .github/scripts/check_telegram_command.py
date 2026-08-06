"""
check_telegram_command.py
─────────────────────────
Chạy trong GitHub Actions mỗi 5 phút.
- Gọi Telegram getUpdates để tìm tin nhắn "Quét" mới trong vòng 6 phút gần nhất.
- Nếu tìm thấy → gửi xác nhận về Telegram + trigger workflow_dispatch scraper.
- Nếu không → thoát im lặng.
"""

import os
import sys
import time
import requests

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")
GITHUB_TOKEN       = os.environ.get("GITHUB_TOKEN", "")
GITHUB_REPOSITORY  = os.environ.get("GITHUB_REPOSITORY", "")   # e.g. "ngtndat/dmx_price_tracker"
WORKFLOW_FILE      = "lg_price_scraper.yml"                     # file workflow cần trigger
BRANCH             = "main"

TRIGGER_KEYWORDS = {"quét", "quet", "scan", "/quét", "/quet", "/scan"}
# Chỉ xét tin nhắn trong vòng 6 phút gần nhất (360s) để tránh re-trigger tin cũ
MAX_AGE_SECONDS = 360


def send_telegram(text: str):
    """Gửi tin nhắn xác nhận về Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10,
        )
    except Exception as e:
        print(f"[!] Không gửi được Telegram: {e}")


def trigger_workflow():
    """Kích hoạt scraper workflow qua GitHub API."""
    if not GITHUB_TOKEN or not GITHUB_REPOSITORY:
        print("[!] Thiếu GITHUB_TOKEN hoặc GITHUB_REPOSITORY. Không thể trigger workflow.")
        return False

    url = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/actions/workflows/{WORKFLOW_FILE}/dispatches"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    payload = {"ref": BRANCH}

    resp = requests.post(url, headers=headers, json=payload, timeout=15)
    if resp.status_code == 204:
        print("[OK] Đã trigger workflow thành công!")
        return True
    else:
        print(f"[!] Trigger workflow lỗi {resp.status_code}: {resp.text}")
        return False


def check_for_command():
    """Kiểm tra Telegram có lệnh 'Quét' mới không."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[!] Thiếu TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID.")
        sys.exit(0)

    allowed_chat_id = str(TELEGRAM_CHAT_ID)
    now_ts = int(time.time())
    cutoff_ts = now_ts - MAX_AGE_SECONDS

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
    params = {
        "allowed_updates": ["message"],
        "offset": -100,   # Lấy 100 update gần nhất (đủ để bắt được tin 5p trước)
        "limit": 100,
    }

    try:
        resp = requests.get(url, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"[!] Lỗi gọi Telegram API: {e}")
        sys.exit(0)

    found = False
    for update in data.get("result", []):
        msg = update.get("message", {})
        if not msg:
            continue

        chat_id = str(msg.get("chat", {}).get("id", ""))
        msg_ts  = msg.get("date", 0)
        text    = msg.get("text", "").strip().lower()

        # Chỉ xét tin từ đúng chat và trong vòng 6 phút
        if chat_id != allowed_chat_id:
            continue
        if msg_ts < cutoff_ts:
            continue
        if text in TRIGGER_KEYWORDS:
            print(f"[Telegram] Phát hiện lệnh '{text}' (ts={msg_ts}). Đang kích hoạt quét...")
            found = True
            break

    return found


def main():
    if check_for_command():
        # 1. Gửi xác nhận ngay lập tức
        send_telegram(
            "⚡ <b>Đã nhận lệnh Quét!</b>\n"
            "🔄 Đang kích hoạt quét giá trên GitHub Actions...\n"
            "<i>(Kết quả sẽ được gửi lại sau khi quét xong ~10-15 phút)</i>"
        )
        # 2. Trigger workflow
        ok = trigger_workflow()
        if not ok:
            send_telegram("❌ <b>Lỗi:</b> Không thể kích hoạt workflow. Hãy kiểm tra GitHub Actions.")
        sys.exit(0)
    else:
        print("[OK] Không có lệnh Quét mới. Kết thúc.")
        sys.exit(0)


if __name__ == "__main__":
    main()
