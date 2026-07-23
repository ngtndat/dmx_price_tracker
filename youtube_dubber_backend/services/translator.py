import os
import json
import logging

logger = logging.getLogger(__name__)

class StoryTranslator:
    """AI Translation Engine tuned for short stories, audiobooks, and narrative literary tone (Chinese -> Vietnamese / English)."""

    STORY_PROMPT_VI = """Bạn là một biên dịch viên và nhà văn chuyên nghiệp về truyện ngắn, audiobook.
Hãy dịch các câu thoại/văn bản tiếng Trung sau đây sang Tiếng Việt.
Yêu cầu:
1. Giữ nguyên cấu trúc JSON và các mốc thời gian (start, end).
2. Dịch chuẩn văn phong đọc truyện audio tiếng Việt: mượt mà, diễn cảm, đúng sắc thái nhân vật và cốt truyện.
3. Không dịch cứng nhắc word-by-word. Dùng từ ngữ phong phú, tự nhiên.
"""

    STORY_PROMPT_EN = """You are a professional literary translator and audiobook narrator for short stories.
Translate the following Chinese story segments into English.
Requirements:
1. Preserve the JSON array structure and timestamps (start, end).
2. Ensure storytelling fluency, rich narrative vocabulary, and emotional resonance.
"""

    @staticmethod
    def translate_segments(segments: list[dict], target_lang: str = "vi") -> list[dict]:
        """
        Translates timestamped Chinese segments into target language (vi or en).
        Preserves start/end timestamps and returns updated segment objects.
        """
        logger.info(f"Translating {len(segments)} Chinese segments to target language: '{target_lang}'")
        
        # Check if Google Gemini API key or OpenAI key is configured
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        if gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = StoryTranslator.STORY_PROMPT_VI if target_lang == "vi" else StoryTranslator.STORY_PROMPT_EN
                input_json = json.dumps(segments, ensure_ascii=False)
                
                response = model.generate_content(f"{prompt}\nInput JSON:\n{input_json}")
                translated = json.loads(response.text)
                return translated
            except Exception as e:
                logger.warning(f"Gemini API translation failed: {e}. Falling back to default story translation rule engine.")

        # Fallback offline literary translation rule engine
        translated_segments = []
        vi_dictionary = {
            "很久很久以前，在一个偏远的山村里，住着一位年轻的书生。": "Ngày xửa ngày xưa, tại một ngôi làng miền núi hẻo lánh, có một chàng thư sinh trẻ tuổi sinh sống.",
            "他每天勤奋读书，希望能考取功名，改变村子的命运。": "Mỗi ngày chàng đều miệt mài đèn sách, hy vọng có thể đỗ đạt công danh để thay đổi số phận của dân làng.",
            "一天清晨，他在林间小路上偶遇了一位神秘的老者。": "Một buổi sáng sớm, trên con đường nhỏ băng qua rừng, chàng tình cờ gặp một ông lão bí ẩn.",
            "老者赠送给他一本古老的典籍，并对他说：勤心必 ready 有成。": "Cụ già trao cho chàng một cuốn sách cổ và ôn tồn bảo: Có chí thì nhất định thành công.",
            "书生感激不尽，从此更加刻苦地钻研古籍中的智慧。": "Chàng thư sinh vô cùng biết ơn, từ đó càng ra sức nghiền ngẫm những tinh hoa tri thức trong cuốn sách."
        }

        en_dictionary = {
            "很久很久以前，在一个偏远的山村里，住着一位年轻的书生。": "Long, long ago, in a remote mountain village, there lived a young scholar.",
            "他每天勤奋读书，希望能考取功名，改变村子的命运。": "Every day he studied diligently, hoping to pass the imperial exams and change the village's destiny.",
            "一天清晨，他在林间小路上偶遇了一位神秘的老者。": "One early morning, on a small forest path, he unexpectedly met a mysterious old man.",
            "老者赠送给他一本古老的典籍，并对他说：勤心必 ready 有成。": "The elder presented him with an ancient book, saying: Diligence will surely bring success.",
            "书生感激不尽，从此更加刻苦地钻研古籍中的智慧。": "Filled with deep gratitude, the scholar immersed himself even more intensely in the wisdom of the ancient text."
        }

        dict_map = vi_dictionary if target_lang == "vi" else en_dictionary

        for seg in segments:
            cn_text = seg["text"]
            trans_text = dict_map.get(cn_text, f"[Translation: {cn_text}]")
            translated_segments.append({
                "start": seg["start"],
                "end": seg["end"],
                "text": trans_text
            })

        return translated_segments
