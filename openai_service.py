import os
import base64
import requests
import re
from openai import OpenAI

# 1. إعداد العميل
api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY") or "not_set"
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

# 2. القواعد الفنية الصارمة (لضمان الجمالية ومنع النصوص العشوائية)
GLOBAL_STORYBOOK_STYLE = """
You are a professional children's book illustrator. 
STYLE: Soft watercolor and colored pencil, warm pastel tones, clean white background. 
RULES: 
- The image must be PURELY VISUAL. No text, letters, or banners.
- Centralize the character. Leave TOP 15% and BOTTOM 15% as clear white space.
- Maintain 100% character consistency based on the provided description.
""".strip()

def create_character_reference(image_data, gender="boy", is_url=True):
    """
    تحليل الصورة لإنتاج وصف دقيق (حوالي 100 كلمة) يجمع بين:
    (العمر، الملامح، الملابس الحقيقية، والجو العام)
    """
    try:
        image_content = {"url": image_data} if is_url else {"url": f"data:image/jpeg;base64,{image_data}"}
        
        # هذا هو البرومبت الذي سينتج الوصف الذي أعجبك
        analysis_prompt = (
            f"Act as a professional character designer. Analyze this {gender}'s photo and provide "
            f"a highly detailed visual description (MAX 100 words). Describe their exact age, "
            f"hair texture/color, eye shape/expression, and EXACT clothing (colors, patterns, type). "
            f"End with the lighting and storybook atmosphere. Output as a single fluid paragraph."
        )

        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-lite-001",
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": analysis_prompt},
                    {"type": "image_url", "image_url": image_content}
                ]
            }],
            max_tokens=200
        )
        description = response.choices[0].message.content.strip()
        return description
    except Exception as e:
        print(f"Analysis Error: {e}")
        return f"A cute {gender} in watercolor style."

def generate_storybook_page(character_description, page_prompt, gender="boy", is_cover=False):
    """
    توليد الصفحة باستخدام الوصف التفصيلي المستخرج
    """
    try:
        # دمج الوصف التفصيلي مع فعل الصفحة المطلوبة
        full_prompt = (
            f"{'COVER ART:' if is_cover else 'STORY SCENE:'} "
            f"The character is: {character_description}. "
            f"In this scene: {page_prompt}. "
            f"Ensure the clothing and facial features remain identical to the description."
        )

        payload = {
            "model": "google/gemini-2.5-flash-image",
            "messages": [
                {"role": "system", "content": GLOBAL_STORYBOOK_STYLE},
                {"role": "user", "content": full_prompt}
            ],
            "modalities": ["image"]
        }
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=90)
        
        data = response.json()
        full_text = str(data)
        
        # استخراج الصورة سواء كانت رابط أو Base64
        if "data:image" in full_text:
            return re.search(r'data:image/[^;]+;base64,[^"\'\s]+', full_text).group(0)
        
        url_match = re.search(r'https://[^\s"\'<>]+(?:\.png|\.jpg|\.jpeg)', full_text)
        return url_match.group(0) if url_match else None
    except Exception as e:
        print(f"Generation Error: {e}")
        return None

def verify_payment_screenshot(image_data, target_handle):
    """دالة التحقق من الدفع (لا تلمسها، فهي تعمل بكفاءة)"""
    try:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "google/gemini-2.0-flash-001",
            "messages": [{
                "role": "user", 
                "content": [
                    {"type": "text", "text": f"Is this a valid payment transfer to {target_handle}? Reply ONLY YES or NO."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                ]
            }]
        }
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=20)
        return "YES" in response.json()["choices"][0]["message"]["content"].strip().upper()
    except: return False
