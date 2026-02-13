import requests
import base64
import os
import uuid
import logging

logger = logging.getLogger(__name__)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

def generate_storybook_page(char_desc, prompt, gender="ولد", is_cover=False):
    """
    توليد الصور عبر OpenRouter باستخدام نموذج FLUX Klein 4b
    """
    try:
        # 1. صياغة البرومبت
        full_prompt = f"A whimsical children's book illustration. {char_desc}. Scene: {prompt}. Soft watercolor style, magical atmosphere."
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        
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
            "modalities": ["image"]
        }
        
        logger.info(f"🎨 Sending request to OpenRouter FLUX...")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=120 # زيادة الوقت لضمان استلام الصور الكبيرة
        )
        
        if response.status_code != 200:
            logger.error(f"❌ API Error: {response.status_code} - {response.text}")
            return None

        data = response.json()
        
        # 2. استخراج الصورة (هذا هو التعديل الصحيح حسب الـ Logs الخاصة بك)
        choices = data.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            images = message.get("images", []) # OpenRouter يضعها هنا
            
            if images:
                image_url_data = images[0] # قد يكون رابط مباشر أو Base64
                
                # إذا كان رابطاً مباشراً يبدأ بـ http
                if isinstance(image_url_data, str) and image_url_data.startswith("http"):
                    return image_url_data
                
                # إذا كان قاموساً يحتوي على url (كما في سجلاتك)
                elif isinstance(image_url_data, dict):
                    img_url = image_url_data.get("url", "")
                    
                    # إذا كانت بيانات Base64
                    if "base64" in img_url or "," in img_url:
                        base64_string = img_url.split(",")[1] if "," in img_url else img_url
                        temp_filename = f"/tmp/flux_{uuid.uuid4().hex[:8]}.png"
                        with open(temp_filename, "wb") as fh:
                            fh.write(base64.b64decode(base64_string))
                        return temp_filename
                    
                    return img_url

        logger.error(f"❌ Could not find image in response: {data}")
        return None
            
    except Exception as e:
        logger.error(f"❌ Exception in generate_storybook_page: {e}")
        return None
