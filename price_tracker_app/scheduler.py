"""
Price Check Scheduler for PricePulse
Runs every 6 hours at 00:00, 06:00, 12:00, 18:00 (GMT+7 / Asia/Ho_Chi_Minh)
"""
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import database
import scraper

VN_TZ = pytz.timezone("Asia/Ho_Chi_Minh")


def run_price_check():
    """
    Main cron job: iterates all active products and refreshes prices.
    If a product URL is dead (404, gone, etc), marks it as inactive.
    """
    products = database.get_all_active_products()
    total = len(products)
    updated = 0
    dead = 0

    print(f"[Scheduler] Starting price check for {total} active products...")

    for product in products:
        try:
            result = scraper.scrape_product_info(product["original_url"])

            if result.get("is_dead"):
                database.mark_product_dead(product["id"])
                dead += 1
                print(f"[Scheduler] Product {product['id']} dead: {product['original_url'][:60]}")
            else:
                new_price = result.get("current_price")
                if new_price and new_price > 0:
                    old_price = product["current_price"]
                    database.update_product_price(product["id"], new_price)
                    change = ((new_price - old_price) / old_price * 100) if old_price else 0
                    print(f"[Scheduler] Product {product['id']} updated: {old_price:,} → {new_price:,} VND ({change:+.1f}%)")
                    updated += 1

        except Exception as e:
            print(f"[Scheduler] Error checking product {product['id']}: {e}")

    print(f"[Scheduler] Done. Updated: {updated}, Dead: {dead}, Skipped: {total - updated - dead}")


def start_scheduler():
    """
    Initializes and starts the APScheduler background scheduler.
    Runs price checks at 00:00, 06:00, 12:00, 18:00 Vietnam time (GMT+7).
    Returns the scheduler instance for graceful shutdown.
    """
    scheduler = BackgroundScheduler(timezone=VN_TZ)

    # Run at 0:00, 6:00, 12:00, 18:00 GMT+7
    scheduler.add_job(
        run_price_check,
        trigger=CronTrigger(hour="0,6,12,18", minute=0, timezone=VN_TZ),
        id="price_check_6h",
        name="6-Hour Price Check (GMT+7)",
        replace_existing=True,
        misfire_grace_time=300  # Allow up to 5 min late start
    )

    scheduler.start()
    print("[Scheduler] APScheduler started. Next runs: 00:00, 06:00, 12:00, 18:00 (GMT+7)")
    return scheduler
