import sys
import requests
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def send_telegram_message(message_text: str, parse_mode: str = "HTML") -> bool:
    """
    Send an HTML-formatted message to Telegram Bot / Channel.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("\n⚠️ [Telegram Notifier] TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID chưa được cấu hình.")
        print("💡 Message xem trước (Console Notification):\n" + "-"*40)
        print(message_text)
        print("-" * 40)
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message_text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        res_json = response.json()

        if response.status_code == 200 and res_json.get("ok"):
            print("📲 [Telegram] ✅ Gửi thông báo cảnh báo giá thành công!")
            return True
        else:
            print(f"❌ [Telegram] Gửi thất bại: {res_json.get('description', response.text)}")
            return False
    except Exception as e:
        print(f"❌ [Telegram] Lỗi kết nối API: {e}")
        return False

def format_price_str(val: int) -> str:
    if not val or val <= 0:
        return "N/A"
    return f"{val:,}".replace(",", ".") + "₫"

def build_discount_alert_message(discounted_products: list[dict], total_scanned: int) -> str:
    """
    Build a structured Telegram HTML notification for discounted products.
    """
    lines = []
    lines.append("🚨 <b>[CẢNH BÁO ĐỐI THỦ GIẢM GIÁ - ĐIỆN MÁY XANH]</b> 🚨")
    lines.append(f"⏰ <i>Quét lúc: 08:00 AM | Tổng sản phẩm quét: {total_scanned}</i>\n")
    lines.append(f"🔥 Phát hiện <b>{len(discounted_products)}</b> sản phẩm chính có giá ưu đãi đặc biệt:\n")

    for idx, p in enumerate(discounted_products, 1):
        name = p.get("name", "Sản phẩm")
        cat = p.get("category", "")
        selling = format_price_str(p.get("selling_price", 0))
        mrp = format_price_str(p.get("mrp_price", 0))
        pct = p.get("discount_pct", 0.0)
        url = p.get("url", "")
        promo = p.get("promotions", "Không có")

        lines.append(f"<b>{idx}. [{cat}] {name}</b>")
        lines.append(f"   💸 Giá niêm yết: <s>{mrp}</s>")
        lines.append(f"   💥 Giá hiện tại: <b>{selling}</b> (🔻 <b>-{pct}%</b>)")
        lines.append(f"   🎁 Khuyến mãi: <i>{promo[:60]}...</i>")
        lines.append(f"   🔗 <a href='{url}'>Xem sản phẩm trên Điện Máy Xanh</a>\n")

    lines.append("📊 <i>Báo cáo chi tiết đã được tự động cập nhật lên Google Sheets!</i>")
    return "\n".join(lines)

if __name__ == "__main__":
    if "--test" in sys.argv or len(sys.argv) == 1:
        sample_alerts = [
            {
                "category": "Máy Lọc Không Khí",
                "name": "Máy lọc không khí LG PuriCare 360 Hit AS60GHWG0",
                "mrp_price": 7500000,
                "selling_price": 5990000,
                "discount_pct": 20.1,
                "promotions": "Tặng PMH 200k + Miễn phí vận chuyển",
                "url": "https://www.dienmayxanh.com/may-loc-khong-khi/lg-puricare-360-hit-as60ghwg0"
            },
            {
                "category": "Máy Lạnh",
                "name": "Máy lạnh Panasonic Inverter 1 HP CU/CS-PU9XKH-8M",
                "mrp_price": 11490000,
                "selling_price": 9890000,
                "discount_pct": 13.9,
                "promotions": "Bao công lắp đặt + Tặng ống đồng",
                "url": "https://www.dienmayxanh.com/may-lanh/panasonic-cu-cs-pu9xkh-8m"
            }
        ]
        msg = build_discount_alert_message(sample_alerts, 10)
        send_telegram_message(msg)
