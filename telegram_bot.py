import sys
import logging
import requests
from datetime import datetime, timezone, timedelta

# Force UTF-8 encoding for standard output
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

DEFAULT_TELEGRAM_TOKEN = "8935294463:AAFYtP6V2ASWaB9Dc7u9Ql2l8NIOnCp4jvQ"
DEFAULT_CHAT_ID = "5226929253"

# Vietnam Timezone GMT+7
TZ_VIETNAM = timezone(timedelta(hours=7))

def get_vn_time_str() -> str:
    return datetime.now(TZ_VIETNAM).strftime("%d/%m/%Y %H:%M:%S")

class TelegramNotifier:
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or DEFAULT_TELEGRAM_TOKEN
        self.chat_id = chat_id or DEFAULT_CHAT_ID

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """Send message via Telegram Bot API."""
        if not self.bot_token or not self.chat_id:
            logging.warning("Telegram Bot Token or Chat ID missing. Skipping message send.")
            try:
                print(f"\n--- [TELEGRAM SIMULATED OUTPUT] ---\n{text}\n-----------------------------------\n")
            except UnicodeEncodeError:
                print(f"\n--- [TELEGRAM SIMULATED OUTPUT] ---\n{text.encode('utf-8', errors='ignore').decode('utf-8')}\n-----------------------------------\n")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": False,
        }

        try:
            res = requests.post(url, json=payload, timeout=12)
            if res.status_code == 200:
                logging.info(f"Telegram notification sent successfully to Chat ID: {self.chat_id}")
                return True
            else:
                logging.error(f"Telegram API Error {res.status_code}: {res.text}")
                return False
        except Exception as e:
            logging.error(f"Failed to send Telegram message: {e}")
            return False

    def send_price_drop_alerts(self, items: list) -> bool:
        """
        Format and send price notification ONLY for successfully scraped items with current_price > 0.
        Never sends 'Lỗi kết nối' or 'N/A' items to Telegram.
        """
        # Filter strictly valid items
        valid_items = [
            item for item in items
            if isinstance(item, dict) and item.get("success") and item.get("current_price", 0) > 0
        ]

        if not valid_items:
            logging.warning("No valid product price data to send. Skipping Telegram alert to avoid sending error messages.")
            return True

        now_str = get_vn_time_str()
        msg = f"📊 <b>BÁO CÁO GIÁ ĐIỆN MÁY XANH</b> 📊\n"
        msg += f"📅 <i>Thời gian (GMT+7): {now_str}</i>\n"
        msg += f"-----------------------------------\n\n"

        for item in valid_items:
            title = item.get("title", item.get("name", "Sản phẩm"))
            curr_price = item.get("current_price", 0)
            prev_price = item.get("previous_price", 0)
            url = item.get("url", "#")
            disc_rate_vs_prev = item.get("discount_rate_vs_prev", 0)

            curr_formatted = f"{curr_price:,}đ".replace(",", ".")
            
            # Format Previous Price (from previous run)
            if prev_price > 0:
                prev_formatted = f"{prev_price:,}đ".replace(",", ".")
            else:
                prev_formatted = "Chưa có (Lần đầu quét)"

            msg += f"🔹 <b>{title}</b>\n"
            
            if prev_price > 0 and curr_price < prev_price:
                msg += f"🔻 <b>Giá cũ (lần quét trước):</b> <s>{prev_formatted}</s>\n"
                msg += f"🔥 <b>Giá mới:</b> <b>{curr_formatted}</b> (-{disc_rate_vs_prev}%)\n"
            elif prev_price > 0 and curr_price > prev_price:
                msg += f"🔺 <b>Giá cũ (lần quét trước):</b> <s>{prev_formatted}</s>\n"
                msg += f"📈 <b>Giá mới:</b> <b>{curr_formatted}</b> (Tăng giá)\n"
            elif prev_price > 0:
                msg += f"🔹 <b>Giá cũ (lần quét trước):</b> {prev_formatted}\n"
                msg += f"💵 <b>Giá mới:</b> <b>{curr_formatted}</b> (Không đổi)\n"
            else:
                msg += f"🔹 <b>Giá cũ (lần quét trước):</b> <i>Lần đầu quét</i>\n"
                msg += f"💵 <b>Giá mới (hiện tại):</b> <b>{curr_formatted}</b>\n"

            msg += f"🔗 <a href='{url}'>Xem chi tiết sản phẩm</a>\n\n"

        msg += f"-----------------------------------\n"
        msg += f"🤖 <i>Tự động cập nhật GMT+7 từ Antigravity Price Tracker</i>"

        return self.send_message(msg)

if __name__ == "__main__":
    test_notifier = TelegramNotifier()
    sample_data = [
        {
            "title": "Máy lọc không khí LG PuriCare 360 Hit AS60GHWG0 41W",
            "current_price": 5390000,
            "previous_price": 5390000,
            "discount_rate_vs_prev": 0.0,
            "success": True,
            "url": "https://www.dienmayxanh.com/may-loc-khong-khi/may-loc-khong-khi-lg-puricare-360-hit-as60ghwg0-41w",
        }
    ]
    test_notifier.send_price_drop_alerts(sample_data)
