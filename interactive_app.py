import os
import sys
import time
import json
import logging
from datetime import datetime

from dmx_scraper import scrape_url_list, scrape_dmx_product
from gsheet_manager import GSheetManager
from telegram_bot import TelegramNotifier, DEFAULT_TELEGRAM_TOKEN, DEFAULT_CHAT_ID

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

CONFIG_FILE = "user_products.json"

def load_user_urls() -> list:
    """Load URLs from user_products.json or default list."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    return [
        "https://www.dienmayxanh.com/may-loc-khong-khi/may-loc-khong-khi-lg-puricare-360-hit-as60ghwg0-41w"
    ]

def save_user_urls(urls: list):
    """Save URLs to user_products.json."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(urls, f, ensure_ascii=False, indent=2)

def run_single_cycle(urls: list, enable_telegram: bool = False, gsheet_name: str = "DMX_Price_Tracker") -> list:
    """Runs one scraping cycle, updates Google Sheets, and sends Telegram alert if enabled."""
    print(f"\n=======================================================")
    print(f"🚀 BẮT ĐẦU CHU KỲ QUÉT GIÁ DMX ({datetime.now().strftime('%d/%m/%Y %H:%M:%S')})")
    print(f"=======================================================")
    
    # 1. Scrape URLs
    results = scrape_url_list(urls)
    
    # 2. Console Summary Table
    print("\n📊 KẾT QUẢ QUÉT GIÁ (KIỂM TRA DUYỆT BẰNG MẮT THƯỜNG):")
    print("-" * 110)
    print(f"{'STT':<4} | {'TÊN SẢN PHẨM':<45} | {'GIÁ BÁN':<12} | {'GIÁ GỐC':<12} | {'GIẢM (%)':<8} | {'TRẠNG THÁI':<15}")
    print("-" * 110)
    for idx, r in enumerate(results, 1):
        title = (r.get("title")[:42] + "...") if len(r.get("title", "")) > 45 else r.get("title", "")
        print(f"{idx:<4} | {title:<45} | {r.get('current_price_str'):<12} | {r.get('original_price_str'):<12} | {str(r.get('discount_rate')) + '%':<8} | {r.get('status'):<15}")
    print("-" * 110)

    # 3. Export to Google Sheets
    gsheet_creds = os.environ.get("GSHEET_CREDS_FILE", "day 2 - 20260721/client_secret_228306670309-5mf83aqa0ksirhvg5lqrb790e52mjig4.apps.googleusercontent.com.json")
    gsheet = GSheetManager(creds_file=gsheet_creds, spreadsheet_name_or_id=gsheet_name)
    print("\n📝 Xuất dữ liệu sang Google Sheets...")
    gsheet.update_price_records(results)

    # 4. Telegram Alerts (Only if enabled and price drops exist)
    if enable_telegram:
        print("\n🔔 Telegram Alerts: ĐANG BẬT -> Kiểm tra gửi tin nhắn...")
        telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN", DEFAULT_TELEGRAM_TOKEN)
        telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID", DEFAULT_CHAT_ID)
        notifier = TelegramNotifier(bot_token=telegram_token, chat_id=telegram_chat_id)
        
        discounted = [r for r in results if r.get("success") and r.get("discount_rate", 0) > 0]
        if discounted:
            notifier.send_price_drop_alerts(discounted)
        else:
            print(" -> Không có sản phẩm nào giảm giá trong chu kỳ này.")
    else:
        print("\n🔕 Telegram Alerts: ĐANG TẮT (Chưa kích hoạt cho tới khi bạn bấm xác nhận).")

    return results

