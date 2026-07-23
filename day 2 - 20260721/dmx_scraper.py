import re
import sys
import time
import requests
import urllib3
from bs4 import BeautifulSoup
from config import HEADERS, DEFAULT_DMX_TARGETS

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def clean_price(price_str: str) -> int:
    """Extract numeric integer value from price string (e.g. '12.490.000₫' -> 12490000)."""
    if not price_str:
        return 0
    cleaned = re.sub(r"[^\d]", "", price_str)
    return int(cleaned) if cleaned else 0

def format_price_vnd(amount: int) -> str:
    """Format integer price to VND string (e.g. 12490000 -> '12.490.000₫')."""
    if not amount or amount <= 0:
        return "N/A"
    return f"{amount:,}".replace(",", ".") + "₫"

def clean_text(text: str) -> str:
    if not text:
        return ""
    return " ".join(text.split())

def parse_dmx_product_detail(url: str) -> dict:
    """
    Fetch and parse a single DMX product detail page to extract promotions, exact price, and status.
    """
    try:
        response = requests.get(url, headers=HEADERS, verify=False, timeout=10)
        if response.status_code == 404:
            return {
                "status": "ngừng kinh doanh",
                "selling_price": 0,
                "mrp_price": 0,
                "promotions": "Sản phẩm bỏ mẫu / Không tìm thấy trang",
            }
        elif response.status_code != 200:
            return {
                "status": "lỗi tải trang",
                "selling_price": 0,
                "mrp_price": 0,
                "promotions": f"Lỗi HTTP {response.status_code}",
            }

        soup = BeautifulSoup(response.text, "html.parser")
        text_lower = response.text.lower()
        
        is_discontinued = any(w in text_lower for w in ["ngừng kinh doanh", "ngung kinh doanh", "không kinh doanh", "tạm hết hàng"])

        # Extract Selling Price
        selling_price = 0
        box_price_present = soup.find(class_="box-price-present")
        bs_price = soup.find(class_="bs_price")
        price_one = soup.find(class_="price-one")
        price_strong = soup.find("strong", class_="price")

        if box_price_present:
            selling_price = clean_price(box_price_present.text)
        elif bs_price and bs_price.find("strong"):
            selling_price = clean_price(bs_price.find("strong").text)
        elif price_one:
            strong_p = price_one.find(class_="box-price-present") or price_one
            selling_price = clean_price(strong_p.text)
        elif price_strong:
            selling_price = clean_price(price_strong.text)

        # Extract MRP Price (Original Price before discount)
        mrp_price = 0
        box_price_old = soup.find(class_="box-price-old")
        if box_price_old:
            mrp_price = clean_price(box_price_old.text)
        elif bs_price and bs_price.find("em"):
            mrp_price = clean_price(bs_price.find("em").text)
        else:
            price_old = soup.find(class_="price-old")
            if price_old:
                mrp_price = clean_price(price_old.text)

        if mrp_price == 0:
            mrp_price = selling_price

        # Extract Promotions
        promo_list = []
        promo_block = soup.find(class_="block-price1") or soup.find(class_="pr-item")
        if promo_block:
            divb_items = promo_block.find_all(class_="divb") or promo_block.find_all("li")
            for idx, item in enumerate(divb_items, 1):
                txt = clean_text(item.text)
                if txt:
                    promo_list.append(f"{idx}. {txt}")
        else:
            promo_divs = soup.find_all(class_=lambda x: x and any(w in str(x).lower() for w in ["promo", "gift", "policy-promo"]))
            for p_div in promo_divs[:3]:
                txt = clean_text(p_div.text)
                if txt and txt not in promo_list:
                    promo_list.append(txt)

        promotions = " | ".join(promo_list) if promo_list else "Không có khuyến mãi riêng"

        return {
            "status": "ngừng kinh doanh" if is_discontinued else "đang kinh doanh",
            "selling_price": selling_price,
            "mrp_price": mrp_price,
            "promotions": promotions,
        }
    except Exception as e:
        return {
            "status": "lỗi xử lý",
            "selling_price": 0,
            "mrp_price": 0,
            "promotions": f"Lỗi: {e}",
        }

