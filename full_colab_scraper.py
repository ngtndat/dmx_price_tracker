# ==============================================================================
# FULL DMX & ALL 8 SITES LG AIR PURIFIER SCRAPER (Google Colab Version)
# ==============================================================================
# HƯỚNG DẪN CHẠY TRÊN GOOGLE COLAB:
#
# BƯỚC 1: Copy toàn bộ nội dung mã này dán vào một Cell mới trong Google Colab.
#
# BƯỚC 2: Điền các thông tin cấu hình bên dưới (Google Sheet URL, Telegram).
#
# BƯỚC 3: Chạy Cell (Play) → Xác thực Google 1 lần → Chọn chạy ngay hoặc theo lịch.
# ==============================================================================

# ==============================================================================
# CẤU HÌNH THÔNG TIN CỦA BẠN
# ==============================================================================
# 1. Dán đường dẫn file Google Sheet của bạn vào đây (Bắt buộc phải có quyền ghi):
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/XXXXXXXXXX/edit"

# 2. Tên Sheet (tab) bạn muốn ghi dữ liệu (Ví dụ: "Sheet1" hoặc "Trang_tinh_1"):
SHEET_NAME = "Sheet1"

# 3. Telegram Bot Token (để gửi thông báo sau mỗi lần quét):
TELEGRAM_BOT_TOKEN = "8935294463:AAFYtP6V2ASWaB9Dc7u9Ql2l8NIOnCp4jvQ"

# 4. Telegram Chat ID (ID của bạn hoặc nhóm nhận thông báo):
TELEGRAM_CHAT_ID = "5226929253"

# 5. Khung giờ tự động quét (giờ Việt Nam GMT+7):
#    Định dạng: [(giờ, phút), ...]
SCHEDULE_TIMES = [(7, 0), (9, 30), (12, 0), (16, 0), (20, 0)]

# 6. Chụp ảnh Sheet gửi Telegram (có thể để rỗng "" để bỏ qua):
#    Ví dụ: "A1:I30" sẽ chụp từ cột A hàng 1 đến cột I hàng 30.
SCREENSHOT_RANGE = "A1:I30"

# ==============================================================================

import requests
from bs4 import BeautifulSoup
import time
import sys
import io
import json
import re
import urllib3
from datetime import datetime, timedelta, timezone

# Suppress insecure request warnings (for verify=False)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Múi giờ Việt Nam
TZ_VN = timezone(timedelta(hours=7))

# Cache xác thực Google Sheets (chỉ xác thực 1 lần/runtime)
_gc_session = None

import gspread
import os

# Headers for HTTP requests
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9,vi;q=0.8"
}

def clean_price(price_str):
    if not price_str:
        return "0"
    cleaned = price_str.replace("₫", "").replace(".", "").replace("\xa0", "").replace("đ", "").strip()
    cleaned = "".join(c for c in cleaned if c.isdigit())
    return cleaned if cleaned else "0"

def format_price(val_str):
    if not val_str or val_str == "N/A" or val_str == "0":
        return "N/A"
    try:
        val = int(float(val_str.replace("₫", "").replace(".", "").replace("\xa0", "").replace("đ", "").strip()))
        return f"{val:,}".replace(",", ".") + "₫"
    except ValueError:
        return val_str