def main_menu():
    urls = load_user_urls()
    enable_telegram = False
    gsheet_name = "DMX_Price_Tracker"

    while True:
        print("\n" + "="*60)
        print("🎯 BẢNG ĐIỀU KHIỂN QUÉT GIÁ ĐIỆN MÁY XANH (AUTOMATION CONTROL)")
        print("="*60)
        print(f"1. Dán/Cập nhật danh sách Link sản phẩm (Đang có: {len(urls)} link)")
        print(f"2. [TEST] Quét giá NGAY và xuất Google Sheets (Xem console kiểm tra)")
        print(f"3. Kích hoạt/Tắt thông báo Telegram (Hiện tại: {'BẬT 🟢' if enable_telegram else 'TẮT 🔴'})")
        print(f"4. Kích hoạt LỊCH CHẠY NỀN tự động mỗi 2 TẾNG (120 phút)")
        print(f"5. Xem hướng dẫn chạy Server / GitHub Actions / Laptop 24/7")
        print("0. Thoát")
        print("="*60)
        
        choice = input("👉 Chọn chức năng (0-5): ").strip()
        
        if choice == "1":
            print("\n--- NHẬP DANH SÁCH LINK SẢN PHẨM ĐIỆN MÁY XANH ---")
            print("Dán các đường link URL sản phẩm (mỗi link 1 dòng). Gõ 'DONE' khi kết thúc:")
            new_urls = []
            while True:
                line = input("> ").strip()
                if line.upper() == "DONE":
                    break
                if line.startswith("http"):
                    new_urls.append(line)
            if new_urls:
                urls = new_urls
                save_user_urls(urls)
                print(f"✅ Đã lưu {len(urls)} đường link vào danh sách theo dõi!")
            else:
                print("⚠️ Chưa nhập link hợp lệ nào.")

        elif choice == "2":
            print("\n🔄 Đang thực hiện TEST quét giá và xuất Google Sheet...")
            run_single_cycle(urls, enable_telegram=enable_telegram, gsheet_name=gsheet_name)

        elif choice == "3":
            enable_telegram = not enable_telegram
            print(f"\n🔔 Đã đổi trạng thái Telegram sang: {'BẬT 🟢' if enable_telegram else 'TẮT 🔴'}")

        elif choice == "4":
            print(f"\n⏱️ BẮT ĐẦU CHẾ ĐỘ CHẠY LỊCH NỀN MỖI 2 TIẾNG (120 PHÚT)...")
            print("Chương trình sẽ tự động quét lại sau mỗi 2 tiếng. Nhấn Ctrl + C để dừng.")
            interval_seconds = 2 * 60 * 60  # 2 hours
            try:
                cycle_count = 1
                while True:
                    print(f"\n--- CHU KỲ LẦN THỨ #{cycle_count} ---")
                    run_single_cycle(urls, enable_telegram=enable_telegram, gsheet_name=gsheet_name)
                    cycle_count += 1
                    print(f"\n⏳ Đang đếm ngược 2 tiếng (7200 giây) cho chu kỳ tiếp theo...")
                    time.sleep(interval_seconds)
            except KeyboardInterrupt:
                print("\n⏹️ Đã dừng lịch chạy nền.")

        elif choice == "5":
            print("\n" + "="*60)
            print("💡 CÁC TỦY CHỌN CHẠY NỀN ĐỊNH KỲ (LAPTOP VS SERVER)")
            print("="*60)
            print("""
OPTION 1: Chạy trực tiếp trên Laptop (Không tốn chi phí)
  - Sử dụng tính năng 4 trong menu này (giữ ứng dụng chạy ngầm trên laptop).
  - Hoặc tạo Task Scheduler trên Windows chạy lệnh 'python interactive_app.py' định kỳ.

OPTION 2: Chạy miễn phí trên GitHub Actions (Khuyên dùng cho Server)
  - Đưa mã nguồn lên GitHub Repo cá nhân.
  - Cấu hình file workflow '.github/workflows/scrape_cron.yml' với lịch cron: '0 */2 * * *' (Mỗi 2 tiếng chạy 1 lần).
  - Không cần bật máy tính, GitHub sẽ tự động chạy code và gửi Telegram cho bạn!

OPTION 3: Chạy trên Server VPS / Cloud 24/7 (PythonAnywhere / Render / Railway)
  - Upload code lên PythonAnywhere (Miễn phí) hoặc VPS Linux ($5/tháng).
  - Thiết lập crontab: '0 */2 * * * python3 /path/to/interactive_app.py'
""")
            input("\nNhấn Enter để quay lại menu chính...")

        elif choice == "0":
            print("Cảm ơn bạn đã sử dụng Antigravity Price Automation!")
            break

if __name__ == "__main__":
    main_menu()
