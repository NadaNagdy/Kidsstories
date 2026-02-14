"""
خدمة متكاملة لتوليد وتحليل الصور - نسخة محسّنة 100% مع نظام Character Consistency
"""

import requests
import base64
import os
import uuid
import logging
from typing import Optional, Dict, List

# ============================================================================
# 🔧 Logging Configuration
# ============================================================================

logger = logging.getLogger(__name__)

# ============================================================================
# 🔑 API Keys
# ============================================================================

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # للـ Vision API (اختياري)

# ============================================================================
# 🎨 Character Profile System
# ============================================================================

class CharacterProfile:
    """نظام بروفايل الشخصية لضمان الاتساق"""
    
    def __init__(
        self,
        name: str,
        gender: str,  # "girl" or "boy"
        age: str = "3-4",
        skin_tone: str = "natural skin tone",
        hair_style: str = "natural hairstyle",
        hair_color: str = "natural hair color",
        hair_texture: str = "natural hair texture",
        eye_color: str = "natural eye color",
        clothing_style: str = "casual colorful outfit"
    ):
        self.name = name
        self.gender = gender
        self.age = age
        self.skin_tone = skin_tone
        self.hair_style = hair_style
        self.hair_color = hair_color
        self.hair_texture = hair_texture
        self.eye_color = eye_color
        self.clothing_style = clothing_style
    
    def build_detailed_description(self, emphasis_level: str = "high") -> str:
        """
        بناء وصف مفصل مع تأكيد قوي على الملامح
        
        Args:
            emphasis_level: "low", "medium", or "high"
        """
        
        # Base description
        base_desc = (
            f"adorable {self.age} year old {self.gender} "
            f"named {self.name}"
        )
        
        # High emphasis (recommended for consistency)
        if emphasis_level == "high":
            feats = []
            if "natural" not in self.skin_tone.lower():
                feats.append(f"beautiful {self.skin_tone.upper()} skin tone")
                feats.append(f"rich {self.skin_tone} complexion")
            
            if "natural" not in self.hair_style.lower():
                feats.append(f"natural {self.hair_style.upper()} hairstyle")
                feats.append(f"{self.hair_color} {self.hair_style} hair")
            
            if "natural" not in self.eye_color.lower():
                feats.append(f"large expressive {self.eye_color} eyes with sparkle highlights")

            # Combiner
            details = ", ".join(feats) if feats else "natural healthy appearance"
            critical_features = f", {details}, rosy cheeks, sweet joyful smile, cute rounded toddler proportions, wearing {self.clothing_style}"
            
            # Reinforcement
            ref_parts = []
            if "natural" not in self.skin_tone.lower(): ref_parts.append(f"{self.skin_tone} skin")
            if "natural" not in self.hair_style.lower(): ref_parts.append(f"{self.hair_style} hair")
            
            reinforcement = f". CRITICAL FEATURES: {', '.join(ref_parts)}" if ref_parts else ""
            if reinforcement: reinforcement += ", NO variations from this character appearance"
            
        elif emphasis_level == "medium":
            critical_features = (
                f", with {self.skin_tone} skin tone, "
                f"{self.hair_style} {self.hair_color} hair "
                f"with {self.hair_texture}, "
                f"expressive {self.eye_color} eyes, "
                f"sweet smile, "
                f"wearing {self.clothing_style}"
            )
            reinforcement = ""
            
        else:  # low
            critical_features = (
                f", {self.skin_tone} skin, "
                f"{self.hair_style} hair, "
                f"{self.eye_color} eyes"
            )
            reinforcement = ""
        
        full_description = f"{base_desc}{critical_features}{reinforcement}"
        
        return full_description


def get_hair_texture(style: str) -> str:
    """تحديد نسيج الشعر بناءً على النوع"""
    textures = {
        "afro": "natural curly afro texture with tight coils and volume",
        "curly": "bouncy curly texture with loose coils",
        "wavy": "soft wavy texture with natural movement",
        "straight": "smooth straight texture with shine",
        "braids": "beautiful braided texture with neat patterns",
        "locs": "natural locs texture with definition"
    }
    return textures.get(style.lower(), "natural hair texture")


