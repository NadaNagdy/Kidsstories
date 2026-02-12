import os
import base64
import requests
import re
from openai import OpenAI

# 1. إعداد مفتاح API والعميل
api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY") or "not_set"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

# 2. القواعد العامة لنمط الكتاب
GLOBAL_STORYBOOK_STYLE = """
You are a professional children's book illustrator.
STYLE: Soft watercolor and colored pencil, classic aesthetic, warm pastel tones, clean white background.
CHARACTER CONSISTENCY: The hero child must stay identical on all pages.
- Respect the gender provided. Same face, skin tone, and hair texture.
- Absolutely NO text, letters, or banners inside the image.
- Leave the TOP 15% and BOTTOM 15% clear for external text overlay.
""".strip()

def create_character_reference(image_data, gender="boy", is_url=True):
    """تحليل الصورة واستخلاص الملامح بناءً على الجنس"""
    try:
        image_content = {"url": image_data} if is_url else {"url": f"data:image/jpeg;base64,{image_data}"}
        gender_context = "This child is a girl." if gender == "girl" else "This child is a boy."
        
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-lite-001",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"{gender_context} Analyze this photo for face shape and hair. Focus on details to maintain consistency."},
                        {"type": "image_url", "image_url": image_content}
                    ],
                }
            ],
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error: {e}")
        return "A cute child, watercolor style."

# --- الدالة التي كانت مفقودة وتسببت في توقف البوت ---
def verify_payment_screenshot(image_data, target_handle):
    """التحقق من صحة صورة التحويل عبر الذكاء الاصطناعي"""
    try:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "google/gemini-2.0-flash-001",
            "messages": [
                {
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": f"Is this a valid payment transfer to {target_handle}? Reply ONLY YES or NO."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                    ]
                }
            ]
        }
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=20)
        result = response.json()["choices"][0]["message"]["content"].strip().upper()
        return "YES" in result
    except Exception as e:
        print(f"Payment verification error: {e}")
        return False

def generate_storybook_page(character_description, page_prompt, gender="boy", is_cover=False):
    """توليد صور القصة مع دعم روابط URL و Base64"""
    try:
        gender_subject = "a beautiful little girl" if gender == "girl" else "a brave little boy"
        user_content = f"TASK: {'COVER' if is_cover else 'STORY'}. SUBJECT: {gender_subject}. CHARACTER: {character_description}. SCENE: {page_prompt}."

        payload = {
            "model": "google/gemini-2.5-flash-image",
            "messages": [
                {"role": "system", "content": GLOBAL_STORYBOOK_STYLE},
                {"role": "user", "content": user_content}
            ],
            "modalities": ["image"]
        }
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=90)
        data = response.json()
        
        # استخراج الصورة (سواء كانت رابطاً أو Base64)
        full_text = str(data)
        if "data:image" in full_text:
            match = re.search(r'data:image/[^;]+;base64,[^"\'\s]+', full_text)
            if match: return match.group(0)
        
        url_match = re.search(r'https://[^\s"\'<>]+(?:\.png|\.jpg|\.jpeg|\b)', full_text)
        return url_match.group(0).rstrip(').') if url_match else None
    except Exception as e:
        print(f"Generation Error: {e}")
        return None
