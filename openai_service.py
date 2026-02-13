import requests
import base64
import os
import uuid
import logging

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def generate_storybook_page(char_desc, prompt, gender="ولد", is_cover=False):
    """
    توليد الصور حصرياً عبر نموذج FLUX Klein 4b على OpenRouter
    """
    try:
        # 1. صياغة البرومبت بأسلوب FLUX (يحب الوصف المباشر)
        full_prompt = f"A whimsical children's book illustration in soft watercolor and colored pencil style. {char_desc}. Scene: {prompt}. Dreamy glowing lighting, high quality, consistent character."
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # 2. إعدادات الطلب لـ OpenRouter
        payload = {
            "model": "black-forest-labs/flux.2-klein-4b", 
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": full_prompt}
                    ]
                }
            ],
            "modalities": ["image"] # السطر الأهم لتفعيل الرسم
        }
        
        logger.info(f"🎨 Requesting FLUX Klein for: {prompt[:30]}...")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60 # زيادة الوقت لأن الرسم يحتاج وقت أطول من النص
        )
        
        if response.status_code == 200:
            data = response.json()
            # استخراج الصورة من مخرجات OpenRouter
            message = data.get("choices", [{}])[0].get("message", {})
            images = message.get("images", [])
            
            if images:
                # OpenRouter يرسل الصورة كـ Data URL (Base64)
                image_data_url = images[0].get("url", "")
                if "," in image_data_url:
                    base64_string = image_data_url.split(",")[1]
                    
                    # حفظ الصورة في المجلد المؤقت للسيرفر
                    temp_filename = f"/tmp/flux_{uuid.uuid4().hex[:8]}.png"
                    with open(temp_filename, "wb") as fh:
                        fh.write(base64.b64decode(base64_string))
                    
                    return temp_filename # نرجع المسار المحلي للصورة
            
        logger.error(f"❌ FLUX Error: {response.text}")
        return None
            
    except Exception as e:
        logger.error(f"❌ Image Gen Exception: {e}")
        return None