def format_price_thousands(val_str):
    if not val_str or val_str == "N/A" or val_str == "0":
        return "N/A"
    cleaned = clean_price(val_str)
    try:
        val = int(cleaned)
        return str(val // 1000)
    except ValueError:
        return val_str

def extract_model_code(name, url):
    known_codes = [
        "AS60GHWG0", "AS10GDBY0", "AS65GDBY0", "AS55GGSY0", "FS15GPBK0", "FS15GPCJ0",
        "AS20GPWU0", "AS20GPBK0", "AS20GSHU0", "MD16GQSE0", "MD19GQGE0", "DD20GMWE1", "DD23GMWE1"
    ]
    combined = f"{name} {url}".upper()
    for code in known_codes:
        if code in combined:
            return code
    if "AERO SPEAKER" in combined or "AEROSPEAKER" in combined:
        return "AS20GSHU0"
    pattern = r"\b([a-zA-Z]{2}[0-9]{2}[a-zA-Z0-9]{5})\b"
    match = re.search(pattern, combined)
    if match:
        return match.group(1).upper()
    return "N/A"

def clean_text(text):
    if not text:
        return ""
    return " ".join(text.split())

# ==============================================================================
# 1. DIEN MAY XANH SCRAPER (DMX)
# ==============================================================================
def parse_dmx_detail(url, category_selling_price="0", category_mrp_price="0"):
    try:
        response = requests.get(url, headers=HEADERS, verify=False, timeout=15)
        if response.status_code == 404:
            return {"Status": "sản phẩm bỏ mẫu", "MRP": "N/A", "Selling": "N/A", "Promotions": "N/A"}
        elif response.status_code != 200:
            return {"Status": "Error", "MRP": format_price(category_mrp_price), "Selling": format_price(category_selling_price), "Promotions": f"Lỗi HTTP {response.status_code}"}
            
        soup = BeautifulSoup(response.text, "html.parser")
        is_discontinued = "ngừng kinh doanh" in response.text.lower() or "ngung kinh doanh" in response.text.lower() or "không kinh doanh" in response.text.lower()
            
        selling_price = "0"
        box_price_present = soup.find(class_="box-price-present")
        bs_price = soup.find(class_="bs_price")
        
        if box_price_present:
            selling_price = clean_price(box_price_present.text)
        elif bs_price and bs_price.find('strong'):
            selling_price = clean_price(bs_price.find('strong').text)
        else:
            price_one = soup.find(class_="price-one")
            if price_one:
                strong_price = price_one.find(class_="box-price-present")
                selling_price = clean_price(strong_price.text) if strong_price else clean_price(price_one.text)
            else:
                price_strong = soup.find("strong", class_="price")
                if price_strong:
                    selling_price = clean_price(price_strong.text)
                    
        if (selling_price == "0" or not selling_price) and category_selling_price != "0":
            selling_price = category_selling_price
            
        mrp_price = "0"
        box_price_old = soup.find(class_="box-price-old")
        if box_price_old:
            mrp_price = clean_price(box_price_old.text)
        elif bs_price and bs_price.find('em'):
            mrp_price = clean_price(bs_price.find('em').text)
        else:
            price_old = soup.find(class_="price-old")
            if price_old:
                mrp_price = clean_price(price_old.text)
                
        if (mrp_price == "0" or not mrp_price) and category_mrp_price != "0":
            mrp_price = category_mrp_price
        if mrp_price == "0" or not mrp_price:
            mrp_price = selling_price
            
        if is_discontinued:
            selling_price = "N/A"
            mrp_price = "N/A"
            
        promo_list = []
        promo_block = soup.find(class_="block-price1")
        if promo_block:
            title_promo = promo_block.find(class_="pr-txtb")
            summary_title = clean_text(title_promo.text) if title_promo else ""
            if summary_title:
                promo_list.append(summary_title)
            divb_items = promo_block.find_all(class_="divb")
            for idx, item in enumerate(divb_items, 1):
                item_text = clean_text(item.text)
                if item_text.startswith(str(idx)):
                    item_text = item_text[len(str(idx)):].strip()
                promo_list.append(f"{idx}. {item_text}")
        else:
            promo_divs = soup.find_all(class_=lambda x: x and any(w in x for w in ["promo", "gift", "policy-promo"]))
            for p_div in promo_divs:
                txt = clean_text(p_div.text)
                if txt and txt not in promo_list:
                    promo_list.append(txt)
                    
        promotions = " | ".join(promo_list) if promo_list else "Không có chương trình khuyến mãi riêng biệt."
        
        return {
            "Status": "sản phẩm bỏ mẫu" if is_discontinued else "đang kinh doanh",
            "MRP": format_price(mrp_price),
            "Selling": format_price(selling_price),
            "Promotions": promotions
        }
    except Exception as e:
        return {"Status": "Error", "MRP": format_price(category_mrp_price), "Selling": format_price(category_selling_price), "Promotions": f"Lỗi: {e}"}

def scrape_dmx(url="https://www.dienmayxanh.com/may-loc-khong-khi-lg"):
    print(f"\n--- 1. CÀO DIỆN MÁY XANH (DMX) ---")
    try:
        response = requests.get(url, headers=HEADERS, verify=False, timeout=15)
        if response.status_code != 200:
            print(f"[!] Lỗi kết nối DMX: {response.status_code}")
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        list_product_ul = soup.find("ul", class_="listproduct")
        if not list_product_ul:
            return []
        lis = list_product_ul.find_all("li", recursive=False)
        results = []
        for idx, li in enumerate(lis, 1):
            a_tag = li.find("a", class_="main-contain") or li.find("a")
            if not a_tag: continue
            model_name = a_tag.get("data-name") or li.find("p", class_="product-title").text.strip()
            category_selling_price = a_tag.get("data-price", "0")
            category_mrp_price = li.get("data-price", "0")
            relative_link = a_tag.get("href")
            full_link = relative_link if relative_link.startswith("http") else f"https://www.dienmayxanh.com{relative_link}"
            full_link = full_link.split("?")[0]
            
            print(f"[{idx}/{len(lis)}] DMX: {model_name}")
            details = parse_dmx_detail(full_link, category_selling_price, category_mrp_price)
            status = details["Status"]
            if status == "đang kinh doanh":
                item_label = li.find(class_="item-label")
                label_text = clean_text(item_label.text).lower() if item_label else ""
                if "mới" in label_text or "mẫu mới" in label_text:
                    status = "sản phẩm mới"
            results.append({
                "Page Title": "DMX", "Tên Model": model_name, "Status": status, "direct product link": full_link,
                "MRP price": details["MRP"], "Selling price": details["Selling"], "Thông tin chương trình khuyến mãi": details["Promotions"]
            })
            time.sleep(1.5)
        return results
    except Exception as e:
        print(f"[!] Lỗi cào DMX: {e}")
        return []

# ==============================================================================
# 2. DIEN MAY CHO LON SCRAPER (DMCL)
# ==============================================================================
def parse_dmcl_detail(url, category_selling_price="0", category_mrp_price="0"):
    try:
        response = requests.get(url, headers=HEADERS, verify=False, timeout=15)
        if response.status_code == 404:
            return {"Status": "sản phẩm bỏ mẫu", "MRP": "N/A", "Selling": "N/A", "Promotions": "N/A"}
        elif response.status_code != 200:
            return {"Status": "Error", "MRP": format_price(category_mrp_price), "Selling": format_price(category_selling_price), "Promotions": f"Lỗi HTTP {response.status_code}"}
        soup = BeautifulSoup(response.text, "html.parser")
        is_discontinued = "ngừng kinh doanh" in response.text.lower() or "ngung kinh doanh" in response.text.lower() or "không kinh doanh" in response.text.lower()
        
        selling_price = "0"
        price_sale_tag = soup.find(class_="price_sale")
        if price_sale_tag:
            selling_price = clean_price(price_sale_tag.text)
        if (selling_price == "0" or not selling_price) and category_selling_price != "0":
            selling_price = category_selling_price
            
        mrp_price = "0"
        price_market_tag = soup.find(class_="price_market")
        if price_market_tag:
            mrp_price = clean_price(price_market_tag.text)
        if (mrp_price == "0" or not mrp_price) and category_mrp_price != "0":
            mrp_price = category_mrp_price
        if mrp_price == "0" or not mrp_price:
            mrp_price = selling_price
            
        if is_discontinued:
            selling_price = "N/A"
            mrp_price = "N/A"
            
        promo_list = []
        gift_pro = soup.find(class_="gift_pro")
        if gift_pro:
            ttl = gift_pro.find(class_="ttl")
            if ttl:
                promo_list.append(clean_text(ttl.text))
            li_items = gift_pro.find_all("li")
            if li_items:
                for idx, li in enumerate(li_items, 1):
                    p_desc = li.find("p")
                    if p_desc:
                        gift_info = p_desc.find(class_="gift_info")
                        if gift_info: gift_info.decompose()
                        promo_list.append(f"{idx}. {clean_text(p_desc.text)}")
                    else:
                        promo_list.append(f"{idx}. {clean_text(li.text)}")
            else:
                promo_list.append(clean_text(gift_pro.text))
        else:
            gift_detail = soup.find(class_="gift_detail")
            if gift_detail:
                promo_list.append(clean_text(gift_detail.text))
                
        promotions = " | ".join(promo_list) if promo_list else "Không có chương trình khuyến mãi riêng biệt."
        return {
            "Status": "sản phẩm bỏ mẫu" if is_discontinued else "đang kinh doanh",
            "MRP": format_price(mrp_price), "Selling": format_price(selling_price), "Promotions": promotions
        }
    except Exception as e:
        return {"Status": "Error", "MRP": format_price(category_mrp_price), "Selling": format_price(category_selling_price), "Promotions": f"Lỗi: {e}"}

def scrape_dmcl(url="https://dienmaycholon.com/may-loc-khong-khi-lg"):
    print(f"\n--- 2. CÀO ĐIỆN MÁY CHỢ LỚN (DMCL) ---")
    try:
        response = requests.get(url, headers={**HEADERS, "Referer": "https://dienmaycholon.com"}, verify=False, timeout=15)
        if response.status_code != 200:
            print(f"[!] Lỗi kết nối DMCL: {response.status_code}")
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        products_div = soup.find("div", class_="products")
        if not products_div:
            return []
        items = products_div.find_all("div", class_="product")
        results = []
        for idx, item in enumerate(items, 1):
            name_tag = item.find("a", class_="name_pro")
            model_name = clean_text(name_tag.text) if name_tag else "N/A"
            price_sale = item.find(class_="price_sale")
            category_selling_price = clean_price(price_sale.text) if price_sale else "0"
            price_market = item.find(class_="price_market")
            category_mrp_price = clean_price(price_market.text) if price_market else "0"
            href = name_tag.get("href")
            if not href: continue
            full_link = href if href.startswith("http") else f"https://dienmaycholon.com{href}"
            full_link = full_link.split("?")[0]
            
            print(f"[{idx}/{len(items)}] DMCL: {model_name}")
            details = parse_dmcl_detail(full_link, category_selling_price, category_mrp_price)
            status = details["Status"]
            if status == "đang kinh doanh":
                if "mới" in model_name.lower() or "new" in model_name.lower():
                    status = "sản phẩm mới"
            results.append({
                "Page Title": "DMCL", "Tên Model": model_name, "Status": status, "direct product link": full_link,
                "MRP price": details["MRP"], "Selling price": details["Selling"], "Thông tin chương trình khuyến mãi": details["Promotions"]
            })
            time.sleep(1.5)
        return results
    except Exception as e:
        print(f"[!] Lỗi cào DMCL: {e}")
        return []

# ==============================================================================
# 3. NGUYEN KIM SCRAPER (NK)
# ==============================================================================
def scrape_nk(url="https://www.nguyenkim.com/may-loc-khong-khi-lg"):
    print(f"\n--- 3. CÀO NGUYỄN KIM (NK) ---")
    try:
        response = requests.get(url, headers=HEADERS, verify=False, timeout=15)
        if response.status_code != 200:
            print(f"[!] Lỗi kết nối Nguyễn Kim: {response.status_code}")
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        
        product_renders = soup.find_all("a", class_="product-render")
        print(f"Tìm thấy {len(product_renders)} sản phẩm trên Nguyễn Kim.")
        results = []
        for idx, a in enumerate(product_renders, 1):
            model_name = a.get("aria-label") or clean_text(a.text)
            href = a.get("href")
            full_link = href if href.startswith("http") else f"https://www.nguyenkim.com{href}"
            full_link = full_link.split("?")[0]
            
            selling_price = "0"
            mrp_price = "0"
            sibling = a.next_sibling
            while sibling:
                if sibling.name == "script" and "dataRenderProduct" in sibling.text:
                    match = re.search(r"dataRenderProduct\.push\(\s*({.*?})\s*\);", sibling.text, re.DOTALL)
                    if match:
                        try:
                            p_data = json.loads(match.group(1))
                            selling_price = str(p_data.get("price", "0"))
                            mrp_price = str(p_data.get("list_price", "0"))
                        except Exception:
                            pass
                    break
                sibling = sibling.next_sibling
                
            print(f"[{idx}/{len(product_renders)}] NK: {model_name}")
            results.append({
                "Page Title": "NguyenKim", "Tên Model": model_name, "Status": "đang kinh doanh", "direct product link": full_link,
                "MRP price": format_price(mrp_price), "Selling price": format_price(selling_price), 
                "Thông tin chương trình khuyến mãi": "Xem khuyến mãi tại link sản phẩm."
            })
        return results
    except Exception as e:
        print(f"[!] Lỗi cào Nguyễn Kim: {e}")
        return []

# ==============================================================================
# 4. CELLPHONES SCRAPER (CPS)
# ==============================================================================
def scrape_cps(url="https://cellphones.com.vn/nha-thong-minh/may-loc-khong-khi/lg.html"):
    print(f"\n--- 4. CÀO CELLPHONES (CPS) ---")
    try:
        response = requests.get(url, headers=HEADERS, verify=False, timeout=15)
        if response.status_code != 200:
            print(f"[!] Lỗi kết nối CellphoneS: {response.status_code}")
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.find_all(class_="product-item")
        print(f"Tìm thấy {len(items)} sản phẩm trên CellphoneS.")
        results = []
        for idx, item in enumerate(items, 1):
            name_tag = item.find(class_="product__name")
            model_name = clean_text(name_tag.text) if name_tag else "LG Air Purifier"
            a_link = item.find("a", class_="product__link")
            if not a_link: continue
            href = a_link.get("href")
            full_link = href.split("?")[0]
            
            price_show = item.find(class_="product__price--show")
            selling_price = clean_price(price_show.text) if price_show else "0"
            price_through = item.find(class_="product__price--through")
            mrp_price = clean_price(price_through.text) if price_through else selling_price
            
            status = "đang kinh doanh"
            installment_div = item.find(class_="box-info__installment")
            if installment_div and "mới" in installment_div.text.lower():
                status = "sản phẩm mới"
                
            print(f"[{idx}/{len(items)}] CPS: {model_name}")
            results.append({
                "Page Title": "CellphoneS", "Tên Model": model_name, "Status": status, "direct product link": full_link,
                "MRP price": format_price(mrp_price), "Selling price": format_price(selling_price),
                "Thông tin chương trình khuyến mãi": "Xem khuyến mãi tại link sản phẩm."
            })
        return results
    except Exception as e:
        print(f"[!] Lỗi cào CellphoneS: {e}")
        return []

FPT_PROXIES = []

def scrape_fpt(url="https://fptshop.com.vn/may-loc-khong-khi/lg"):
    global FPT_PROXIES
    print(f"\n--- 5. CÀO FPT SHOP (FPT) ---")
    
    # 1. Fetch proxy list once and reuse it
    if not FPT_PROXIES:
        print("Đang tải danh sách proxy Việt Nam từ API...")
        try:
            proxy_api_url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=6000&country=VN&ssl=all&anonymity=all"
            resp = requests.get(proxy_api_url, timeout=10)
            FPT_PROXIES = [p.strip() for p in resp.text.strip().split("\n") if p.strip()]
            print(f"-> Đã lấy được {len(FPT_PROXIES)} proxy Việt Nam.")
        except Exception as e:
            print(f"[!] Không thể lấy danh sách proxy: {e}")
            FPT_PROXIES = []
            
    if not FPT_PROXIES:
        print("[!] Không có proxy Việt Nam nào. Không thể vượt qua geoblock của FPT Shop.")
        return []

    # 2. Start request with proxy rotation
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8",
    }
    
    for idx, proxy in enumerate(FPT_PROXIES, 1):
        print(f"  [{idx}/{len(FPT_PROXIES)}] Thử cào FPT qua proxy VN: {proxy}...")
        proxies = {
            "http": f"http://{proxy}",
            "https": f"http://{proxy}"
        }
        try:
            response = requests.get(url, headers=headers, proxies=proxies, timeout=8, verify=False)
            
            if response.status_code == 200:
                if "cardInfo" in response.text:
                    print(f"  [Thành công] Đã tải trang FPT Shop thành công qua proxy {proxy}!")
                    soup = BeautifulSoup(response.text, "html.parser")
                    cards = soup.find_all(class_="cardInfo")
                    print(f"Tìm thấy {len(cards)} sản phẩm trên FPT Shop.")
                    results = []
                    
                    for c_idx, card in enumerate(cards, 1):
                        a_tag = card.find("a")
                        if not a_tag: continue
                        model_name = a_tag.get("title") or (card.find("h3").text.strip() if card.find("h3") else "N/A")
                        href = a_tag.get("href")
                        full_link = href if href.startswith("http") else f"https://fptshop.com.vn{href}"
                        full_link = full_link.split("?")[0]
                        
                        price_old = card.find(class_="line-through")
                        mrp_price = clean_price(price_old.text) if price_old else "0"
                        price_new = card.find(class_="text-textOnWhitePrimary")
                        selling_price = clean_price(price_new.text) if price_new else "0"
                        if mrp_price == "0": mrp_price = selling_price
                        
                        promo = card.find(class_="line-clamp-2")
                        promotions = clean_text(promo.text) if promo else "Xem chi tiết khuyến mãi tại link."
                        
                        status = "đang kinh doanh"
                        if "mới" in model_name.lower() or "gen 2" in model_name.lower():
                            status = "sản phẩm mới"
                            
                        print(f"    [{c_idx}/{len(cards)}] FPT: {model_name}")
                        results.append({
                            "Page Title": "FPT", "Tên Model": model_name, "Status": status, "direct product link": full_link,
                            "MRP price": format_price(mrp_price), "Selling price": format_price(selling_price),
                            "Thông tin chương trình khuyến mãi": promotions
                        })
                    return results
                else:
                    print("  [!] Lỗi: Tải trang thành công nhưng Cloudflare captcha hiện diện.")
            else:
                print(f"  [!] Lỗi HTTP: {response.status_code}")
        except Exception as e:
            print(f"  [!] Lỗi kết nối proxy: {e}")
            
    print("[!] Không có proxy Việt Nam nào kết nối thành công tới FPT Shop.")
    return []

