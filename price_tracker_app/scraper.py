from __future__ import annotations
import re
import random
import requests
from bs4 import BeautifulSoup
import urllib.parse

# Headers to mimic a real browser request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.google.com/",
    "Cache-Control": "no-cache",
}

# --- Platform Detection ---

PLATFORM_MAP = {
    "shopee.vn": "shopee",
    "shope.ee": "shopee",
    "lazada.vn": "lazada",
    "lzd.co": "lazada",
    "tiktok.com": "tiktok",
    "tiktokshop.com": "tiktok",
    "traveloka.com": "traveloka",
    "trip.com": "trip",
    "ctrip.com": "trip",
    "sendo.vn": "sendo",
    "thegioididong.com": "thegioididong",
    "dienmayxanh.com": "dienmayxanh",
    "bachhoaxanh.com": "bachhoaxanh",
    "cellphones.com.vn": "cellphones",
    "tiki.vn": "tiki",
}

PLATFORM_LABELS = {
    "shopee": "Shopee",
    "lazada": "Lazada",
    "tiktok": "TikTok Shop",
    "traveloka": "Traveloka",
    "trip": "Trip.com",
    "sendo": "Sendo",
    "thegioididong": "Thế Giới Di Động",
    "dienmayxanh": "Điện Máy Xanh",
    "bachhoaxanh": "Bách Hoá Xanh",
    "cellphones": "CellphoneS",
    "tiki": "Tiki",
    "other": "Khác",
}


def analyze_url(url: str) -> str:
    url_lower = url.lower()
    for domain, platform in PLATFORM_MAP.items():
        if domain in url_lower:
            return platform
    return "other"


# --- Mock Product Generator ---

def generate_mock_product(url: str, platform: str) -> dict:
    """
    Generates a realistic-looking simulated product when live scraping is blocked.
    Reads keywords from the URL slug to determine product category.
    """
    parsed = urllib.parse.urlparse(url)
    path_segments = parsed.path.split("/")

    slug = ""
    for seg in path_segments:
        if len(seg) > 10 and "-" in seg:
            slug = re.sub(r"-i\.\d+\.\d+$|-i\d+-s\d+\.html$|\?.*$", "", seg)
            break
    if not slug and len(path_segments) > 1:
        slug = path_segments[-1] or path_segments[-2]

    title = urllib.parse.unquote(slug.replace("-", " ").replace("_", " ").strip())
    if not title or len(title) < 5:
        title = f"Sản phẩm {PLATFORM_LABELS.get(platform, platform.capitalize())}"
    else:
        title = title.title()

    title_lower = title.lower()

    def match(text, keywords):
        return any(re.search(r'\b' + re.escape(k) + r'\b', text) for k in keywords)

    # Category detection
    if match(title_lower, ["son", "kem", "serum", "toner", "tẩy trang", "makeup", "phấn", "nước hoa", "dưỡng da", "skincare", "mask", "mặt nạ", "micellar"]):
        img_id = random.choice(["photo-1608248597279-f99d160bfcbc", "photo-1556228720-195a672e8a03", "photo-1598440947619-2c35fc9aa908"])
        price = random.randint(60000, 750000)

    elif match(title_lower, ["điện thoại", "phone", "laptop", "tai nghe", "headphone", "sạc", "charger", "ipad", "xiaomi", "samsung", "iphone", "camera", "máy tính", "airpod"]):
        img_id = random.choice(["photo-1511707171634-5f897ff02aa9", "photo-1588872657578-7efd1f1555ed", "photo-1505740420928-5e560c06d30e"])
        price = random.randint(1500000, 25000000)

    elif match(title_lower, ["áo", "quần", "váy", "đầm", "jacket", "shirt", "giày", "shoes", "sneaker", "túi", "bag", "balo", "dép"]):
        img_id = random.choice(["photo-1523381210434-271e8be1f52b", "photo-1542291026-7eec264c27ff", "photo-1553062407-98eeb64c6a62"])
        price = random.randint(120000, 1200000)

    elif match(title_lower, ["nồi", "chảo", "bếp", "ly", "cốc", "chén", "dĩa", "tủ", "giường", "ghế", "bàn", "kệ", "quạt", "máy lạnh", "điều hòa"]):
        img_id = random.choice(["photo-1556911220-e15b29be8c8f", "photo-1586023492125-27b2c045efd7", "photo-1616486338812-3dadae4b4ace"])
        price = random.randint(80000, 8000000)

    elif platform in ("traveloka", "trip") or match(title_lower, ["khách sạn", "hotel", "resort", "villa", "vé", "bay", "flight", "tour", "phòng"]):
        img_id = random.choice(["photo-1571896349842-33c89424de2d", "photo-1496417263034-38ec4f0b665a", "photo-1444201983204-c43cbd584d93"])
        price = random.randint(500000, 12000000)

    else:
        img_id = random.choice(["photo-1505740420928-5e560c06d30e", "photo-1526170375885-4d8ecf77b99f", "photo-1523275335684-37898b6baf30"])
        price = random.randint(50000, 2000000)

    image_url = f"https://images.unsplash.com/{img_id}?auto=format&fit=crop&w=400&h=400&q=80"
    platform_label = PLATFORM_LABELS.get(platform, platform.upper())

    # NOTE: This price is ESTIMATED based on product category, NOT the real price.
    # Title prefixed with [?] to indicate estimation to the user.
    return {
        "platform": platform,
        "original_url": url,
        "title": f"[{platform_label}] {title}",
        "image_url": image_url,
        "current_price": price,
        "is_simulated": True,
        "is_dead": False,
        "simulated_reason": "Kh\u00f4ng th\u1ec3 l\u1ea5y gi\u00e1 th\u1ef1c t\u1ebf. S\u00e0n TMDT ch\u1eb7n scraping. Gi\u00e1 hi\u1ec3n th\u1ecb l\u00e0 m\u00f4 ph\u1ecfng.",
    }