def scrape_dmx_category(target_url: str, category_name: str = "Gia Dụng", max_items: int = 15) -> list[dict]:
    """
    Scrape product items from a DMX category page URL.
    """
    print(f"\n🔍 [DMX Scraper] Đang quét danh mục: '{category_name}' ({target_url})...")
    results = []
    
    try:
        response = requests.get(target_url, headers=HEADERS, verify=False, timeout=12)
        if response.status_code != 200:
            print(f"❌ Không thể truy cập DMX ({target_url}): HTTP {response.status_code}")
            return results

        soup = BeautifulSoup(response.text, "html.parser")
        
        # Product containers in DMX
        product_list = soup.find("ul", class_="listproduct") or soup.find("ul", class_=lambda x: x and "listproduct" in x)
        items = product_list.find_all("li", recursive=False) if product_list else soup.find_all("li", class_=lambda x: x and "item" in str(x))

        print(f"📦 Tìm thấy {len(items)} sản phẩm trong danh mục.")

        count = 0
        for li in items:
            if count >= max_items:
                break

            a_tag = li.find("a", class_="main-contain") or li.find("a")
            if not a_tag:
                continue

            name = a_tag.get("data-name")
            if not name:
                h3 = li.find("h3") or li.find("p", class_="product-title")
                name = h3.text.strip() if h3 else "Sản phẩm Điện Máy Xanh"

            href = a_tag.get("href", "")
            if not href:
                continue

            full_url = href if href.startswith("http") else f"https://www.dienmayxanh.com{href}"
            full_url = full_url.split("?")[0]

            # Price from data attributes or elements
            cat_price_str = a_tag.get("data-price") or "0"
            selling_price = clean_price(cat_price_str)
            
            if selling_price == 0:
                price_elem = li.find("strong", class_="price") or li.find(class_="box-price-present")
                if price_elem:
                    selling_price = clean_price(price_elem.text)

            mrp_elem = li.find("span", class_="percent") or li.find(class_="box-price-old") or li.find("p", class_="price-old")
            mrp_price = selling_price
            if mrp_elem:
                parsed_mrp = clean_price(mrp_elem.text)
                if parsed_mrp > selling_price:
                    mrp_price = parsed_mrp

            # Label status (e.g. Mới, Bán chạy, Giá rẻ)
            label_tag = li.find(class_="item-label") or li.find(class_="lb-tragop")
            label_text = clean_text(label_tag.text) if label_tag else ""

            # Check detailed promo & exact price if needed
            details = parse_dmx_product_detail(full_url)
            
            final_selling = details["selling_price"] if details["selling_price"] > 0 else selling_price
            final_mrp = details["mrp_price"] if details["mrp_price"] > 0 else mrp_price
            
            # Calculate discount percentage
            discount_pct = 0.0
            if final_mrp > final_selling and final_mrp > 0:
                discount_pct = round(((final_mrp - final_selling) / final_mrp) * 100, 1)

            product_data = {
                "category": category_name,
                "name": name,
                "url": full_url,
                "selling_price": final_selling,
                "mrp_price": final_mrp,
                "discount_pct": discount_pct,
                "status": details["status"] if details["status"] != "lỗi xử lý" else ("Mới" if "mới" in label_text.lower() else "đang kinh doanh"),
                "promotions": details["promotions"],
            }

            results.append(product_data)
            count += 1
            print(f"   [{count}/{max_items}] {name[:40]} | Giá: {format_price_vnd(final_selling)} (-{discount_pct}%)")
            time.sleep(0.5)

    except Exception as e:
        print(f"❌ Lỗi khi cào danh mục {category_name}: {e}")

    return results

def scrape_all_dmx_targets(targets: list[dict] = None) -> list[dict]:
    """
    Scrape all target categories defined in configuration.
    """
    targets = targets or DEFAULT_DMX_TARGETS
    all_products = []
    
    print("=" * 70)
    print("🚀 BẮT ĐẦU QUÉT GIÁ TOÀN BỘ SẢN PHẨM MỤC TIÊU TRÊN ĐIỆN MÁY XANH")
    print("=" * 70)

    for target in targets:
        items = scrape_dmx_category(target["url"], category_name=target["category"], max_items=5)
        all_products.extend(items)

    print(f"\n✅ Hoàn thành quét {len(all_products)} sản phẩm Điện Máy Xanh.")
    return all_products

if __name__ == "__main__":
    import sys
    if "--test" in sys.argv or len(sys.argv) == 1:
        test_results = scrape_all_dmx_targets(DEFAULT_DMX_TARGETS[:2])
        print(f"\n📊 Tổng số sản phẩm test: {len(test_results)}")