# ==============================================================================
# 6. CAO THIEN PHAT SCRAPER (CTP)
# ==============================================================================
def scrape_ctp(url="https://caothienphat.com/danhmuc/thiet-bi-gia-dinh/may-loc-khong-khi/?_brand=lg"):
    print(f"\n--- 6. CÀO CAO THIÊN PHÁT (CTP) ---")
    try:
        response = requests.get(url, headers=HEADERS, verify=False, timeout=15)
        if response.status_code != 200:
            print(f"[!] Lỗi kết nối Cao Thiên Phát: {response.status_code}")
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.find_all(class_="product-small")
        items = [item for item in items if 'col' in item.get('class', [])]
        print(f"Tìm thấy {len(items)} sản phẩm trên Cao Thiên Phát.")
        results = []
        for idx, item in enumerate(items, 1):
            title_p = item.find(class_="woocommerce-loop-product__title")
            if not title_p: continue
            a_link = title_p.find("a")
            if not a_link: continue
            model_name = clean_text(a_link.text)
            href = a_link.get("href")
            full_link = href.split("?")[0]
            
            price_wrapper = item.find(class_="price-wrapper")
            selling_price = "0"
            mrp_price = "0"
            if price_wrapper:
                ins_tag = price_wrapper.find("ins")
                if ins_tag:
                    selling_price = clean_price(ins_tag.text)
                else:
                    price_amount = price_wrapper.find(class_="woocommerce-Price-amount")
                    if price_amount: selling_price = clean_price(price_amount.text)
                del_tag = price_wrapper.find("del")
                if del_tag:
                    mrp_price = clean_price(del_tag.text)
                else:
                    mrp_price = selling_price
            
            print(f"[{idx}/{len(items)}] CTP: {model_name}")
            results.append({
                "Page Title": "CaoThienPhat", "Tên Model": model_name, "Status": "đang kinh doanh", "direct product link": full_link,
                "MRP price": format_price(mrp_price), "Selling price": format_price(selling_price),
                "Thông tin chương trình khuyến mãi": "Xem khuyến mãi tại link sản phẩm."
            })
        return results
    except Exception as e:
        print(f"[!] Lỗi cào Cao Thiên Phát: {e}")
        return []

