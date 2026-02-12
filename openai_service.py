import os
import base64
import requests
import re
from openai import OpenAI

# إعداد مفتاح API
api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY") or "not_set"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

# القواعد العامة لنمط الكتاب (Watercolor Style)
GLOBAL_STORYBOOK_STYLE = """
Style: classic children's storybook, soft watercolor + colored pencil, warm pastel colors.
Format: square (1:1). Top 75% artwork, bottom 25% clean light panel for Arabic text.
Character Consistency: The hero MUST look identical to the description on ALL pages.
- Same face, skin tone, and hair.
- MUST wear a striped sweatshirt in every scene.
- No text inside the artwork itself.
""".strip()

def create_character_reference(image_data, is_url=True):
    """تحليل الصورة واستخراج وصف دقيق ومختصر للهوية البصرية"""
    try:
        image_content = {"url": image_data} if is_url else {"url": f"data:image/jpeg;base64,{image_data}"}

        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-lite-001",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this child for a storybook. Focus on face shape, hair texture/color, and eye shape. IMPORTANT: Mention they are wearing a striped sweatshirt. Keep the total description under 150 tokens to avoid errors."},
                        {"type": "image_url", "image_url": image_content}
                    ],
                }
            ],
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error creating character reference: {e}")
        return "A cute child with curly hair wearing a striped sweatshirt, watercolor style."

def verify_payment_screenshot(image_data, target_handle):
    """التحقق من صحة صورة التحويل البنكي"""
    try:
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        prompt = f"Does this payment screenshot show a transfer to '{target_handle}'? Reply with ONLY 'YES' or 'NO'."
        
        payload = {
            "model": "google/gemini-2.0-flash-001",
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}]}]
        }
        
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=20)
        answer = response.json()["choices"][0]["message"]["content"].strip().upper()
        return "YES" in answer
    except Exception as e:
        print(f"Error in verification: {e}")
        return False

def generate_storybook_page(character_description, page_prompt, child_name=None, is_cover=False, is_final=False):
    """توليد صورة الصفحة مع الحفاظ على تناسق الشخصية"""
    try:
        page_type = "COVER PAGE" if is_cover else ("FINAL REWARD PAGE" if is_final else "STORY PAGE")
        
        user_content = f"""
        TASK: {page_type}
        CHARACTER: {character_description}
        SCENE: {page_prompt}
        NAME: {child_name if child_name else ''}
        REMINDER: Child MUST wear the striped sweatshirt. Leave bottom 25% empty for text.
        """.strip()

        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "google/gemini-2.5-flash-image",
            "messages": [
                {"role": "system", "content": GLOBAL_STORYBOOK_STYLE},
                {"role": "user", "content": user_content}
            ],
            "modalities": ["image"]
        }
        
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
        data = response.json()
        
        # محاولة استخراج الرابط من مختلف تنسيقات الرد
        res_content = ""
        if 'images' in data['choices'][0]:
            res_content = data['choices'][0]['images'][0]
        else:
            res_content = data['choices'][0]['message']['content']

        # استخدام Regex لضمان الحصول على الرابط فقط
        url_match = re.search(r'https://\S+', str(res_content))
        return url_match.group(0).rstrip(')') if url_match else None

    except Exception as e:
        print(f"Error generating page: {e}")
        return None

def transform_photo_to_character(image_data, is_url=False):
    char_desc = create_character_reference(image_data, is_url=is_url)
    return generate_storybook_page(char_desc, "A professional character portrait, smiling.")
