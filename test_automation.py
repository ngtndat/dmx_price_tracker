import sys
import unittest
import json
import os

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from dmx_scraper import parse_price, scrape_dmx_product
from telegram_bot import TelegramNotifier
from gsheet_manager import GSheetManager

class TestDmxAutomation(unittest.TestCase):
    def test_parse_price(self):
        self.assertEqual(parse_price("12.990.000₫"), 12990000)
        self.assertEqual(parse_price("8,500,000 đ"), 8500000)
        self.assertEqual(parse_price(""), 0)

    def test_products_json_exists(self):
        self.assertTrue(os.path.exists("products.json"))
        with open("products.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertIsInstance(data, list)
            self.assertGreater(len(data), 0)

    def test_telegram_notifier_format(self):
        notifier = TelegramNotifier()
        sample_data = [
            {
                "title": "Tủ lạnh Panasonic Test",
                "current_price": 11000000,
                "original_price": 13000000,
                "discount_rate": 15.3,
                "url": "https://example.com"
            }
        ]
        result = notifier.send_price_drop_alerts(sample_data)

    def test_gsheet_manager_simulation(self):
        manager = GSheetManager()
        result = manager.update_price_records([
            {"id": "test-id", "title": "Test Product", "current_price": 1000000, "original_price": 1200000, "discount_rate": 16.6, "in_stock": True, "url": "https://example.com"}
        ])

if __name__ == "__main__":
    unittest.main()
