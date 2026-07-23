import sys
import logging
import requests
from datetime import datetime

# Configure stdout encoding for Windows compatibility
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

DEFAULT_TELEGRAM_TOKEN = "8935294463:AAFYtP6V2ASWaB9Dc7u9Ql2l8NIOnCp4jvQ"
DEFAULT_CHAT_ID = "5226929253"

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
            res = requests.post(url, json=payload, timeout=10)
            if res.status_code == 200:
                logging.info(f"Telegram notification sent successfully to Chat ID: {self.chat_id}")
                return True
            else:
                logging.error(f"Telegram API Error {res.status_code}: {res.text}")
                return False
        except Exception as e:
            logging.error(f"Failed to send Telegram message: {e}")
            return False

    def send_price_drop_alerts(self, discounted_items: list) -> bool:
        """Format and send a list of price drop alerts to Telegram."""
        if not discounted_items:
            logging.info("No price drops detected. No Telegram message sent.")
            return True

        now_str = datetime.now().strftime("%d/%m/%Y %H:%M")
        msg = f"🚨 <b>CẢNH BÁO GIẢM GIÁ ĐIỆN MÁY XANH</b> 🚨\n"
        msg += f"📅 <i>Thời gian: {now_str}</i>\n"
        msg += f"-----------------------------------\n\n"

        for item in discounted_items:
            title = item.get("title", item.get("name", "Sản phẩm"))
            curr_price = item.get("current_price", 0)
            orig_price = item.get("original_price", 0)
            discount = item.get("discount_rate", 0)
            url = item.get("url", "#")

            curr_formatted = f"{curr_price:,}đ".replace(",", ".")
            orig_formatted = f"{orig_price:,}đ".replace(",", ".")

            msg += f"🔹 <b>{title}</b>\n"
            msg += f"🔻 Giá cũ: <s>{orig_formatted}</s> ➔ <b>{curr_formatted}</b> (-{discount}%)\n"
            msg += f"🔗 <a href='{url}'>Xem chi tiết sản phẩm</a>\n\n"

        msg += f"-----------------------------------\n"
        msg += f"🤖 <i>Tự động gửi từ Antigravity Price Tracker</i>"

        return self.send_message(msg)

if __name__ == "__main__":
    test_notifier = TelegramNotifier()
    sample_data = [
        {
            "title": "Tủ lạnh Panasonic Inverter 322 lít NR-TV341BPVN",
            "current_price": 11490000,
            "original_price": 12990000,
            "discount_rate": 11.5,
            "url": "https://www.dienmayxanh.com/tu-lanh/panasonic-nr-tv341bpvn",
        }
    ]
    test_notifier.send_price_drop_alerts(sample_data)