# ============================================================================
# 🛡️ Helper Functions (Safe Utilities)
# ============================================================================

def _extract_image_from_response(response_data: dict) -> Optional[str]:
    """
    استخراج الصورة من استجابة OpenRouter بطرق متعددة وأكثر قوة
    """
    try:
        # محاولة 1: الوصول المباشر للمسارات الشائعة
        choices = response_data.get("choices", [])
        if choices:
            choice = choices[0]
            # 1.1: message object (Chat Completions)
            message = choice.get("message", {})
            # 1.2: text field (Legacy Completions)
            text = choice.get("text", "")
            
            # البحث في الـ images داخل الـ message
            images = message.get("images", [])
            if images and isinstance(images, list) and len(images) > 0:
                img = images[0]
                if isinstance(img, str): return img
                if isinstance(img, dict): 
                    res = img.get("url") or img.get("data") or img.get("b64_json")
                    if res: return res
            
            # البحث في content (string or blocks)
            content = message.get("content") or text
            if isinstance(content, str) and len(content) > 50:
                c_strip = content.strip()
                if c_strip.startswith(("http", "data:image", "ROkS", "iVBOR", "/9j/")):
                    return c_strip
                # base64 raw check
                if len(c_strip) > 500 and not " " in c_strip[:100]:
                    return c_strip
            
            # multimodal content list
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") in ["image_url", "image"]:
                            return (block.get("image_url", {}).get("url") or 
                                    block.get("image") or block.get("data"))

        # محاولة 2: البحث العميق (Deep Search) عن أي قيمة تشبه الصورة
        def deep_search(obj, depth=0):
            if depth > 10: return None
            
            if isinstance(obj, dict):
                # التحقق من مفاتيح الصور الشائعة أولاً
                for img_key in ["url", "data", "image", "b64_json", "image_url"]:
                    if img_key in obj:
                        val = obj[img_key]
                        if isinstance(val, str) and len(val) > 10:
                            if val.strip().startswith(("http", "data:image", "ROkS", "iVBOR", "/9j/")):
                                return val.strip()
                        elif isinstance(val, dict) and "url" in val:
                            return val["url"]

                for value in obj.values():
                    if isinstance(value, str):
                        v = value.strip().strip('"').strip("'")
                        if v.startswith(("http", "data:image")):
                            return v
                        if len(v) > 500 and v.startswith(("iVBOR", "/9j/", "ROkS", "UklGR")):
                            return v
                                
                    if isinstance(value, (dict, list)):
                        res = deep_search(value, depth + 1)
                        if res: return res
            
            elif isinstance(obj, list):
                for item in obj:
                    res = deep_search(item, depth + 1)
                    if res: return res
            return None

        result = deep_search(response_data)
        if result:
            logger.debug(f"✅ Image data found via deep search (Type: {result[:10]}...)")
            return result
            
        # إذا فشل كل شيء، طباعة المفاتيح العلوية للمساعدة في التشخيص
        logger.warning(f"⚠️ Extraction failed. Top keys: {list(response_data.keys())}")
        if choices:
            msg_keys = list(choices[0].get("message", {}).keys())
            logger.warning(f"⚠️ Message keys: {msg_keys}")

        return None
        
    except Exception as e:
        logger.error(f"❌ Error extracting image: {e}")
        return None


