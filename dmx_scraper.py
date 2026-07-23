import os
import sys
import json
import logging
import re
import time
import requests
import urllib3
from bs4 import BeautifulSoup

# Suppress insecure request warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]

def clean_price(price_str: str) -> int:
    """Helper function to clean and parse price string to integer."""
    if not price_str:
        return 0
    digits = "".join(c for c in str(price_str) if c.isdigit())
    return int(digits) if digits else 0

def format_price_str(val_int: int) -> str:
    """Format integer price to VND currency string."""
    if not val_int or val_int == 0:
        return "0₫"
    return f"{val_int:,}".replace(",", ".") + "₫"

def clean_text(text: str) -> str:
    if not text:
        return ""
    return " ".join(text.split())

def scrape_dmx_product(url: str) -> dict:
    """
    Ultra-robust scraper for Dien May Xanh product page combining JSON-LD & multi-selector HTML fallback.
    Retries up to 3 times to prevent 0đ errors on Cloud runners.
    """
    response_text = ""
    status_code = 0

    for attempt in range(1, 4):
        headers = {
            "User-Agent": USER_AGENTS[(attempt - 1) % len(USER_AGENTS)],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        }
        try:
            logging.info(f"Fetching URL (Attempt {attempt}): {url}")
            res = requests.get(url, headers=headers, verify=False, timeout=15)
            status_code = res.status_code
            if res.status_code == 200 and len(res.text) > 1000:
                response_text = res.text
                break
        except Exception as e:
            logging.warning(f"Attempt {attempt} failed: {e}")
            time.sleep(1)

    if not response_text:
        return {
            "url": url,
            "title": "Sản phẩm DMX (Lỗi kết nối)",
            "current_price": 0,
            "current_price_str": "0₫",
            "original_price": 0,
            "original_price_str": "0₫",
            "discount_rate": 0,
            "in_stock": False,
            "status": f"Error HTTP {status_code}",
            "promotions": "N/A",
            "success": False,
            "error": f"HTTP {status_code}"
        }

    soup = BeautifulSoup(response_text, "html.parser")
    raw_text_lower = response_text.lower()
    
    is_discontinued = any(w in raw_text_lower for w in ["ngừng kinh doanh", "ngung kinh doanh", "không kinh doanh"])
    
    title = ""
    current_price = 0
    original_price = 0

    # --- 1. JSON-LD Parser (Most Accurate) ---
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            if data.get("@type") == "Product":
                title = data.get("name", "")
                offers = data.get("offers", {})
                if isinstance(offers, dict):
                    current_price = int(float(offers.get("price", 0)))
                elif isinstance(offers, list) and len(offers) > 0:
                    current_price = int(float(offers[0].get("price", 0)))
                break
        except Exception:
            pass

    # --- 2. Title Extraction Fallback ---
    if not title:
        title_elem = soup.find("h1") or soup.find("div", class_="label") or soup.find("section", class_="detail")
        title = clean_text(title_elem.text) if title_elem else "Sản phẩm Điện Máy Xanh"

    # --- 3. Selling Price Fallback ---
    if current_price == 0:
        price_container = (
            soup.find("div", class_="bs_price")
            or soup.find("div", class_=re.compile(r"box-price|bs_detail|product-detail", re.I))
            or soup
        )
        curr_elem = (
            price_container.find("p", class_="giagiam")
            or price_container.find("b", class_="price")
            or price_container.find("span", class_="price")
            or price_container.find("p", class_="box-price-present")
            or price_container.find("strong", class_="price")
            or price_container.find("strong")
        )
        if curr_elem:
            current_price = clean_price(curr_elem.text)

    # --- 4. Regex Fallback if Price still 0 ---
    if current_price == 0:
        # Search for pattern like 5.390.000₫ or 5,390,000đ in raw HTML
        matches = re.findall(r"(\d{1,3}(?:\.\d{3}){2,3})\s*[₫đ]", response_text)
        if matches:
            for m in matches:
                parsed = clean_price(m)
                if parsed >= 100000:  # Minimum realistic appliance price
                    current_price = parsed
                    break

    # Original / MRP Price
    price_container = (
        soup.find("div", class_="bs_price")
        or soup.find("div", class_=re.compile(r"box-price|bs_detail|product-detail", re.I))
        or soup
    )
    old_elem = (
        price_container.find("em")
        or price_container.find("p", class_="giagoc")
        or price_container.find("cite", class_="his-price")
        or price_container.find("span", class_="box-price-old")
        or price_container.find("del")
    )
    if old_elem:
        parsed_old = clean_price(old_elem.text)
        if parsed_old > current_price:
            original_price = parsed_old

    if original_price == 0 or original_price < current_price:
        original_price = current_price

    # Stock Status
    in_stock = not is_discontinued
    if soup.find(string=re.compile(r"Tạm hết hàng|Hết hàng", re.I)):
        in_stock = False

    status_str = "Ngừng kinh doanh" if is_discontinued else ("Hết hàng" if not in_stock else "Đang kinh doanh")
    discount_rate = round(((original_price - current_price) / original_price * 100), 1) if original_price > current_price else 0.0

    return {
        "url": url,
        "title": title,
        "current_price": current_price,
        "current_price_str": format_price_str(current_price),
        "original_price": original_price,
        "original_price_str": format_price_str(original_price),
        "discount_rate": discount_rate,
        "in_stock": in_stock,
        "status": status_str,
        "promotions": "Chi tiết tại web.",
        "success": current_price > 0,
    }

def scrape_url_list(urls: list) -> list:
    """Scrape a list of product URLs."""
    results = []
    for idx, url in enumerate(urls, 1):
        url = url.strip()
        if not url:
            continue
        data = scrape_dmx_product(url)
        data["id"] = f"product-{idx}"
        results.append(data)
    return results

def scrape_all_products(products_file: str = "products.json") -> list:
    """Read products.json or list and scrape all items."""
    urls = []
    if os.path.exists(products_file):
        try:
            with open(products_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "url" in item:
                            urls.append(item["url"])
                        elif isinstance(item, str):
                            urls.append(item)
        except Exception as e:
            logging.error(f"Error reading {products_file}: {e}")

    if not urls:
        urls = ["https://www.dienmayxanh.com/may-loc-khong-khi/may-loc-khong-khi-lg-puricare-360-hit-as60ghwg0-41w"]

    return scrape_url_list(urls)

if __name__ == "__main__":
    test_url = "https://www.dienmayxanh.com/may-loc-khong-khi/may-loc-khong-khi-lg-puricare-360-hit-as60ghwg0-41w"
    print(json.dumps(scrape_dmx_product(test_url), ensure_ascii=False, indent=2))
