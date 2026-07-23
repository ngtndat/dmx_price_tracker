import os
import sys
import pytz
from datetime import datetime

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


# Local imports
from config import PRICE_DROP_ALERT_THRESHOLD_PCT, SPREADSHEET_ID
from dmx_scraper import scrape_all_dmx_targets
from sheets_updater import update_daily_price_sheet, append_price_history_log
from telegram_notifier import build_discount_alert_message, send_telegram_message

VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")

def run_daily_dmx_price_tracking_pipeline():
    """
    Main pipeline function triggered every morning at 08:00 AM.
    1. Scrape DMX target categories/products
    2. Identify price drops & competitor discounts
    3. Update Google Sheets
    4. Send Telegram alerts
    """
    start_time = datetime.now(VN_TZ)
    now_str = start_time.strftime("%Y-%m-%d %H:%M:%S")

    print("\n" + "="*75)
    print(f"🚀 [{now_str}] BẮT ĐẦU CHẠY AUTOMATION QUÉT GIÁ ĐIỆN MÁY XANH")
    print("="*75)

    # Step 1: Scrape DMX products
    products = scrape_all_dmx_targets()
    if not products:
        print("❌ Không có dữ liệu sản phẩm nào được quét. Kết thúc quy trình.")
        return

    # Step 2: Identify discounted products
    discounted_products = [
        p for p in products 
        if p.get("discount_pct", 0.0) >= PRICE_DROP_ALERT_THRESHOLD_PCT and p.get("selling_price", 0) > 0
    ]

    print(f"\n🔍 Thống kê: Tổng {len(products)} sản phẩm | {len(discounted_products)} sản phẩm có ưu đãi giảm giá (>= {PRICE_DROP_ALERT_THRESHOLD_PCT}%).")

    # Step 3: Update Google Sheets
    print("\n📊 1/2. Cập nhật Google Sheets...")
    sheet_success = update_daily_price_sheet(products, SPREADSHEET_ID)

    if discounted_products:
        print("📈 2/2. Lưu lịch sử các đợt giảm giá vào Google Sheets...")
        append_price_history_log(discounted_products, SPREADSHEET_ID)

    # Step 4: Dispatch Telegram Alert
    if discounted_products:
        print("\n📲 Đang định dạng và gửi cảnh báo đến Telegram...")
        telegram_msg = build_discount_alert_message(discounted_products, total_scanned=len(products))
        send_telegram_message(telegram_msg)
    else:
        print("\nℹ️ Không phát hiện sản phẩm nào giảm giá vượt ngưỡng. Không gửi Telegram.")

    duration = (datetime.now(VN_TZ) - start_time).total_seconds()
    print("="*75)
    print(f"✅ HOÀN THÀNH TOÀN BỘ QUY TRÌNH AUTOMATION TRONG {duration:.2f} GIÂY!")
    print("="*75 + "\n")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        run_daily_dmx_price_tracking_pipeline()
    else:
        # Default behavior when run directly
        print("💡 Đang chạy kiểm thử trực tiếp quy trình automation...")
        run_daily_dmx_price_tracking_pipeline()
