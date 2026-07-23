import os
import sys
import json
import logging
from datetime import datetime

# Configure stdout encoding for Windows compatibility
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class GSheetManager:
    def __init__(self, creds_file: str = None, spreadsheet_name_or_id: str = None):
        self.creds_file = creds_file
        self.spreadsheet_name_or_id = spreadsheet_name_or_id
        self.client = None

        if creds_file and os.path.exists(creds_file):
            try:
                import gspread
                self.client = gspread.service_account(filename=creds_file)
                logging.info(f"Successfully authenticated Google Sheets API with credentials: {creds_file}")
            except Exception as e:
                logging.error(f"Failed to authenticate Google Sheets API: {e}")

    def update_price_records(self, scraped_data: list) -> bool:
        """Appends daily price snapshot into Google Sheets."""
        if not self.client:
            logging.warning("Google Sheets client not authenticated. Simulating update.")
            try:
                print(f"\n--- [GOOGLE SHEETS SIMULATED UPDATE] ---")
                print(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
                for item in scraped_data:
                    print(f" - {item.get('title')}: {item.get('current_price'):,} VND (Stock: {item.get('in_stock')})")
                print(f"----------------------------------------\n")
            except Exception:
                pass
            return False

        try:
            sheet = self.client.open(self.spreadsheet_name_or_id).sheet1
            today_str = datetime.now().strftime("%Y-%m-%d %H:%M")

            rows = []
            for item in scraped_data:
                rows.append([
                    today_str,
                    item.get("id", ""),
                    item.get("title", ""),
                    item.get("current_price", 0),
                    item.get("original_price", 0),
                    item.get("discount_rate", 0),
                    "Có hàng" if item.get("in_stock") else "Hết hàng",
                    item.get("url", "")
                ])

            sheet.append_rows(rows)
            logging.info(f"Appended {len(rows)} rows to Google Sheet: {self.spreadsheet_name_or_id}")
            return True
        except Exception as e:
            logging.error(f"Failed to append rows to Google Sheets: {e}")
            return False

if __name__ == "__main__":
    manager = GSheetManager()
    manager.update_price_records([
        {"id": "test-1", "title": "Tủ lạnh Panasonic Test", "current_price": 11490000, "original_price": 12990000, "discount_rate": 11.5, "in_stock": True, "url": "https://example.com"}
    ])