# ==============================================================================
# 7. MEDIAMART SCRAPER
# ==============================================================================
def scrape_mediamart(url="https://mediamart.vn/may-loc-khong-khi-lg?a=5585"):
    print(f"\n--- 7. CÀO MEDIAMART ---")
    try:
        response = requests.get(url, headers=HEADERS, verify=False, timeout=15)
        if response.status_code != 200:
            print(f"[!] Lỗi kết nối MediaMart: {response.status_code}")
            return []
        soup = BeautifulSoup(response.text, "html.parser")
        items = soup.find_all("a", class_="product-item")
        print(f"Tìm thấy {len(items)} sản phẩm trên MediaMart.")
        results = []
        seen_links = set()
        for idx, item in enumerate(items, 1):
            href = item.get("href")
            if not href: continue
            full_link = href if href.startswith("http") else f"https://mediamart.vn{href}"
            full_link = full_link.split("?")[0]
            
            # Bỏ qua các thẻ trùng URL (thường do MediaMart bao gồm cả ảnh và tên trong 2 thẻ a riêng biệt)
            if full_link in seen_links:
                continue
            seen_links.add(full_link)
            
            title_p = item.find(class_="product-name")
            model_name = clean_text(title_p.text) if title_p else "LG Air Purifier"
            
            price_sale = item.find(class_="product-price")
            selling_price = clean_price(price_sale.text) if price_sale else "0"
            price_regular = item.find(class_="product-price-regular")
            mrp_price = clean_price(price_regular.text) if price_regular else selling_price
            
            print(f"[{idx}/{len(items)}] MediaMart: {model_name}")
            results.append({
                "Page Title": "MediaMart", "Tên Model": model_name, "Status": "đang kinh doanh", "direct product link": full_link,
                "MRP price": format_price(mrp_price), "Selling price": format_price(selling_price),
                "Thông tin chương trình khuyến mãi": "Xem khuyến mãi tại link sản phẩm."
            })
        return results
    except Exception as e:
        print(f"[!] Lỗi cào MediaMart: {e}")
        return []