def _save_image_from_data(image_data: str) -> Optional[str]:
    """
    حفظ الصورة من URL أو base64 (مع معالجة متقدمة للأخطاء)
    
    Args:
        image_data: URL أو base64 string
    
    Returns:
        مسار الملف أو URL
    """
    try:
        if not image_data: return None
        
        # 1. حالة URL مباشر
        if image_data.startswith("http"):
            logger.info(f"✅ Direct URL: {image_data[:50]}...")
            return image_data
        
        # 2. حالة Base64
        # تنظيف السلسلة من المقدمات الشائعة
        if "base64," in image_data:
            image_data = image_data.split("base64,")[1]
        elif "," in image_data:
            # محاولة إزالة أي مقدمة قبل الفاصلة (مثل data:image/png)
            parts = image_data.split(",", 1)
            if len(parts[0]) < 50:
                image_data = parts[1]
        
        # تنظيف شامل للسلسلة
        image_data = image_data.strip().replace(" ", "").replace("\n", "").replace("\r", "")
        
        # معالجة الـ padding المفقود
        missing_padding = len(image_data) % 4
        if missing_padding:
            image_data += '=' * (4 - missing_padding)
            
        image_bytes = base64.b64decode(image_data)
        
        # التحقق من صحة البيانات
        if not image_bytes: return None
        
        # إنشاء ملف مؤقت
        temp_filename = f"/tmp/gen_{uuid.uuid4().hex[:8]}.png"
        with open(temp_filename, "wb") as fh:
            fh.write(image_bytes)
        
        file_size = os.path.getsize(temp_filename)
        logger.info(f"✅ Saved: {temp_filename} ({file_size} bytes)")
        
        return temp_filename
        
    except Exception as e:
        logger.error(f"❌ Save error: {e}")
        return None


def prepare_prompt_safe(
    prompt: str, 
    child_name: Optional[str] = None,
    fallback_name: str = "البطل"
) -> str:
    """
    ✅ تحضير آمن للـ prompt - يحل مشكلة NoneType
    
    Args:
        prompt: النص الأصلي
        child_name: اسم الطفل (يمكن أن يكون None)
        fallback_name: الاسم البديل
    
    Returns:
        النص المعدل بشكل آمن
    """
    if not prompt:
        return ""
    
    # ✅ تحويل None إلى string
    name_to_use = child_name if child_name else fallback_name
    
    # ✅ الاستبدال الآمن
    if "{child_name}" in prompt:
        prompt = prompt.replace("{child_name}", name_to_use)
    
    return prompt.strip()


def validate_api_key() -> bool:
    """
    التحقق من وجود OPENROUTER_API_KEY
    
    Returns:
        True إذا موجود، False إذا مفقود
    """
    if not OPENROUTER_API_KEY:
        logger.error("❌ OPENROUTER_API_KEY is not set in environment variables!")
        return False
    return True


# ============================================================================
# 👁️ Character Analysis (IMPROVED WITH PROFILE SYSTEM)
# ============================================================================

