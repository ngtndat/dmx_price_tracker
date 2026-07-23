"""
Affiliate Link Conversion Module for PricePulse
Supports: AccessTrade (VN), Involve Asia, Shopee Affiliate, Lazada Affiliate, Traveloka, Trip.com
"""
import urllib.parse
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

# --- Config ---
ACCESSTRADE_PUB_ID = os.getenv("ACCESSTRADE_PUB_ID", "")
INVOLVE_ASIA_PUB_ID = os.getenv("INVOLVE_ASIA_PUB_ID", "")
SHOPEE_AFFILIATE_TAG = os.getenv("SHOPEE_AFFILIATE_TAG", "")
LAZADA_AFFILIATE_TAG = os.getenv("LAZADA_AFFILIATE_TAG", "")
TRAVELOKA_AFFILIATE_TAG = os.getenv("TRAVELOKA_AFFILIATE_TAG", "")
TRIPDOTCOM_AFFILIATE_TAG = os.getenv("TRIPDOTCOM_AFFILIATE_TAG", "")
UTM_SOURCE = "pricepulse"
UTM_MEDIUM = "affiliate"


def convert_to_affiliate(url: str, platform: str) -> dict:
    """
    Converts a raw product URL to an affiliate link.

    Returns:
        dict with keys:
            - affiliate_url: the monetised link to redirect to
            - network: which affiliate network was used
            - is_converted: True if a real affiliate link was generated
    """
    url = url.strip()
    encoded = urllib.parse.quote(url, safe="")
    utm = f"utm_source={UTM_SOURCE}&utm_medium={UTM_MEDIUM}&utm_campaign={platform}"

    # --- Shopee ---
    if platform == "shopee":
        if SHOPEE_AFFILIATE_TAG:
            # Shopee Affiliate deep link via sub-affiliate tag
            affiliate_url = f"https://s.shopee.vn/a-promo?smtt={SHOPEE_AFFILIATE_TAG}&url={encoded}&{utm}"
            return {"affiliate_url": affiliate_url, "network": "Shopee Affiliate", "is_converted": True}
        elif ACCESSTRADE_PUB_ID:
            affiliate_url = f"https://pub.accesstrade.vn/deep_link/{ACCESSTRADE_PUB_ID}?url={encoded}&{utm}"
            return {"affiliate_url": affiliate_url, "network": "AccessTrade", "is_converted": True}

    # --- Lazada ---
    elif platform == "lazada":
        if LAZADA_AFFILIATE_TAG:
            affiliate_url = f"https://www.lazada.vn/shop/?adcode={LAZADA_AFFILIATE_TAG}&url={encoded}&{utm}"
            return {"affiliate_url": affiliate_url, "network": "Lazada Affiliate", "is_converted": True}
        elif ACCESSTRADE_PUB_ID:
            affiliate_url = f"https://pub.accesstrade.vn/deep_link/{ACCESSTRADE_PUB_ID}?url={encoded}&{utm}"
            return {"affiliate_url": affiliate_url, "network": "AccessTrade", "is_converted": True}

    # --- TikTok Shop ---
    elif platform == "tiktok":
        if ACCESSTRADE_PUB_ID:
            affiliate_url = f"https://pub.accesstrade.vn/deep_link/{ACCESSTRADE_PUB_ID}?url={encoded}&{utm}"
            return {"affiliate_url": affiliate_url, "network": "AccessTrade", "is_converted": True}

    # --- Traveloka ---
    elif platform == "traveloka":
        if TRAVELOKA_AFFILIATE_TAG:
            affiliate_url = f"https://www.traveloka.com/affiliate?af_id={TRAVELOKA_AFFILIATE_TAG}&url={encoded}&{utm}"
            return {"affiliate_url": affiliate_url, "network": "Traveloka Affiliate", "is_converted": True}
        elif INVOLVE_ASIA_PUB_ID:
            affiliate_url = f"https://invol.co/{INVOLVE_ASIA_PUB_ID}?url={encoded}&{utm}"
            return {"affiliate_url": affiliate_url, "network": "Involve Asia", "is_converted": True}

    # --- Trip.com ---
    elif platform == "trip":
        if TRIPDOTCOM_AFFILIATE_TAG:
            affiliate_url = f"https://www.trip.com/affiliate/?aid={TRIPDOTCOM_AFFILIATE_TAG}&url={encoded}&{utm}"
            return {"affiliate_url": affiliate_url, "network": "Trip.com Affiliate", "is_converted": True}
        elif INVOLVE_ASIA_PUB_ID:
            affiliate_url = f"https://invol.co/{INVOLVE_ASIA_PUB_ID}?url={encoded}&{utm}"
            return {"affiliate_url": affiliate_url, "network": "Involve Asia", "is_converted": True}

    # Sendo
    elif platform == "sendo":
        if ACCESSTRADE_PUB_ID:
            affiliate_url = f"https://pub.accesstrade.vn/deep_link/{ACCESSTRADE_PUB_ID}?url={encoded}&{utm}"
            return {"affiliate_url": affiliate_url, "network": "AccessTrade", "is_converted": True}

    # Thế Giới Di Động / Điện Máy Xanh
    elif platform in ("thegioididong", "dienmayxanh"):
        if ACCESSTRADE_PUB_ID:
            affiliate_url = f"https://pub.accesstrade.vn/deep_link/{ACCESSTRADE_PUB_ID}?url={encoded}&{utm}"
            return {"affiliate_url": affiliate_url, "network": "AccessTrade", "is_converted": True}

    # Fallback: no affiliate ID configured – return original URL with UTM tracking
    fallback_sep = "&" if "?" in url else "?"
    fallback_url = f"{url}{fallback_sep}{utm}"
    return {"affiliate_url": fallback_url, "network": "Direct (no affiliate)", "is_converted": False}


