import os
import sys
import json
import logging
import re
import requests
import urllib3
from bs4 import BeautifulSoup

# Suppress insecure request warnings if verify=False is used
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

def clean_price(price_str: str) -> int:
    """Helper function to clean and parse price string to integer."""
    if not price_str:
        return 0
    digits = "".join(c for c in str(price_str) if c.isdigit())
    return int(digits) if digits else 0

def format_price_str(val_int: int) -> str:
    """Format integer price to VND currency string."""
    if not val_int or val_int == 0:
        return "N/A"
    return f"{val_int:,}".replace(",", ".") + "₫"

def clean_text(text: str) -> str:
    if not text:
        return ""
    return " ".join(text.split())

def scrape_dmx_product(url: str) -> dict:
    """
    Advanced scraper for Dien May Xanh product page combining Colab logic & JSON-LD parsing.
    Returns exact Selling Price, MRP Price, Discount %, Stock Status, and Promotions.
    """
    try:
        logging.info(f"Fetching URL: {url}")
        response = requests.get(url, headers=HEADERS, verify=False, timeout=15)
        
        if response.status_code == 404:
            return {
                "url": url,
                "title": "Sản phẩm bỏ mẫu / Không tìm thấy",
                "current_price": 0,
                "original_price": 0,
                "discount_rate": 0,
                "in_stock": False,
                "status": "Sản phẩm bỏ mẫu (404)",
                "promotions": "N/A",
                "success": False,
                "error": "HTTP 404"
            }
        elif response.status_code != 200:
            return {
                "url": url,
                "title": "Lỗi kết nối",
                "current_price": 0,
                "original_price": 0,
                "discount_rate": 0,
                "in_stock": False,
                "status": f"Error HTTP {response.status_code}",
                "promotions": "N/A",
                "success": False,
                "error": f"HTTP {response.status_code}"
            }

        soup = BeautifulSoup(response.text, "html.parser")
        raw_text_lower = response.text.lower()
        
        is_discontinued = any(w in raw_text_lower for w in ["ngừng kinh doanh", "ngung kinh doanh", "không kinh doanh"])
        
        title = ""
        current_price = 0
        original_price = 0

        # --- 1. JSON-LD Parser (Highest Accuracy for Price & Title) ---
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

        # --- 3. Selling Price & MRP Price Parsing (Colab Scraper Logic) ---
        bs_price = soup.find(class_="bs_price")
        box_price_present = soup.find(class_="box-price-present")
        
        if current_price == 0:
            if box_price_present:
                current_price = clean_price(box_price_present.text)
            elif bs_price and bs_price.find('strong'):
                current_price = clean_price(bs_price.find('strong').text)
            else:
                price_strong = soup.find("strong", class_="price") or soup.find("p", class_="giagiam")
                if price_strong:
                    current_price = clean_price(price_strong.text)

        # MRP / Original Price Extraction
        box_price_old = soup.find(class_="box-price-old")
        if bs_price and bs_price.find('em'):
            original_price = clean_price(bs_price.find('em').text)
        elif box_price_old:
            original_price = clean_price(box_price_old.text)
        else:
            price_old = soup.find("p", class_="giagoc") or soup.find(class_="price-old")
            if price_old:
                original_price = clean_price(price_old.text)

        if original_price == 0 or original_price < current_price:
            original_price = current_price

        # --- 4. Promotions Parsing ---
        promo_list = []
        promo_block = soup.find(class_="block-price1") or soup.find(class_="box-promo")
        if promo_block:
            title_promo = promo_block.find(class_="pr-txtb")
            if title_promo:
                promo_list.append(clean_text(title_promo.text))
            divb_items = promo_block.find_all(class_="divb") or promo_block.find_all("li")
            for idx, item in enumerate(divb_items, 1):
                txt = clean_text(item.text)
                if txt:
                    promo_list.append(f"{idx}. {txt}")
        
        promotions = " | ".join(promo_list) if promo_list else "Không có khuyến mãi riêng."

        # --- 5. Stock Status ---
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
            "promotions": promotions,
            "success": True,
        }

    except Exception as e:
        logging.error(f"Error scraping {url}: {e}")
        return {
            "url": url,
            "title": "Sản phẩm DMX",
            "current_price": 0,
            "current_price_str": "N/A",
            "original_price": 0,
            "original_price_str": "N/A",
            "discount_rate": 0,
            "in_stock": False,
            "status": f"Error: {e}",
            "promotions": "N/A",
            "success": False,
            "error": str(e)
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