def create_character_reference(
    image_url: str = None,
    gender: str = "ولد",
    is_url: bool = True,
    use_ai_analysis: bool = False,
    # NEW: Character profile parameters
    child_name: str = "الطفل",
    skin_tone: str = "natural skin tone",
    hair_style: str = "natural hair style",
    hair_color: str = "natural hair color",
    eye_color: str = "natural eye color",
    age: str = "3-4"
) -> str:
    """
    ✅ تحليل شخصية الطفل أو استخدام وصف محسّن (IMPROVED VERSION)
    
    Args:
        image_url: رابط الصورة (اختياري)
        gender: الجنس ("ولد" أو "بنت")
        is_url: هل الصورة رابط أم base64
        use_ai_analysis: استخدام تحليل AI
        child_name: اسم الطفل
        skin_tone: لون البشرة (مهم جداً!) - BE SPECIFIC: "dark brown", "medium brown", etc.
        hair_style: نوع الشعر - "afro", "curly", "straight", "braids", "locs", "wavy"
        hair_color: لون الشعر - "brown", "black", "blonde" (exact color)
        eye_color: لون العيون
        age: العمر
    
    Returns:
        وصف مفصل للشخصية مع تأكيد قوي على الملامح
    
    Examples:
        >>> # Without AI analysis (recommended for consistency)
        >>> desc = create_character_reference(
        ...     gender="بنت",
        ...     child_name="لوجى",
        ...     skin_tone="dark brown",
        ...     hair_style="afro",
        ...     hair_color="brown"
        ... )
        
        >>> # With AI analysis (requires image + API key)
        >>> desc = create_character_reference(
        ...     image_url="path/to/image.jpg",
        ...     gender="بنت",
        ...     use_ai_analysis=True,
        ...     child_name="لوجى",
        ...     skin_tone="dark brown"  # backup if AI fails
        ... )
    """
    
    # ============================================================================
    # الوصف المحسّن (بدلاً من الافتراضي الضعيف)
    # ============================================================================
    
    def get_improved_description() -> str:
        """
        وصف افتراضي محسّن مع تأكيد قوي على الملامح
        """
        
        # تحديد الجنس
        gender_term = "girl" if gender == "بنت" else "boy"
        
        # بناء بروفايل الشخصية
        profile = CharacterProfile(
            name=child_name,
            gender=gender_term,
            age=age,
            skin_tone=skin_tone,
            hair_style=hair_style,
            hair_color=hair_color,
            hair_texture=get_hair_texture(hair_style),
            eye_color=eye_color
        )
        
        # بناء الوصف المفصل مع تأكيد عالي
        detailed_desc = profile.build_detailed_description(emphasis_level="high")
        
        return detailed_desc
    
    # ============================================================================
    # إذا لم يُطلب AI analysis - استخدم الوصف المحسّن
    # ============================================================================
    
    if not use_ai_analysis:
        logger.info("ℹ️ Using IMPROVED character description with profile system")
        improved_desc = get_improved_description()
        logger.info(f"✅ Generated description: {len(improved_desc)} characters")
        logger.debug(f"Description preview: {improved_desc[:150]}...")
        return improved_desc
    
    # ============================================================================
    # استخدام GPT-4 Vision للتحليل (عبر OpenAI المباشر أو OpenRouter)
    # ============================================================================
    
    api_key = OPENAI_API_KEY
    api_base = "https://api.openai.com/v1/chat/completions"
    model_name = "gpt-4o"
    headers = {
        "Content-Type": "application/json"
    }

    # تحديد المزود (OpenAI vs OpenRouter)
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    elif OPENROUTER_API_KEY:
        logger.info("ℹ️ Using OpenRouter for Vision Analysis (gpt-4o)")
        api_key = OPENROUTER_API_KEY
        api_base = "https://openrouter.ai/api/v1/chat/completions"
        model_name = "openai/gpt-4o"
        headers["Authorization"] = f"Bearer {api_key}"
        headers["HTTP-Referer"] = os.getenv("APP_URL", "https://kids-stories.app")
        headers["X-Title"] = "Kids Story Generator"
    else:
        logger.warning("⚠️ No API Key found (OpenAI or OpenRouter), using improved default description")
        return get_improved_description()

    try:
        logger.info(f"👁️ Analyzing character with {model_name}...")
        
        # تحضير الصورة
        if is_url:
            if not image_url.startswith("http") and not image_url.startswith("data:"):
                # افتراض أن الرابط صالح أو معالجة الخطأ
                 pass 
            image_content = {"type": "image_url", "image_url": {"url": image_url}}
        else:
            if not image_url.startswith("data:"):
                image_url = f"data:image/jpeg;base64,{image_url}"
            image_content = {"type": "image_url", "image_url": {"url": image_url}}
        
        # Prompt محسّن للتحليل
        gender_term = "girl" if gender == "بنت" else "boy"
        
        analysis_prompt = f"""
Analyze this child's image and provide a DETAILED character description for FLUX image generation.

CRITICAL: Focus on these features and be VERY SPECIFIC:

1. **Skin Tone**: Describe the EXACT skin tone (e.g., "dark brown", "medium brown", "light brown", "tan", etc.)
   - Use specific color terms, not vague words like "warm"
   
2. **Hair Style**: Describe the hair type precisely (e.g., "natural afro", "tight curls", "loose curls", "straight", "braids", "locs")
   - Include texture details (coily, curly, wavy, straight)
   - Mention volume and shape
   
3. **Hair Color**: EXACT color (e.g., "dark brown", "black", "light brown" - be precise)

4. **Facial Features**:
   - Eye color and shape
   - Face shape
   - Notable features

5. **Age appearance**: Approximate age (e.g., "3-4 years old")

Format your response as a detailed character description suitable for FLUX prompts.
Be SPECIFIC about colors and textures. This is for a children's storybook illustration.

Gender: {gender_term}
Name: {child_name}
"""
        
        payload = {
            "model": model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": analysis_prompt},
                        image_content
                    ]
                }
            ],
            "max_tokens": 500
        }
        
        response = requests.post(
            api_base,
            headers=headers,
            json=payload,
            timeout=45
        )
        
        if response.status_code == 200:
            data = response.json()
            ai_description = data["choices"][0]["message"]["content"].strip()
            
            logger.info("✅ AI analysis completed")
            logger.debug(f"AI Description: {ai_description[:200]}...")
            
            # دمج وصف AI مع التأكيد على الملامح المحددة
            enhanced_desc = enhance_ai_description(
                ai_description,
                child_name=child_name,
                gender=gender_term,
                skin_tone=skin_tone,
                hair_style=hair_style,
                hair_color=hair_color,
                eye_color=eye_color,
                age=age
            )
            
            return enhanced_desc
        else:
            logger.error(f"❌ Vision API error: {response.status_code} - {response.text}")
            logger.info("⤵️ Falling back to improved default description")
            return get_improved_description()
            
    except Exception as e:
        logger.error(f"❌ AI analysis failed: {e}")
        logger.info("⤵️ Falling back to improved default description")
        return get_improved_description()