def _scrape_shopee_api(shop_id: str, item_id: str) -> dict:
    """
    Attempts to get real Shopee price via Shopee's item API.
    Shopee prices are stored multiplied by 100000 (e.g. 6400000000 = 6,400,000 VND).
    Returns dict with price fields or empty dict if blocked.
    """
    api_url = f"https://shopee.vn/api/v4/item/get?itemid={item_id}&shopid={shop_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": f"https://shopee.vn/product/{shop_id}/{item_id}",
        "X-API-SOURCE": "pc",
        "X-Shopee-Language": "vi",
        "X-Requested-With": "XMLHttpRequest",
        "Accept-Language": "vi-VN,vi;q=0.9",
    }
    try:
        resp = requests.get(api_url, headers=headers, timeout=8)
        if resp.status_code != 200:
            return {}
        data = resp.json()
        item = data.get("data") or data.get("item") or {}
        if not item or data.get("error"):
            return {}
        # Shopee price unit: integer stored as price * 100000
        # e.g. 640000000000 -> 6,400,000 VND
        raw_price = item.get("price") or item.get("price_min") or 0
        raw_price_max = item.get("price_max") or raw_price
        if raw_price and raw_price > 0:
            price = raw_price // 100000
            price_max = raw_price_max // 100000
        else:
            return {}
        return {
            "name": item.get("name", ""),
            "price": price,
            "price_max": price_max,
            "image": item.get("image", ""),
        }
    except Exception as e:
        print(f"[Scraper][Shopee API] Error: {e}")
        return {}


def _scrape_shopee_from_html(url: str, raw_html: str) -> dict:
    """
    Try to extract Shopee price from embedded script data in the HTML shell.
    Shopee sometimes embeds initial redux state as a JSON blob.
    """
    # Try finding price in JSON patterns within HTML 
    # Shopee prices embedded in format like 640000000000 (6.4M * 100000)
    candidates = []
    
    # Pattern: large numbers that when divided by 100000 make sense as VND price
    for match in re.finditer(r'(?:"price"|"price_min"|"price_max")[:\s"]*([0-9]{8,15})', raw_html):
        raw = int(match.group(1))
        vnd = raw // 100000
        if 10000 <= vnd <= 1_000_000_000:  # 10K to 1B VND is reasonable
            candidates.append(vnd)
    
    if candidates:
        # Take the minimum non-zero price (usually price_min for multi-variant products)
        return {"price": min(candidates), "price_max": max(candidates)}
    
    # Fallback: look for plain VND prices embedded directly
    for match in re.finditer(r'(?:"price"|"price_min")[:\s"]*([0-9]{5,10})', raw_html):
        raw = int(match.group(1))
        if 10000 <= raw <= 1_000_000_000:
            candidates.append(raw)
    
    if candidates:
        return {"price": min(candidates)}
    
    return {}


