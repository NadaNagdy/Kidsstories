from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import requests
import base64
from io import BytesIO
import arabic_reshaper
from bidi.algorithm import get_display
def get_image_source(source):
    """
    دالة ذكية لفتح الصورة سواء كانت رابط URL أو مسار ملف محلي (مثل مخرجات Flux)
    """
    try:
        # إذا كان المدخل رابط يبدأ بـ http
        if isinstance(source, str) and source.startswith("http"):
            response = requests.get(source, timeout=15)
            return Image.open(BytesIO(response.content))
        
        # إذا كان مسار ملف موجود على السيرفر (/tmp/...)
        elif isinstance(source, str) and os.path.exists(source):
            return Image.open(source)
            
        # إذا كانت الصورة مفتوحة بالفعل (Image object)
        elif isinstance(source, Image.Image):
            return source
            
        return None
    except Exception as e:
        print(f"❌ Error in get_image_source: {e}")
        return None
# ---------------------------------------------------------------------------
# 1. محرك النصوص العربية (إصلاح الحروف الناقصة والروابط)
# ---------------------------------------------------------------------------

def _prepare_arabic_text(text: str) -> str:
    """تحضير النص ليكون مقروءاً وصحيحاً برمجياً"""
    if not text: return ""
    # استخدام الإعدادات الافتراضية الأكثر قوة وتوافقاً مع Pillow
    # تم تعطيل support_ligatures لأنها قد تسبب مربعات في بعض الخطوط
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

def _get_arabic_font(size: int, weight: str = "bold") -> ImageFont.FreeTypeFont:
    """تحميل الخطوط مع ضمان الدقة - Almarai هو الأفضل للوضوح"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(base_dir, "fonts")
    
    suffix = "-Bold.ttf" if weight.lower() == "bold" else "-Regular.ttf"
    
    almarai_path = os.path.join(fonts_dir, f"Almarai{suffix}")
    if os.path.exists(almarai_path):
        return ImageFont.truetype(almarai_path, size)
    
    cairo_path = os.path.join(fonts_dir, f"Cairo{suffix}")
    if os.path.exists(cairo_path):
        return ImageFont.truetype(cairo_path, size)

    return ImageFont.load_default()

def _detect_best_position(img):
    """تحليل الصورة للعثور على أفضل مساحة (أغمق مساحة) للنص الأصفر"""
    try:
        w, h = img.size
        # فحص الجزء العلوي (أول 30%) والجزء السفلي (آخر 30%)
        top_slice = img.crop((0, 0, w, int(h * 0.3))).convert("L")
        bottom_slice = img.crop((0, int(h * 0.7), w, h)).convert("L")
        
        top_bright = sum(top_slice.getdata()) / (w * int(h * 0.3))
        bottom_bright = sum(bottom_slice.getdata()) / (w * (h - int(h * 0.7)))
        
        # نختار المنطقة الأغمق ليكون النص الأصفر بارزاً جداً
        return "TOP" if top_bright < bottom_bright else "BOTTOM"
    except:
        return "BOTTOM"

# ---------------------------------------------------------------------------
# 2. وظائف إنشاء الصور (تحسين البروز والوضوح)
# ---------------------------------------------------------------------------

def create_cover_page(image_url, value, child_name, gender, output_path):
    """إنشاء الغلاف بملء الصفحة مع نصوص صفراء فائقة الوضوح"""
    try:
        width, height = 1024, 1024
        art_source = get_image_source(image_url)
        if not art_source: return None
        
        img = art_source.convert("RGB").resize((width, height), Image.LANCZOS)
        draw = ImageDraw.Draw(img)
        
        title_font = _get_arabic_font(115, weight="bold")
        name_font = _get_arabic_font(105, weight="bold")

        main_fill = (255, 235, 0)
        stroke_color = (0, 0, 0) # أسود للحدود لضمان البروز

        # 1. العنوان المسطح في الأعلى
        prefix = "بطلة" if gender == "female" else "بطل"
        top_text = f"{prefix} {value}"
        reshaped_top = _prepare_arabic_text(top_text)
        tw = draw.textbbox((0, 0), reshaped_top, font=title_font)[2]
        tx, ty = (width - tw) // 2, 80
        
        draw.text((tx, ty), reshaped_top, font=title_font, fill=main_fill, 
                  stroke_width=10, stroke_fill=stroke_color)

        # 2. اسم الطفل في الأسفل
        reshaped_name = _prepare_arabic_text(child_name)
        nw = draw.textbbox((0, 0), reshaped_name, font=name_font)[2]
        nx, ny = (width - nw) // 2, 860
        
        draw.text((nx, ny), reshaped_name, font=name_font, fill=main_fill,
                  stroke_width=10, stroke_fill=stroke_color)

        img.save(output_path, quality=100, subsampling=0) 
        return output_path
    except Exception as e:
        print(f"❌ Error in create_cover_page: {e}")
        return None

def overlay_text_on_image(image_url, text, output_path):
    """توزيع النص بذكاء في المساحات الفارغة بلون أصفر وبروز عالٍ"""
    try:
        width, height = 1024, 1024
        art_source = get_image_source(image_url)
        if not art_source: return None
        
        img = art_source.convert("RGB").resize((width, height), Image.LANCZOS)
        
        # تحديد أفضل مكان للنص
        position = _detect_best_position(img)
        draw = ImageDraw.Draw(img)
        
        font = _get_arabic_font(45, weight="bold")
        main_fill = (255, 235, 0)
        stroke_color = (0, 0, 0)
        
        # تقسيم النص لسطور
        lines = []
        words = text.split()
        current_line = []
        for word in words:
            current_line.append(word)
            test_line = " ".join(current_line)
            if draw.textlength(_prepare_arabic_text(test_line), font=font) > 960:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        lines.append(" ".join(current_line))
        
        line_height = 60
        total_height = len(lines) * line_height
        
        # اختيار الإحداثيات بناءً على ذكاء المساحة
        if position == "TOP":
            start_y = 60
        else:
            start_y = height - total_height - 100
        
        for i, line in enumerate(lines):
            line_reshaped = _prepare_arabic_text(line)
            lw = draw.textlength(line_reshaped, font=font)
            lx = (width - lw) // 2
            ly = start_y + (i * line_height)
            
            # رسم النص بحدود سميكة جداً لضمان القراءة
            draw.text((lx, ly), line_reshaped, font=font, fill=main_fill,
                      stroke_width=10, stroke_fill=stroke_color)

        img.save(output_path, quality=100, subsampling=0)
        return output_path
    except Exception as e:
        print(f"❌ Error in overlay_text_on_image: {e}")
        return None