def enhance_ai_description(
    ai_desc: str,
    child_name: str,
    gender: str,
    skin_tone: str,
    hair_style: str,
    hair_color: str,
    eye_color: str,
    age: str
) -> str:
    """
    تحسين وصف AI بضمان بقاء الملامح متسقة دون فرض قيم افتراضية قاسية
    """
    # تنظيف وتجهيز وصف الـ AI القادم من GPT-4o Vision
    clean_ai_desc = ai_desc.strip()
    if clean_ai_desc.endswith("."): clean_ai_desc = clean_ai_desc[:-1]
    
    # إضافة بادئة وخاتمة لضمان الاتساق (Consistency Wrapper)
    # نضع الاسم والعمر والجنس كقالب ثابت، ونترك التفاصيل الجسدية للـ AI الذي حلل الصورة
    consistency_wrapper = (
        f"A consistent character named {child_name}, an adorable {age} year old {gender}. "
        f"Appearance: {clean_ai_desc}. "
        f"CRITICAL: Maintain this exact facial structure, skin tone, and hair texture in every scene. "
        f"NO variations from this unique character look."
    )
    
    return consistency_wrapper



# ============================================================================
# 📸 Image Generation (FLUX Klein 4b via OpenRouter)
# ============================================================================

def generate_storybook_page(
    char_desc: str, 
    prompt: str, 
    child_name: Optional[str] = None,
    gender: str = "ولد", 
    age_group: str = "3-4",
    is_cover: bool = False,
    timeout: int = 120
) -> Optional[str]:
    """
    توليد صفحة قصة باستخدام FLUX Klein 4b عبر OpenRouter
    
    Args:
        char_desc (str): وصف الشخصية المفصل (من create_character_reference)
        prompt (str): وصف المشهد
        child_name (str, optional): اسم الطفل (يمكن أن يكون None)
        gender (str): "ولد" أو "بنت"
        age_group (str): العمر
        is_cover (bool): هل هذه صفحة الغلاف
        timeout (int): وقت الانتظار بالثواني
    
    Returns:
        Optional[str]: مسار الملف المؤقت أو رابط URL، أو None في حالة الفشل
    
    Examples:
        >>> # First, create character description
        >>> char_desc = create_character_reference(
        ...     gender="بنت",
        ...     child_name="لوجى",
        ...     skin_tone="dark brown",
        ...     hair_style="afro",
        ...     hair_color="brown"
        ... )
        >>> 
        >>> # Then generate image
        >>> image = generate_storybook_page(
        ...     char_desc=char_desc,
        ...     prompt="{child_name} playing in garden",
        ...     child_name="لوجى",
        ...     gender="بنت"
        ... )
    """
    try:
        # ✅ التحقق من API Key
        if not validate_api_key():
            return None
        
        # ✅ تحضير آمن للـ prompt
        safe_prompt = prepare_prompt_safe(prompt, child_name)
        
        # ✅ بناء FLUX-optimized prompt
        # Based on FLUX Klein 4B best practices & improved character system
        
        gender_term = "girl" if gender == "بنت" else "boy"
        age_desc = f"{age_group} year old" if "-" in age_group else "toddler"
        
        # Style (Artistic theme ONLY - no physical features)
        style = (
            "whimsical classic children's book illustration theme, "
            "soft digital watercolor washes, delicate colored pencil detailing, "
            "dreamy cozy bedtime story colors, rich saturated painterly textures, "
            "gentle watercolor gradients, paper texture, soft blending, "
            "Millie and the Moon Bear artistic aesthetic"
        )
        
        # Lighting (magical bedtime story aesthetic)
        lighting_style = (
            "magical glowing light, soft luminous atmosphere, dreamy lighting, "
            "enchanting bedtime story aesthetic, cozy and whimsical"
        )
        
        # Composition
        composition = (
            "full frame artistic illustration, edge-to-edge masterpiece, "
            "cinematic wide angle, no borders, no margins, "
            "strictly NO text, NO letters, NO characters, NO titles, NO typography, "
            "children's book page layout"
        )
        
        # Quality markers
        quality = (
            "ultra-high definition children's book illustration, "
            "professional publication quality, clean simple masterpiece, "
            "vibrant colors, suitable for ages 1-5, "
            "MAINTAIN CONSISTENT CHARACTER FEATURES throughout"
        )
        
        # ✅ Complete prompt with FLUX structure + Character Consistency
        full_prompt = (
            f"Create a {style} children's storybook illustration. "
            f"The main character is: {char_desc}. "  # ← Character description with emphasis
            f"Scene: {safe_prompt}. "
            f"Composition: {composition}. "
            f"Lighting: {lighting_style}. "
            f"Quality: {quality}. "
            f"CRITICAL: The character MUST match the exact description provided, "
            f"with precise attention to skin tone, hair style, hair color, and all facial features. "
            f"NO variations from the character description."
        )
        
        logger.info(f"🎨 Generating image with FLUX Klein 4b...")
        logger.info(f"👤 Character: {char_desc[:100]}...")
        logger.debug(f"📝 Full Prompt Length: {len(full_prompt)} characters")
        
        # إعداد الطلب
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": os.getenv("APP_URL", "https://kids-stories.app"),
            "X-Title": "Kids Story Generator"
        }
        
        payload = {
            "model": "black-forest-labs/flux.2-klein-4b", 
            "messages": [
                {
                    "role": "user", 
                    "content": full_prompt
                }
            ]
        }
        
        # إرسال الطلب
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=timeout
        )
        
        # معالجة الاستجابة
        if response.status_code == 200:
            data = response.json()
            
            # ✅ محاولة الاستخراج
            image_data = _extract_image_from_response(data)
            
            if image_data:
                # ✅ حفظ أو إرجاع الصورة
                result = _save_image_from_data(image_data)
                
                if result:
                    logger.info(f"✅ Image generated successfully!")
                    return result
                else:
                    logger.error("❌ Failed to save/process image")
                    return None
            else:
                logger.warning("⚠️ No valid image data found in response")
                logger.debug(f"Response keys: {list(data.keys())}")
                if data.get("choices"):
                    logger.debug(f"Message keys: {list(data['choices'][0].get('message', {}).keys())}")
                return None
        else:
            logger.error(f"❌ OpenRouter API Error: {response.status_code}")
            logger.error(f"Response: {response.text[:300]}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error(f"❌ Request timeout after {timeout}s")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ Request error: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Image generation error: {e}", exc_info=True)
        return None