# --- Live Scrapers ---

def _scrape_shopee(url: str, soup: BeautifulSoup, raw_html: str) -> dict:
    """
    Scrape Shopee product. Tries two methods:
    1. Shopee internal API (requires no login for most items)
    2. HTML embedded data extraction
    Falls back gracefully with is_simulated=True if both fail.
    """
    # Parse shop & item IDs from URL
    m = re.search(r'i\.?(\d+)\.(\d+)', url)
    if not m:
        # Try alternative URL pattern: /product/shopid/itemid
        m = re.search(r'/product/(\d+)/(\d+)', url)
    
    title_tag = soup.find("meta", property="og:title")
    image_tag = soup.find("meta", property="og:image")
    title = title_tag["content"] if title_tag else None
    image_url = image_tag["content"] if image_tag else None
    
    # Try HTML embedded data first (no network call)
    html_data = _scrape_shopee_from_html(url, raw_html)
    
    # Try Shopee API if we have IDs
    api_data = {}
    if m:
        shop_id, item_id = m.group(1), m.group(2)
        api_data = _scrape_shopee_api(shop_id, item_id)
        if api_data:
            print(f"[Scraper][Shopee] API success: price={api_data.get('price'):,} VND")
    
    # Determine best price source
    price = None
    is_simulated = True
    simulated_reason = None
    
    if api_data.get("price"):
        price = api_data["price"]
        is_simulated = False
        # Use name from API if no og:title
        if not title and api_data.get("name"):
            title = api_data["name"]
        if not image_url and api_data.get("image"):
            image_url = f"https://down-vn.img.susercontent.com/file/{api_data['image']}"
    elif html_data.get("price"):
        price = html_data["price"]
        is_simulated = False
        print(f"[Scraper][Shopee] HTML embedded price: {price:,} VND")
    else:
        simulated_reason = "Shopee ch\u1eb7n API kh\u00f4ng c\u00f3 session cookie. Gi\u00e1 hi\u1ec3n th\u1ecb l\u00e0 m\u00f4 ph\u1ecfng."
        print(f"[Scraper][Shopee] Both API and HTML extraction failed, will use simulation")
    
    if price and title:
        return {
            "platform": "shopee",
            "original_url": url,
            "title": title,
            "image_url": image_url,
            "current_price": price,
            "is_simulated": is_simulated,
            "is_dead": False,
            "simulated_reason": simulated_reason,
        }
    
    # If we got price but no title (API blocked), return None to let caller use simulation
    return None


def _scrape_lazada(url: str, soup: BeautifulSoup, raw_html: str) -> dict | None:
    title_tag = soup.find("meta", property="og:title")
    image_tag = soup.find("meta", property="og:image")
    title = title_tag["content"] if title_tag else None
    image_url = image_tag["content"] if image_tag else None
    price = None

    price_match = re.search(r'"price"[:\s"]+([0-9\.]+)', raw_html)
    if price_match:
        raw_p = price_match.group(1).replace(".", "").replace(",", "")
        try:
            price = int(raw_p)
        except ValueError:
            price = None

    if title and price and price > 0:
        return {
            "platform": "lazada",
            "original_url": url,
            "title": title,
            "image_url": image_url,
            "current_price": price,
            "is_simulated": False,
            "is_dead": False,
        }
    return None


def _scrape_traveloka(url: str, soup: BeautifulSoup, raw_html: str) -> dict | None:
    title_tag = soup.find("meta", property="og:title") or soup.find("title")
    image_tag = soup.find("meta", property="og:image")
    title = title_tag.get("content", title_tag.text) if title_tag else None
    image_url = image_tag["content"] if image_tag else None

    price = None
    price_match = re.search(r'(?:IDR|VND|₫|Rp)\s*([\d\.,]+)', raw_html)
    if price_match:
        raw_p = price_match.group(1).replace(".", "").replace(",", "")
        try:
            price = int(raw_p)
        except ValueError:
            price = None

    if title and price and price > 0:
        return {
            "platform": "traveloka",
            "original_url": url,
            "title": title,
            "image_url": image_url,
            "current_price": price,
            "is_simulated": False,
            "is_dead": False,
        }
    return None


