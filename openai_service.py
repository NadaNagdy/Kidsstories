import os
import base64
import requests
import re
from openai import OpenAI

# 1. إعداد مفتاح API والعميل
# يتم جلب المفتاح من متغيرات البيئة لضمان الأمان
api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY") or "not_set"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

# 2. القواعد العامة لنمط الكتاب (Visual Style & Layout)
# تم تحديثها لمنع الذكاء الاصطناعي من توليد أي نصوص أو مربعات داخل الصورة
GLOBAL_STORYBOOK_STYLE = """
You are a professional children's book illustrator.
STYLE: Soft watercolor and colored pencil, classic aesthetic, warm pastel tones, clean white background.
CHARACTER CONSISTENCY: The hero child must stay identical on all pages.
- Respect the gender provided. Same face, skin tone, and hair texture.
- STRICT NEGATIVE RULE: Absolutely NO text, letters, words, banners, or ribbons inside the image.
- LAYOUT: Leave the TOP 15% and BOTTOM 15% of the image as PURE WHITE SPACE to allow for external text overlay.
- Centralize the character in the middle of the square canvas.
""".strip()

def create_character_reference(image_data, gender="boy", is_url=True):
    """
    تحليل احترافي للصورة لاستخراج وصف دقيق (100 كلمة بحد أقصى).
    يركز على ملامح الوجه، نسيج الشعر، والملابس الحقيقية الموجودة في الصورة.
    """
    try:
        image_content = {"url": image_data} if is_url else {"url": f"data:image/jpeg;base64,{image_data}"}
        
        # البرومبت المطور لاستخلاص الهوية البصرية بدقة "قصصية"
        detailed_prompt = (
            f"Act as a professional character designer. Provide a highly detailed but CONCISE visual description (MAX 100 words). "
            f"Analyze this {gender}'s photo and describe: "
            f"1. Exact age. "
            f"2. Hair (color, style, texture). "
            f"3. Face (skin tone, eye shape/color, expression). "
            f"4. EXACT clothing they are wearing (colors, patterns, and type). "
            f"5. Atmosphere/Lighting. "
            f"Output must be a single fluid paragraph suitable for an AI art generator."
        )
        
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-lite-001",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": detailed_prompt},
                        {"type": "image_url", "image_url": image_content}
                    ],
                }
            ],
            max_tokens=150 # يضمن بقاء الوصف في حدود 100 كلمة
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in character analysis: {e}")
        return f"A cute {gender} in a storybook setting, watercolor style."

def verify_payment_screenshot(image_data, target_handle):
    """التحقق من صحة صورة التحويل (إنستا باي أو محفظة) عبر الذكاء الاصطناعي"""
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
    """
    توليد صور القصة مع الالتزام بالوصف الدقيق ومنع الهلوسة النصية.
    character_description: الوصف المستخلص من صورة الطفل (الـ 100 كلمة).
    """
    try:
        # تحديد موضوع الرسم بناءً على الجنس لزيادة الدقة
        gender_subject = "a beautiful little girl" if gender == "girl" else "a brave little boy"
        
        # برومبت إضافي في حالة الغلاف لضمان تكوين سينمائي
        cover_extra = "This is a cover: Center the child, surrounded by magical storybook elements. NO BANNERS. NO TEXT." if is_cover else ""

        user_content = f"""
        TASK: {'COVER ART' if is_cover else 'STORY ART'}
        SUBJECT: {gender_subject}
        CHARACTER DESCRIPTION: {character_description}
        SCENE DESCRIPTION: {page_prompt}
        {cover_extra}
        REMINDER: Absolutely no text in image. Keep top and bottom margins clear and white.
        """.strip()

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