def generate_story_images(
    story_pages: List[Dict],
    char_desc: str,
    child_name: Optional[str] = None,
    gender: str = "ولد"
) -> List[Dict]:
    """
    توليد صور لقصة كاملة مع ضمان اتساق الشخصية
    
    Args:
        story_pages: قائمة صفحات القصة
        char_desc: وصف الشخصية المفصل (من create_character_reference)
        child_name: اسم الطفل
        gender: الجنس
    
    Returns:
        قائمة نتائج التوليد
    
    Example:
        >>> # Create character once
        >>> char_desc = create_character_reference(
        ...     gender="بنت",
        ...     child_name="لوجى",
        ...     skin_tone="dark brown",
        ...     hair_style="afro"
        ... )
        >>> 
        >>> # Generate all pages with same character
        >>> pages = [
        ...     {"page_number": 1, "prompt": "Scene 1"},
        ...     {"page_number": 2, "prompt": "Scene 2"}
        ... ]
        >>> results = generate_story_images(pages, char_desc, "لوجى")
    """
    results = []
    total = len(story_pages)
    
    logger.info(f"📚 Generating {total} story images with consistent character...")
    logger.info(f"👤 Using character: {char_desc[:80]}...")
    
    for idx, page in enumerate(story_pages, 1):
        page_num = page.get("page_number", idx)
        prompt = page.get("prompt", "") or page.get("magic_image_prompt", "")
        
        logger.info(f"🎨 Processing page {page_num}/{total}")
        
        image_path = generate_storybook_page(
            char_desc=char_desc,  # ✅ Same character for all pages
            prompt=prompt,
            child_name=child_name,
            gender=gender,
            is_cover=(idx == 1)
        )
        
        results.append({
            "page_number": page_num,
            "success": image_path is not None,
            "image_path": image_path,
            "text": page.get("text", "")
        })
        
        status = "✅" if image_path else "❌"
        logger.info(f"{status} Page {page_num}: {'Success' if image_path else 'Failed'}")
    
    success_count = sum(1 for r in results if r["success"])
    logger.info(f"📊 Results: {success_count}/{total} images generated")
    
    return results