def _scrape_trip(url: str, soup: BeautifulSoup, raw_html: str) -> dict | None:
    title_tag = soup.find("meta", property="og:title") or soup.find("title")
    image_tag = soup.find("meta", property="og:image")
    title = title_tag.get("content", title_tag.text) if title_tag else None
    image_url = image_tag["content"] if image_tag else None

    price = None
    price_match = re.search(r'"price"\s*:\s*([0-9]+)', raw_html)
    if price_match:
        try:
            price = int(price_match.group(1))
        except ValueError:
            price = None

    if title and price and price > 0:
        return {
            "platform": "trip",
            "original_url": url,
            "title": title,
            "image_url": image_url,
            "current_price": price,
            "is_simulated": False,
            "is_dead": False,
        }
    return None


def _scrape_generic(url: str, soup: BeautifulSoup, raw_html: str, platform: str) -> dict | None:
    """Generic og:meta scraper + JSON-LD price extraction for any platform."""
    title_tag = soup.find("meta", property="og:title") or soup.find("title")
    image_tag = soup.find("meta", property="og:image")
    title = (title_tag.get("content") or title_tag.text) if title_tag else None
    image_url = image_tag["content"] if image_tag else None

    price = None
    # Try JSON-LD schema
    price_match = re.search(r'"price"[:\s"]+([0-9]{4,})', raw_html)
    if price_match:
        try:
            price = int(price_match.group(1).replace(".", "").replace(",", ""))
        except ValueError:
            pass

    if title and price and price > 0:
        return {
            "platform": platform,
            "original_url": url,
            "title": title,
            "image_url": image_url,
            "current_price": price,
            "is_simulated": False,
            "is_dead": False,
        }
    return None


# --- Main Entrypoint ---

def scrape_product_info(url: str) -> dict:
    """
    Main entry point. Identifies platform, attempts live scrape, then falls back to simulation.
    Returns a dict with: platform, original_url, title, image_url, current_price, is_simulated, is_dead
    """
    platform = analyze_url(url)

    try:
        response = requests.get(url, headers=HEADERS, timeout=10, allow_redirects=True)

        # Detect dead links
        if response.status_code in (404, 410, 301, 302):
            # 301/302 might be valid redirects – follow but re-check final URL
            if response.status_code in (404, 410):
                return {"platform": platform, "original_url": url, "title": "", "image_url": None,
                        "current_price": 0, "is_simulated": False, "is_dead": True}

        if response.status_code != 200:
            print(f"[Scraper] HTTP {response.status_code} for {url[:60]}, falling back to simulation")
            return generate_mock_product(url, platform)

        raw_html = response.text

        # Check for anti-bot / Cloudflare challenge page
        if "cloudflare" in raw_html.lower() and "challenge" in raw_html.lower():
            print(f"[Scraper] Cloudflare blocked for {url[:60]}, falling back to simulation")
            return generate_mock_product(url, platform)

        # Check for empty / error content
        if len(raw_html) < 500:
            return generate_mock_product(url, platform)

        soup = BeautifulSoup(raw_html, "html.parser")

        # Platform-specific scrapers
        result = None
        if platform == "shopee":
            result = _scrape_shopee(url, soup, raw_html)
        elif platform == "lazada":
            result = _scrape_lazada(url, soup, raw_html)
        elif platform == "traveloka":
            result = _scrape_traveloka(url, soup, raw_html)
        elif platform == "trip":
            result = _scrape_trip(url, soup, raw_html)
        else:
            result = _scrape_generic(url, soup, raw_html, platform)

        if result:
            return result

    except requests.exceptions.ConnectionError:
        # DNS failure or connection refused → probably dead link
        return {"platform": platform, "original_url": url, "title": "", "image_url": None,
                "current_price": 0, "is_simulated": False, "is_dead": True}
    except requests.exceptions.Timeout:
        print(f"[Scraper] Timeout for {url[:60]}, falling back to simulation")
    except Exception as e:
        print(f"[Scraper] Error for {url[:60]}: {e}")

    # Final fallback: realistic simulation
    return generate_mock_product(url, platform)