def get_affiliate_setup_tip(platform: str) -> str:
    """
    Returns a user-facing tip suggesting how to get affiliate revenue for a platform.
    """
    tips = {
        "shopee": "💡 Đăng ký <a href='https://affiliate.shopee.vn' target='_blank'>Shopee Affiliate</a> hoặc <a href='https://accesstrade.vn' target='_blank'>AccessTrade</a> để nhận hoa hồng khi người dùng mua qua link của bạn!",
        "lazada": "💡 Đăng ký <a href='https://accesstrade.vn' target='_blank'>AccessTrade</a> để tạo deep link Lazada và nhận hoa hồng 2–5% mỗi đơn hàng.",
        "tiktok": "💡 Tham gia <a href='https://accesstrade.vn' target='_blank'>AccessTrade</a> để tạo link affiliate TikTok Shop.",
        "traveloka": "💡 Đăng ký <a href='https://www.traveloka.com/vi-vn/p/affiliate' target='_blank'>Traveloka Affiliate</a> để nhận hoa hồng cho mỗi booking khách sạn / vé máy bay.",
        "trip": "💡 Tham gia <a href='https://affiliates.trip.com' target='_blank'>Trip.com Affiliate</a> để nhận hoa hồng từ đặt phòng và tour.",
        "sendo": "💡 Đăng ký <a href='https://accesstrade.vn' target='_blank'>AccessTrade</a> để tạo link affiliate Sendo.",
        "thegioididong": "💡 Đăng ký <a href='https://accesstrade.vn' target='_blank'>AccessTrade</a> để tạo link affiliate Thế Giới Di Động.",
        "dienmayxanh": "💡 Đăng ký <a href='https://accesstrade.vn' target='_blank'>AccessTrade</a> để tạo link affiliate Điện Máy Xanh.",
    }
    return tips.get(platform, "💡 Đăng ký <a href='https://accesstrade.vn' target='_blank'>AccessTrade</a> để kiếm hoa hồng từ link sản phẩm này!")