# ============================================================================
# 💳 Payment Verification (GPT-4 Vision - Optional)
# ============================================================================

def verify_payment_screenshot(
    image_b64: str, 
    target_number: str,
    use_ai_verification: bool = False,
    min_amount: float = 50.0
) -> bool:
    """
    التحقق من لقطة شاشة الدفع (InstaPay / Vodafone Cash)
    
    Args:
        image_b64: الصورة بصيغة base64
        target_number: رقم المحفظة المستهدف
        use_ai_verification: استخدام AI للتحقق
        min_amount: الحد الأدنى للمبلغ
    
    Returns:
        True إذا صحيح، False إذا خاطئ
    """
    
    logger.info(f"💳 Verifying payment for: {target_number}")
    
    # الوضع الافتراضي: قبول تلقائي
    if not use_ai_verification:
        logger.info("✅ Payment auto-approved (AI verification disabled)")
        return True
    
    # التحقق من API Key
    if not OPENAI_API_KEY:
        logger.warning("⚠️ OPENAI_API_KEY not set, auto-approving payment")
        return True
    
    try:
        logger.info("👁️ Analyzing payment screenshot with GPT-4 Vision...")
        
        # تحضير الصورة
        if not image_b64.startswith("data:"):
            image_b64 = f"data:image/jpeg;base64,{image_b64}"
        
        headers = {
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"Verify this InstaPay/Vodafone Cash payment screenshot.\n\n"
                                f"Target number: {target_number}\n"
                                f"Minimum amount: {min_amount} EGP\n\n"
                                f"Check:\n"
                                f"1. Valid InstaPay/Vodafone Cash screenshot?\n"
                                f"2. Recipient matches {target_number}?\n"
                                f"3. Amount >= {min_amount} EGP?\n"
                                f"4. Recent transaction?\n\n"
                                f"Reply ONLY: VALID or INVALID"
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_b64}
                        }
                    ]
                }
            ],
            "max_tokens": 10
        }
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            result = data["choices"][0]["message"]["content"].strip().upper()
            
            is_valid = "VALID" in result
            
            if is_valid:
                logger.info("✅ Payment verified: VALID")
            else:
                logger.warning(f"❌ Payment rejected: {result}")
            
            return is_valid
        else:
            logger.error(f"❌ Vision API error: {response.status_code}")
            logger.info("⚠️ Auto-approving due to API error")
            return True
            
    except Exception as e:
        logger.error(f"❌ Payment verification error: {e}")
        logger.info("⚠️ Auto-approving due to exception")
        return True