# ==============================================================================
# 8. HC SCRAPER (Sitemap + Parse trang chi tiết tĩnh)
# ==============================================================================
def fetch_with_proxy(url, proxies_list, min_length=1000):
    """Fetch URL qua proxy xoay vòng Việt Nam (dùng cho Google Colab bị geoblock)."""
    for proxy in proxies_list:
        try:
            r = requests.get(url, headers=HEADERS,
                             proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"},
                             timeout=12, verify=False)
            if r.status_code == 200 and len(r.text) > min_length:
                return r
        except Exception:
            pass
    return None

def scrape_hc(url="https://hc.com.vn/ords/cat/loc-khong-khi/lg"):
    global FPT_PROXIES
    print(f"\n--- 8. CÀO HỆ THỐNG HC (Sitemap) ---")
    
    # Xác định keyword lọc sản phẩm từ URL danh mục
    # vd: /loc-khong-khi/lg -> ["loc-khong-khi", "lg"], /may-hut-am/lg -> ["may-hut-am", "lg"]
    url_parts = url.rstrip("/").split("/ords/cat/")[-1].split("/")
    sitemap_keywords = [p for p in url_parts if p]
    
    # --- Hàm fetch: ưu tiên trực tiếp, fallback proxy ---
    def smart_fetch(target_url, min_len=1000):
        # Thử trực tiếp trước (nếu máy ở VN)
        try:
            r = requests.get(target_url, headers=HEADERS, timeout=12, verify=False)
            if r.status_code == 200 and len(r.text) > min_len:
                return r
        except Exception:
            pass
        # Fallback: dùng proxy VN
        if FPT_PROXIES:
            return fetch_with_proxy(target_url, FPT_PROXIES, min_len)
        return None
    
    # Bước 1: Tải sitemap.xml để lấy TẤT CẢ URL sản phẩm
    print("  Đang tải sitemap.xml (~3MB)...")
    sitemap_resp = smart_fetch("https://hc.com.vn/sitemap.xml", min_len=10000)
    if not sitemap_resp:
        print("  [!] Không tải được sitemap.xml. Bỏ qua HC.")
        return []
    
    # Bước 2: Trích xuất URL sản phẩm khớp keyword
    all_product_urls = set()
    for match in re.findall(r'<loc>(https://hc\.com\.vn/ords/product/[^<]+)</loc>', sitemap_resp.text):
        slug = match.split("/")[-1].lower()
        # Kiểm tra slug chứa tất cả keyword (vd: "loc-khong-khi" AND "lg")
        if all(kw.lower() in slug for kw in sitemap_keywords):
            all_product_urls.add(match)
    
    product_urls = sorted(all_product_urls)
    print(f"  -> Tìm thấy {len(product_urls)} sản phẩm trong sitemap.")
    
    if not product_urls:
        print("  [!] Không tìm thấy sản phẩm HC nào khớp. Bỏ qua.")
        return []
    
    # Bước 3: Vào từng trang chi tiết, parse dữ liệu tĩnh
    print(f"  Đang cào {len(product_urls)} trang chi tiết...\n")
    results = []
    for idx, prod_url in enumerate(product_urls, 1):
        slug = prod_url.split("/")[-1]
        
        detail_resp = smart_fetch(prod_url, min_len=1000)
        if not detail_resp:
            print(f"    [{idx}/{len(product_urls)}] {slug}... FAILED")
            continue
        
        detail_soup = BeautifulSoup(detail_resp.text, "html.parser")
        
        # Parse AVP List (Attribute-Value Pair) của Oracle APEX
        avp_labels = detail_soup.find_all(class_="t-AVPList-label")
        avp_values = detail_soup.find_all(class_="t-AVPList-value")
        attrs = {}
        for lbl, val in zip(avp_labels, avp_values):
            label_text = clean_text(lbl.text).strip().rstrip(":")
            value_text = clean_text(val.text).strip()
            attrs[label_text] = value_text

        model_name = attrs.get("Tên", "N/A")
        model_code = attrs.get("Model", "N/A")
        status_raw = attrs.get("Trạng thái", "").lower()
        
        if "hết hàng" in status_raw or "tạm hết" in status_raw:
            status = "Hết hàng"
        elif "ngừng" in status_raw:
            status = "ngừng kinh doanh"
        else:
            status = "đang kinh doanh"

        sale_elem = detail_soup.find(class_="hc_sale_price")
        selling_price = clean_price(sale_elem.text) if sale_elem else "0"

        supp_elem = detail_soup.find(class_="hc_supp_price")
        mrp_price = clean_price(supp_elem.text) if supp_elem else selling_price

        print(f"    [{idx}/{len(product_urls)}] HC: {model_code} | {status} | Giá: {format_price(selling_price)}")
        
        results.append({
            "Page Title": "HC", "Tên Model": model_name, "Status": status,
            "direct product link": prod_url,
            "MRP price": format_price(mrp_price), "Selling price": format_price(selling_price),
            "Thông tin chương trình khuyến mãi": "Xem khuyến mãi tại link sản phẩm."
        })
        
        time.sleep(0.3)
    
    print(f"  -> HC hoàn tất: {len(results)} sản phẩm.")
    return results

