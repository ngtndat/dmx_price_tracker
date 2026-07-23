import os
import sys
import time
import pytz
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Local import
from main_automation import run_daily_dmx_price_tracking_pipeline

VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")

def start_daily_scheduler(hour: int = 8, minute: int = 0):
    """
    Start local background cron job running daily at specified hour:minute (Default: 08:00 AM VN_TZ).
    """
    scheduler = BackgroundScheduler(timezone=VN_TZ)
    
    scheduler.add_job(
        run_daily_dmx_price_tracking_pipeline,
        trigger=CronTrigger(hour=hour, minute=minute, timezone=VN_TZ),
        id="daily_8am_dmx_price_tracker",
        name="Quét giá Điện Máy Xanh & Gửi Telegram 8:00 AM",
        replace_existing=True
    )
    
    scheduler.start()
    
    now_str = datetime.now(VN_TZ).strftime("%Y-%m-%d %H:%M:%S")
    print("=" * 70)
    print(" ⏰ ĐÃ KÍCH HOẠT LỊCH QUÉT GIÁ ĐIỆN MÁY XANH TỰ ĐỘNG LÚC 08:00 SÁNG!")
    print(f" 🌐 Thời gian hiện tại: {now_str} (Múi giờ Asia/Ho_Chi_Minh)")
    print(" 📊 Kết quả quét sẽ tự động cập nhật Google Sheet và báo Telegram.")
    print("=" * 70)
    
    return scheduler

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        print("⚡ Thực thi quét giá ngay lập tức theo yêu cầu (--now)...")
        run_daily_dmx_price_tracking_pipeline()
    else:
        scheduler = start_daily_scheduler(hour=8, minute=0)
        try:
            print("\n🔄 Scheduler đang lắng nghe trong nền... Bấm Ctrl+C để dừng.")
            while True:
                time.sleep(2)
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
            print("\n🛑 Đã dừng scheduler.")
