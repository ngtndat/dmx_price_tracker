from typing import List, Dict

def generate_youtube_metadata(title_hint: str, segments: List[Dict], lang: str = "vi") -> Dict[str, str]:
    """
    Generates YouTube title, description, and tags optimized for viral short stories / short drama.
    """
    text_key = f"text_{lang}"
    sample_text = " ".join([seg.get(text_key, seg.get("text", "")) for seg in segments[:10]])

    if lang == "vi":
        title = f"[Phim Ngắn Hay 2026] {title_hint} - Thuyết Minh Tiếng Việt | Truyện Ngắn Trung Quốc"
        description = f"""🎬 {title_hint} - Phim Truyện Ngắn Trung Quốc Hay Nhất (Thuyết Minh / Phụ Đề Tiếng Việt)

📌 Tóm tắt nội dung:
{sample_text[:300]}...

❤️ Bấm Đăng Ký (Subscribe) và Bật Chuông để xem các bộ phim ngắn Trung Quốc hot nhất mỗi ngày!
#PhimNgan #TruyenNganTrungQuoc #PhimHay #ThuyetMinhTiengViet #PhimTrungQuoc #ShortDrama
"""
        tags = "Phim ngắn Trung Quốc, Truyện ngắn Trung Quốc, Phim hay 2026, Phim thuyết minh, Phim ngôn tình, Phim hay mỗi ngày, Short drama, Phim bộ ngắn"

    else:
        title = f"[Short Drama 2026] {title_hint} - English Dubbed / Subtitled | Chinese Short Story"
        description = f"""🎬 {title_hint} - Chinese Short Drama & Mini Series (English Voiceover & Subtitles)

📌 Synopsis:
{sample_text[:300]}...

❤️ Don't forget to Like, Share and Subscribe for daily exciting mini-dramas!
#ShortDrama #ChineseDrama #EngSub #MiniSeries #AsianDrama
"""
        tags = "Chinese short drama, Mini series, Eng sub, English dubbed, Best chinese drama 2026, Short movie, Romantic drama"

    return {
        "title": title,
        "description": description,
        "tags": tags
    }