# ==============================================================================
# TELEGRAM NOTIFIER
# ==============================================================================
def send_telegram_summary(all_data, source_counts, next_run_str=None, error_msg=None):
    """Gửi thông báo tóm tắt kết quả quét lên Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("[!] Chưa cấu hình Telegram. Bỏ qua gửi thông báo.")
        return
    
    now_str = datetime.now(TZ_VN).strftime("%d/%m/%Y %H:%M:%S")
    
    if error_msg:
        msg = (
            f"❌ <b>QUÉT THẤT BẠI - MÁY LỌC KK & MÁY HÚT ẨM LG</b>\n"
            f"📅 <i>Thời gian: {now_str} (GMT+7)</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"⚠️ Lỗi: {error_msg}\n"
        )
    else:
        total = len(all_data)
        msg = (
            f"✅ <b>QUÉT HOÀN TẤT - MÁY LỌC KK & MÁY HÚT ẨM LG</b>\n"
            f"📅 <i>Thời gian: {now_str} (GMT+7)</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 <b>Tổng sản phẩm:</b> {total} sp\n"
            f"🔢 <b>Chi tiết theo nguồn:</b>\n"
        )
        source_icons = {
            "DMX": "🟢", "DMCL": "🔵", "NguyenKim": "🟡",
            "CellphoneS": "🟠", "FPT": "🔴", "CaoThienPhat": "🟣",
            "MediaMart": "⚪", "HC": "🟤"
        }
        for src, count in source_counts.items():
            icon = source_icons.get(src, "▪️")
            msg += f"  {icon} {src}: <b>{count}</b> sp\n"
        msg += f"📋 <b>Google Sheet:</b> <a href='{SPREADSHEET_URL}'>Xem tại đây</a>\n"
    
    if next_run_str:
        msg += f"━━━━━━━━━━━━━━━━━━━━━━━━━\n⏰ <b>Lần quét tiếp theo:</b> {next_run_str}\n"
    
    msg += "🤖 <i>Antigravity Price Tracker</i>"
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        res = requests.post(url, json=payload, timeout=12)
        if res.status_code == 200:
            print("[OK] Đã gửi thông báo Telegram thành công!")
        else:
            print(f"[!] Telegram API lỗi {res.status_code}: {res.text}")
    except Exception as e:
        print(f"[!] Không thể gửi Telegram: {e}")


# ==============================================================================
# SHEET SCREENSHOT → TELEGRAM (Chụp ảnh vùng ô và gửi Telegram)
# ==============================================================================
def send_sheet_screenshot_telegram(gc):
    """Đọc dữ liệu từ SCREENSHOT_RANGE, render thành ảnh bảng PNG, gửi Telegram."""
    if not SCREENSHOT_RANGE or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import io as _io
        
        print(f"\n--- CHỤP ẢNH SHEET [{SCREENSHOT_RANGE}] GỬi TELEGRAM ---")
        
        # Lấy dữ liệu từ Google Sheets
        sh = gc.open_by_url(SPREADSHEET_URL)
        try:
            sheet = sh.worksheet(SHEET_NAME)
        except Exception:
            sheet = sh.get_worksheet(0)
        
        raw = sheet.get(SCREENSHOT_RANGE)
        if not raw:
            print("[!] Không có dữ liệu trong vùng ô này.")
            return
        
        # Chuẩn hóa số cột
        max_cols = max(len(r) for r in raw)
        data = [r + [''] * (max_cols - len(r)) for r in raw]
        
        headers = data[0] if data else []
        rows    = data[1:] if len(data) > 1 else [[''] * max_cols]
        
        # Tạo hình
        fig_w = max(14, max_cols * 2.0)
        fig_h = max(3, len(rows) * 0.45 + 1.2)
        fig, ax = plt.subplots(figsize=(fig_w, fig_h))
        ax.axis('off')
        ax.set_facecolor('#FAFAFA')
        fig.patch.set_facecolor('#FAFAFA')
        
        tbl = ax.table(
            cellText=rows,
            colLabels=headers,
            loc='center',
            cellLoc='center'
        )
        tbl.auto_set_font_size(False)
        tbl.set_fontsize(8)
        tbl.scale(1, 1.7)
        
        # Header style (xám đậm)
        for j in range(max_cols):
            cell = tbl[0, j]
            cell.set_facecolor('#1E3A5F')
            cell.set_text_props(color='white', fontweight='bold', fontsize=8)
            cell.set_edgecolor('#FFFFFF')
        
        # Hàng alternating
        for i in range(len(rows)):
            bg = '#E8F0FE' if i % 2 == 0 else '#FFFFFF'
            for j in range(max_cols):
                cell = tbl[i + 1, j]
                cell.set_facecolor(bg)
                cell.set_edgecolor('#CCCCCC')
        
        now_str = datetime.now(TZ_VN).strftime("%d/%m/%Y %H:%M")
        plt.title(
            f"📅 Dữ liệu Máy Lọc KK & Máy Hút Ẩm LG — {now_str} (GMT+7)",
            fontsize=10, fontweight='bold', pad=12, color='#1E3A5F'
        )
        
        # Lưu vào buffer
        buf = _io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=150, facecolor='#FAFAFA')
        buf.seek(0)
        plt.close(fig)
        
        # Gửi lên Telegram
        tg_caption = (
            f"📊 <b>Snapshot dữ liệu Sheet</b>\n"
            f"🔍 Vùng ô: <code>{SCREENSHOT_RANGE}</code>  |  Tab: <code>{SHEET_NAME}</code>\n"
            f"📅 {now_str} (GMT+7)"
        )
        send_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        files   = {'photo': ('sheet_snapshot.png', buf, 'image/png')}
        payload = {'chat_id': TELEGRAM_CHAT_ID, 'caption': tg_caption, 'parse_mode': 'HTML'}
        res = requests.post(send_url, files=files, data=payload, timeout=30)
        
        if res.status_code == 200:
            print(f"[OK] Đã gửi ảnh snapshot Sheet ({SCREENSHOT_RANGE}) lên Telegram!")
        else:
            print(f"[!] Telegram sendPhoto lỗi {res.status_code}: {res.text[:200]}")
    
    except Exception as e:
        print(f"[!] Không thể chụp/gửi ảnh Sheet: {e}")


# ==============================================================================
# GOOGLE SHEETS AUTH (Cache session - chỉ xác thực 1 lần/runtime)
# ==============================================================================
def get_gc():
    """Trả về gspread client. Xác thực 1 lần, cache cho các lần sau."""
    global _gc_session
    if _gc_session is not None:
        print("[OK] Dùng lại phiên xác thực Google Sheets đã có.")
        return _gc_session
    
    print("--- XÁC THỰC GOOGLE SHEETS (chỉ cần làm 1 lần) ---")
    gc = None
    
    # Phương thức 1: Biến môi trường (GitHub Actions / Colab Secret)
    env_creds = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON")
    if env_creds:
        try:
            print("Đang xác thực qua biến môi trường GOOGLE_SERVICE_ACCOUNT_JSON...")
            creds_dict = json.loads(env_creds)
            gc = gspread.service_account_from_dict(creds_dict)
            print("[OK] Xác thực qua biến môi trường thành công!")
        except Exception as e:
            print(f"[!] Lỗi: {e}")
    
    # Phương thức 2: File credentials cục bộ
    if not gc:
        for cred_file in ["credentials.json", "service_account.json", "secret.json"]:
            if os.path.exists(cred_file):
                try:
                    print(f"Đang xác thực qua file '{cred_file}'...")
                    gc = gspread.service_account(filename=cred_file)
                    print("[OK] Xác thực qua file credentials thành công!")
                    break
                except Exception as e:
                    print(f"[!] Lỗi khi đọc file {cred_file}: {e}")
    
    # Phương thức 3: Google Colab OAuth (popup 1 lần duy nhất)
    if not gc:
        try:
            print("Đang xác thực qua tài khoản Google Colab (sẽ hiện popup 1 lần)...")
            from google.colab import auth
            from google.auth import default
            auth.authenticate_user()
            creds, _ = default()
            gc = gspread.authorize(creds)
            print("[OK] Xác thực qua Google Colab thành công!")
        except Exception as e:
            print(f"[!] Lỗi xác thực Colab: {e}")
    
    if not gc:
        print("[!] Không thể xác thực. Kiểm tra lại cấu hình.")
        return None
    
    _gc_session = gc
    return gc


# ==============================================================================
# CORE JOB: Chạy 1 lần quét + ghi sheet + gửi telegram
# ==============================================================================
def run_scraper_job(gc, next_run_str=None):
    """Thực hiện 1 lần quét toàn bộ, ghi vào Google Sheet, gửi Telegram."""
    print("\n" + "="*70)
    print(f"🚀 BẮT ĐẦU QUÉT - {datetime.now(TZ_VN).strftime('%d/%m/%Y %H:%M:%S')} (GMT+7)")
    print("="*70)
    
    all_data = []
    source_counts = {}
    
    def run_and_count(scrape_fn, *args, label=None):
        results = scrape_fn(*args)
        src = results[0]["Page Title"] if results else (label or "Unknown")
        source_counts[src] = source_counts.get(src, 0) + len(results)
        all_data.extend(results)
    
    # --- PHẦN 1: MÁY LỌC KHÔNG KHÍ LG ---
    print("\n==================== QUÉT MÁY LỌC KHÔNG KHÍ LG ====================")
    run_and_count(scrape_dmx, "https://www.dienmayxanh.com/may-loc-khong-khi-lg")
    run_and_count(scrape_dmcl, "https://dienmaycholon.com/may-loc-khong-khi-lg")
    run_and_count(scrape_nk, "https://www.nguyenkim.com/may-loc-khong-khi-lg")
    run_and_count(scrape_cps, "https://cellphones.com.vn/nha-thong-minh/may-loc-khong-khi/lg.html")
    run_and_count(scrape_fpt, "https://fptshop.com.vn/may-loc-khong-khi/lg")
    run_and_count(scrape_ctp, "https://caothienphat.com/danhmuc/thiet-bi-gia-dinh/may-loc-khong-khi/?_brand=lg")
    run_and_count(scrape_mediamart, "https://mediamart.vn/may-loc-khong-khi-lg?a=5585")
    run_and_count(scrape_hc, "https://hc.com.vn/ords/cat/loc-khong-khi/lg")
    
    # --- PHẦN 2: MÁY HÚT ẨM LG ---
    print("\n==================== QUÉT MÁY HÚT ẨM LG ====================")
    run_and_count(scrape_dmx, "https://www.dienmayxanh.com/may-hut-am-lg?itm_source=trang-nganh-hang&itm_medium=filter")
    run_and_count(scrape_nk, "https://www.nguyenkim.com/may-hut-am-lg/")
    run_and_count(scrape_cps, "https://cellphones.com.vn/do-gia-dung/may-hut-am/lg.html")
    run_and_count(scrape_fpt, "https://fptshop.com.vn/may-hut-am/lg")
    run_and_count(scrape_mediamart, "https://mediamart.vn/may-hut-am-lg")
    run_and_count(scrape_hc, "https://hc.com.vn/ords/cat/may-hut-am/lg")
    
    if not all_data:
        print("[!] Không thu thập được dữ liệu nào.")
        send_telegram_summary([], {}, next_run_str, error_msg="Không thu thập được dữ liệu nào từ tất cả các trang.")
        return
    
    print(f"\n[OK] Thu được {len(all_data)} sản phẩm từ {len(source_counts)} nguồn.")
    
    # Ghi lên Google Sheets
    print("\n--- XUẤT DỮ LIỆU LÊN GOOGLE SHEET ---")
    try:
        sh = gc.open_by_url(SPREADSHEET_URL)
        try:
            sheet = sh.worksheet(SHEET_NAME)
        except Exception:
            sheet = sh.get_worksheet(0)
        
        print(f"Đang ghi vào tab '{sheet.title}'...")
        values = sheet.get_all_values()
        has_header = len(values) > 0
        
        headers = ["Giờ quét", "Page Title", "Mã Model", "Tên Model", "Status",
                   "direct product link", "MRP price", "Selling price",
                   "Thông tin chương trình khuyến mãi"]
        rows_to_append = []
        if not has_header:
            rows_to_append.append(headers)
        
        current_time = datetime.now(TZ_VN).strftime('%Y-%m-%d %H:%M:%S')
        for row in all_data:
            model_name = row["Tên Model"]
            prod_link = row["direct product link"]
            model_code = extract_model_code(model_name, prod_link)
            rows_to_append.append([
                current_time,
                row["Page Title"],
                model_code,
                model_name,
                row["Status"],
                prod_link,
                format_price_thousands(row["MRP price"]),
                format_price_thousands(row["Selling price"]),
                row["Thông tin chương trình khuyến mãi"]
            ])
        
        sheet.append_rows(rows_to_append, value_input_option='USER_ENTERED')
        print("\n" + "="*70)
        print("[THÀNH CÔNG] Dữ liệu đã được ghi vào Google Sheet!")
        print(f"👉 {SPREADSHEET_URL}")
        print("="*70)
        
        # Gửi thông báo tóm tắt
        send_telegram_summary(all_data, source_counts, next_run_str)
        # Gửi ảnh chụp Sheet
        send_sheet_screenshot_telegram(gc)
        
    except Exception as e:
        err = f"Lỗi ghi Google Sheets: {e}"
        print(f"[!] {err}")
        send_telegram_summary(all_data, source_counts, next_run_str, error_msg=err)


# ==============================================================================
# SCHEDULER: Chạy tự động theo khung giờ
# ==============================================================================
def get_next_run_time(schedule_times):
    """Tìm thời điểm quét tiếp theo từ danh sách khung giờ (giờ VN)."""
    now = datetime.now(TZ_VN)
    today = now.date()
    candidates = []
    for (h, m) in schedule_times:
        t = datetime(today.year, today.month, today.day, h, m, tzinfo=TZ_VN)
        if t > now:
            candidates.append(t)
    if not candidates:
        # Tất cả giờ hôm nay đã qua → lấy giờ đầu tiên ngày mai
        tomorrow = today + timedelta(days=1)
        h, m = schedule_times[0]
        candidates.append(datetime(tomorrow.year, tomorrow.month, tomorrow.day, h, m, tzinfo=TZ_VN))
    return min(candidates)


def start_scheduler(gc):
    """Vòng lặp chạy tự động theo SCHEDULE_TIMES. Nhấn Ctrl+C để dừng."""
    # Sắp xếp giờ tăng dần
    schedule_times = sorted(SCHEDULE_TIMES)
    
    print("\n" + "="*70)
    print("⏰ CHẾ ĐỘ TỰ ĐỘNG - Lịch quét hàng ngày (Giờ Việt Nam GMT+7):")
    for (h, m) in schedule_times:
        print(f"   • {h:02d}:{m:02d}")
    print("   Nhấn Ctrl+C để dừng.")
    print("="*70)
    
    try:
        while True:
            now = datetime.now(TZ_VN)
            next_run = get_next_run_time(schedule_times)
            wait_secs = (next_run - now).total_seconds()
            next_run_str = next_run.strftime("%d/%m/%Y %H:%M")
            
            print(f"\n⏳ Lần quét tiếp theo: {next_run_str} (còn {int(wait_secs//3600)}h {int((wait_secs%3600)//60)}p)")
            
            # Chờ đến giờ (kiểm tra mỗi 30 giây)
            while True:
                now = datetime.now(TZ_VN)
                remaining = (next_run - now).total_seconds()
                if remaining <= 0:
                    break
                sleep_chunk = min(30, remaining)
                time.sleep(sleep_chunk)
            
            print(f"\n🔔 ĐÃ ĐẾN GIỜ QUÉT: {datetime.now(TZ_VN).strftime('%H:%M')}")
            
            # Tính lần quét tiếp theo (sau lần này)
            time.sleep(2)  # buffer nhỏ để tránh tính trùng cùng phút
            next_next = get_next_run_time(schedule_times)
            next_next_str = next_next.strftime("%d/%m/%Y %H:%M")
            
            run_scraper_job(gc, next_run_str=next_next_str)
            
    except KeyboardInterrupt:
        print("\n[Dừng] Bạn đã dừng lịch tự động.")


# ==============================================================================
# MAIN ENGINE
# ==============================================================================
def main():
    if SPREADSHEET_URL == "https://docs.google.com/spreadsheets/d/XXXXXXXXXX/edit":
        print("[!] Hãy điền SPREADSHEET_URL của bạn vào cấu hình ở đầu file.")
        return
    
    # Xác thực Google Sheets 1 lần duy nhất (cache session)
    gc = get_gc()
    if not gc:
        return
    
    # Hỏi người dùng muốn chạy ngay hay chờ theo lịch
    print("\n" + "="*70)
    print("Bạn muốn:")
    print("  [1] Chạy quét NGAY BÂY GIỜ")
    print("  [2] Chờ và chạy tự động theo LỊCH (7:00 / 9:30 / 12:00 / 16:00 / 20:00)")
    print("="*70)
    
    try:
        choice = input("Nhập lựa chọn (1 hoặc 2, mặc định = 1): ").strip()
    except Exception:
        choice = "1"  # Nếu không nhập được (ví dụ chạy non-interactive), chạy ngay
    
    if choice == "2":
        start_scheduler(gc)
    else:
        # Tính giờ quét tiếp theo để đưa vào Telegram
        next_run = get_next_run_time(sorted(SCHEDULE_TIMES))
        next_run_str = next_run.strftime("%d/%m/%Y %H:%M")
        run_scraper_job(gc, next_run_str=next_run_str)


if __name__ == "__main__":
    main()
