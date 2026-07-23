import os
import json
import logging
from datetime import datetime, timezone, timedelta

# Vietnam Timezone UTC+7
TZ_VIETNAM = timezone(timedelta(hours=7))

HISTORY_FILE = "price_history.json"

def get_vietnam_now() -> datetime:
    """Returns current datetime in Vietnam Timezone (GMT+7)."""
    return datetime.now(TZ_VIETNAM)

def get_vietnam_time_str(fmt: str = "%d/%m/%Y %H:%M:%S") -> str:
    """Returns formatted string of current Vietnam time."""
    return get_vietnam_now().strftime(fmt)

def load_price_history(filepath: str = HISTORY_FILE) -> dict:
    """Load historical price mapping from JSON file."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading {filepath}: {e}")
    return {}

def save_price_history(history_data: dict, filepath: str = HISTORY_FILE):
    """Save historical price mapping to JSON file."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logging.error(f"Error saving {filepath}: {e}")

def process_price_comparison(scraped_data: list, filepath: str = HISTORY_FILE) -> list:
    """
    Compares scraped current price against previous run's price from price_history.json.
    - Adds `previous_price`, `previous_price_str`, and `price_change_rate` to items.
    - Saves updated prices back into price_history.json for the next cycle.
    """
    history = load_price_history(filepath)
    now_str = get_vietnam_time_str()

    compared_items = []
    for item in scraped_data:
        url = item.get("url")
        current_price = item.get("current_price", 0)

        # Retrieve previous run price
        prev_record = history.get(url, {})
        previous_price = prev_record.get("last_price", 0) if isinstance(prev_record, dict) else 0

        # Calculate price drop/change relative to PREVIOUS run
        price_drop = 0
        discount_rate_vs_prev = 0.0

        if previous_price > 0 and current_price > 0:
            if current_price < previous_price:
                price_drop = previous_price - current_price
                discount_rate_vs_prev = round((price_drop / previous_price) * 100, 1)

        previous_price_str = f"{previous_price:,}₫".replace(",", ".") if previous_price > 0 else "Chưa có (Lần đầu quét)"

        item["previous_price"] = previous_price
        item["previous_price_str"] = previous_price_str
        item["price_drop_vs_prev"] = price_drop
        item["discount_rate_vs_prev"] = discount_rate_vs_prev

        compared_items.append(item)

        # Update history for next run if current_price valid (> 0)
        if current_price > 0:
            history[url] = {
                "last_price": current_price,
                "title": item.get("title", ""),
                "last_updated": now_str
            }

    # Persist history
    save_price_history(history, filepath)
    return compared_items