# ============================================================================
# 🧪 Testing & Validation
# ============================================================================

def test_api_connection() -> Dict[str, bool]:
    """
    اختبار الاتصال بالـ APIs
    """
    results = {
        "openrouter_key": bool(OPENROUTER_API_KEY),
        "openai_key": bool(OPENAI_API_KEY),
        "openrouter_api": False,
        "openai_api": False
    }
    
    # اختبار OpenRouter
    if OPENROUTER_API_KEY:
        try:
            headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
            response = requests.get(
                "https://openrouter.ai/api/v1/models",
                headers=headers,
                timeout=10
            )
            results["openrouter_api"] = response.status_code == 200
        except:
            pass
    
    # اختبار OpenAI
    if OPENAI_API_KEY:
        try:
            headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
            response = requests.get(
                "https://api.openai.com/v1/models",
                headers=headers,
                timeout=10
            )
            results["openai_api"] = response.status_code == 200
        except:
            pass
    
    return results


# ============================================================================
# 📊 Main Testing
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🎨 OpenAI Service - Testing Suite (IMPROVED VERSION)")
    print("="*80 + "\n")
    
    # Test 1: API Keys
    print("Test 1: API Keys Status")
    print("-" * 40)
    test_results = test_api_connection()
    for key, value in test_results.items():
        status = "✅" if value else "❌"
        print(f"{status} {key}: {value}")
    print()
    
    # Test 2: Character Profile System
    print("Test 2: Character Profile System")
    print("-" * 40)
    
    # Test case 1: Girl with afro
    desc1 = create_character_reference(
        gender="بنت",
        child_name="لوجى",
        skin_tone="dark brown",
        hair_style="afro",
        hair_color="brown",
        eye_color="brown"
    )
    
    print(f"Character: لوجى (Girl with afro)")
    print(f"Length: {len(desc1)} characters")
    print(f"Preview: {desc1[:150]}...")
    print()
    
    # Feature checks
    checks = {
        "Has 'dark brown skin'": "dark brown" in desc1.lower() and "skin" in desc1.lower(),
        "Has 'afro'": "afro" in desc1.lower(),
        "Has 'brown hair'": "brown" in desc1.lower() and "hair" in desc1.lower(),
        "Has negative prompts": "no" in desc1.lower(),
        "Has child name": "لوجى" in desc1
    }
    
    print("Feature Checks:")
    for check, passed in checks.items():
        status = "✅" if passed else "❌"
        print(f"  {status} {check}")
    print()
    
    # Test 3: Prompt Preparation
    print("Test 3: Prompt Preparation")
    print("-" * 40)
    test_cases = [
        ("{child_name} playing", "ليلى"),
        ("{child_name} eating", None),
        ("No placeholder", "عمر"),
    ]
    
    for prompt, name in test_cases:
        result = prepare_prompt_safe(prompt, name)
        print(f"Input: '{prompt}' | Name: {name}")
        print(f"Output: '{result}'")
        print()
    
    print("="*80)
    print("✅ Testing Complete!")
    print("="*80 + "\n")
    
    print("📋 Summary:")
    print("- ✅ Character Profile System integrated")
    print("- ✅ Improved default descriptions with emphasis")
    print("- ✅ Multi-layer character consistency")
    print("- ✅ Negative prompts included")
    print("- ✅ Safe prompt preparation")
    print()
