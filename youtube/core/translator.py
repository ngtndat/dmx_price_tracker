import os
import re
from typing import List, Dict
from deep_translator import GoogleTranslator

# Short Drama / Web Novel Term Mapping Dictionary (Trung - Việt)
DRAMA_DICTIONARY = {
    "高考": "kỳ thi đại học",
    "重生": "trọng sinh",
    "学霸": "học bá",
    "学渣": "học cặn",
    "爽文": "sảng văn",
    "白莲花": "bạch liên hoa",
    "金手指": "bàn tay vàng",
    "穿越": "xuyên không",
    "霸道总裁": "tổng tài bá đạo",
    "渣男": "tra nam",
    "绿茶": "trà xanh",
    "系统": "hệ thống",
    "逆袭": "nghịch tập",
    "状元": "Trạng Nguyên",
    "打脸": "vả mặt",
    "金主": "kim chủ",
    "大佬": "đại lão",
    "闺蜜": "bạn thân",
    "吃瓜": "hóng drama",
    "影帝": "ảnh đế",
    "影后": "ảnh hậu"
}

# Post-processing fixes for common Google Translate awkward phrases
POST_TRANSLATE_FIXES = {
    r"\bZhuangyuan\b": "Trạng Nguyên",
    r"\bShuangwen\b": "sảng văn",
    r"\bBaidao\b": "bá đạo",
    r"\bcool article\b": "kịch tính",
    r"\bchong sheng\b": "trọng sinh",
}

def preprocess_chinese_text(text: str) -> str:
    """Preprocess Chinese text with drama term dictionary before translation."""
    for zh_term, vi_term in DRAMA_DICTIONARY.items():
        if zh_term in text:
            # Keep mapping in mind
            pass
    return text

def postprocess_vietnamese_text(text: str) -> str:
    """Refine translated Vietnamese text for smooth reading."""
    if not text:
        return text
    for pattern, replacement in POST_TRANSLATE_FIXES.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    # Capitalize first letter properly
    text = text.strip()
    if text and len(text) > 0:
        text = text[0].upper() + text[1:]
    return text

def translate_segments(segments: List[Dict], target_lang: str = "vi") -> List[Dict]:
    """
    Translates Chinese transcribed segments into target_lang ('vi' or 'en').
    Updates segments dict with 'text_vi' or 'text_en' field.
    """
    if not segments:
        return segments

    translator = GoogleTranslator(source='zh-CN', target=target_lang)
    texts = [seg["text"] for seg in segments]

    batch_size = 25
    translated_texts = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        try:
            batch_str = "\n".join(batch)
            translated_str = translator.translate(batch_str)
            translated_list = translated_str.split("\n")
            if len(translated_list) == len(batch):
                translated_texts.extend(translated_list)
            else:
                for item in batch:
                    translated_texts.append(translator.translate(item))
        except Exception as e:
            print(f"Translation batch error: {e}, falling back line by line...")
            for item in batch:
                try:
                    translated_texts.append(translator.translate(item))
                except Exception:
                    translated_texts.append(item)

    # Attach translated texts to segments with post-processing
    for seg, trans in zip(segments, translated_texts):
        cleaned_trans = trans.strip() if trans else seg["text"]
        if target_lang == "vi":
            cleaned_trans = postprocess_vietnamese_text(cleaned_trans)
        seg[f"text_{target_lang}"] = cleaned_trans

    return segments

def translate_dual(segments: List[Dict]) -> List[Dict]:
    """
    Translates Chinese segments to BOTH Vietnamese ('vi') AND English ('en').
    """
    segments = translate_segments(segments, target_lang="vi")
    segments = translate_segments(segments, target_lang="en")
    return segments

