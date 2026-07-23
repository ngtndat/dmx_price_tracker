# ==============================================================================
# FPT SHOP SCRAPER VIA GOOGLE SEARCH SNIPPETS
# ==============================================================================
# LƯU Ý QUAN TRỌNG:
# 1. Google chặn dải IP của Google Colab (trả về lỗi 429) để chống bot tự động.
# 2. Để chạy thành công đoạn code này, bạn hãy chạy trực tiếp bằng Python trên
#    MÁY TÍNH CÁ NHÂN (Residential IP) của mình thay vì chạy trên Google Colab.
# ==============================================================================

import requests
from bs4 import BeautifulSoup
import urllib.parse
import re
import time
import urllib3

# Tắt cảnh báo kết nối SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
}

def clean_price(price_str):
    if not price_str:
        return "0"
    cleaned = price_str.replace("₫", "").replace(".", "").replace("\xa0", "").replace("đ", "").strip()
    cleaned = "".join(c for c in cleaned if c.isdigit())
    return cleaned if cleaned else "0"

def format_price_thousands(val_str):
    if not val_str or val_str == "N/A" or val_str == "0":
        return "N/A"
    cleaned = clean_price(val_str)
    try:
        val = int(cleaned)
        return str(val // 1000)
    except ValueError:
        return val_str

def scrape_fpt_from_google_snippets(model_list):
    print(f"\n--- CÀO THÔNG TIN FPT SHOP QUA SNIPPET GOOGLE ---")
    results = []
    
    for idx, model in enumerate(model_list, 1):
        query = f"{model} fptshop"
        # hl=vi để Google hiển thị tiếng Việt và định dạng giá tiền (đ / ₫)
        url = f"https://www.google.com/search?q={urllib.parse.quote_plus(query)}&hl=vi"
        print(f"[{idx}/{len(model_list)}] Đang truy vấn Google: '{query}'...")
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=12)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                # Thẻ bao bọc các kết quả tìm kiếm của Google
                g_cards = soup.find_all(class_="g")
                
                fpt_matched = False
                for card in g_cards:
                    a_tag = card.find("a", href=True)
                    if a_tag and "fptshop.com.vn" in a_tag["href"]:
                        # 1. Trích xuất Tên sản phẩm hiển thị trên Google (thường trong h3)
                        h3 = card.find("h3")
                        title_name = h3.text.strip() if h3 else "N/A"
                        
                        # 2. Tìm giá tiền hiển thị ở dòng mô tả của Google (Ví dụ: "5.990.000 đ")
                        card_text = card.text
                        
                        # Sử dụng Regex để tìm các số định dạng giá Việt Nam (ví dụ: 5.990.000 đ)
                        price_patterns = re.findall(r"\b\d{1,3}(?:\.\d{3})+(?:\s*(?:đ|₫|VND))?", card_text)
                        
                        price_found = "N/A"
                        for pattern in price_patterns:
                            # Ưu tiên lấy những giá trị chứa ký hiệu tiền tệ
                            if "đ" in pattern or "₫" in pattern:
                                price_found = pattern
                                break
                            elif pattern.count(".") >= 2: # hoặc có 2 dấu chấm trở lên (ví dụ: 5.990.000)
                                price_found = pattern
                                break
                        
                        # Rút gọn tên hiển thị (bỏ phần đuôi - FPTShop...)
                        clean_name = title_name.replace(" - FPTShop.com.vn", "").replace(" - Fptshop.com.vn", "").strip()
                        # Rút gọn giá thành dạng nghìn đồng (ví dụ: 5990)
                        final_price = format_price_thousands(price_found)
                        
                        print(f"  -> Tên tìm thấy: {clean_name}")
                        print(f"  -> Giá tìm thấy: {price_found} (Rút gọn: {final_price})")
                        print(f"  -> Đường dẫn: {a_tag['href']}")
                        
                        results.append({
                            "Mã Model": model,
                            "Tên Model": clean_name,
                            "Giá cuối": final_price,
                            "Link": a_tag['href']
                        })
                        fpt_matched = True
                        break
                        
                if not fpt_matched:
                    print("  -> [!] Không tìm thấy kết quả FPT Shop nào trên trang đầu Google.")
                    
            elif response.status_code == 429:
                print("  -> [!] Lỗi 429: Google chặn lượt quét của bạn (Vui lòng chạy lại trên Máy tính cá nhân thay vì Colab).")
            else:
                print(f"  -> [!] Lỗi kết nối Google: {response.status_code}")
                
        except Exception as e:
            print(f"  -> [!] Lỗi: {e}")
            
        time.sleep(3) # Delay một chút tránh bị Google quét bot
        
    return results

if __name__ == "__main__":
    # Chạy thử nghiệm danh sách các mã model mẫu
    test_models = ["AS60GHWG0", "MD16GQSE0", "AS10GDBY0"]
    scrape_fpt_from_google_snippets(test_models)