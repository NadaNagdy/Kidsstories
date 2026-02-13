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
    """تحضير النص ليدعم الحروف المركبة مثل (لا) والتنوين والهمزات"""
    if not text: return ""
    
    # إعدادات تجبر المكتبة على رسم الحروف كاملة وبدون أخطاء
    configuration = {
        'delete_harakat': False,      # الحفاظ على التشكيل لجمال الخط
        'support_ligatures': True,     # حل مشكلة حرف (لا) والحروف المتصلة
        'arabic': True
    }
    reshaper = arabic_reshaper.ArabicReshaper(configuration=configuration)
    reshaped_text = reshaper.reshape(text)
    return get_display(reshaped_text)

def _get_arabic_font(size: int, weight: str = "bold") -> ImageFont.FreeTypeFont:
    """تحميل الخطوط التي رفعتها مع ضمان الدقة"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(base_dir, "fonts")
    
    # تحديد اسم الملف بناءً على ما قمت برفعه بالضبط
    suffix = "-Bold.ttf" if weight.lower() == "bold" else "-Regular.ttf"
    
    # المحاولة الأولى: Cairo (للأناقة والوضوح)
    cairo_path = os.path.join(fonts_dir, f"Cairo{suffix}")
    if os.path.exists(cairo_path):
        return ImageFont.truetype(cairo_path, size)
    
    # المحاولة الثانية: Almarai
    almarai_path = os.path.join(fonts_dir, f"Almarai{suffix}")
    if os.path.exists(almarai_path):
        return ImageFont.truetype(almarai_path, size)

    return ImageFont.load_default()

# ---------------------------------------------------------------------------
# 2. وظائف إنشاء الصور (تأثيرات البروز والوضوح)
# ---------------------------------------------------------------------------

def create_cover_page(image_url, value, child_name, gender, output_path):
    """إنشاء الغلاف بملء الصفحة مع نصوص بارزة"""
    try:
        width, height = 1024, 1024
        art_source = get_image_source(image_url)
        if not art_source: return None
        
        # 1. تكبير الصورة لتملأ الصفحة تماماً
        img = art_source.convert("RGB").resize((width, height), Image.LANCZOS)
        draw = ImageDraw.Draw(img)
        
        # أحجام الخطوط
        title_font = _get_arabic_font(120, weight="bold")
        name_font = _get_arabic_font(100, weight="bold")

        # 2. رسم العنوان (بطل/بطلة القيمة) في الأعلى
        prefix = "بطلة" if gender == "female" else "بطل"
        top_text = f"{prefix} {value}"
        reshaped_top = _prepare_arabic_text(top_text)
        tw = draw.textbbox((0, 0), reshaped_top, font=title_font)[2]
        tx, ty = (width - tw) // 2, 80
        
        # Stroke عريض لضمان القراءة فوق أي خلفية
        draw.text((tx, ty), reshaped_top, font=title_font, fill=(255, 255, 255), 
                  stroke_width=6, stroke_fill=(45, 30, 20))
        draw.text((tx, ty), reshaped_top, font=title_font, fill=(45, 30, 20))

        # 3. اسم الطفل في الأسفل
        reshaped_name = _prepare_arabic_text(child_name)
        nw = draw.textbbox((0, 0), reshaped_name, font=name_font)[2]
        nx, ny = (width - nw) // 2, 850
        
        draw.text((nx, ny), reshaped_name, font=name_font, fill=(255, 255, 255),
                  stroke_width=6, stroke_fill=(60, 40, 30))
        draw.text((nx, ny), reshaped_name, font=name_font, fill=(60, 40, 30))

        img.save(output_path, quality=100, subsampling=0) 
        return output_path
    except Exception as e:
        print(f"❌ Error in create_cover_page: {e}")
        return None

def overlay_text_on_image(image_url, text, output_path):
    """دمج نصوص القصة فوق صورة تملأ الصفحة بلمسة جمالية"""
    try:
        width, height = 1024, 1024
        art_source = get_image_source(image_url)
        if not art_source: return None
        
        # 1. الصورة تملأ الصفحة
        img = art_source.convert("RGB").resize((width, height), Image.LANCZOS)
        draw = ImageDraw.Draw(img)
        
        # 2. إعداد الخط
        font = _get_arabic_font(55, weight="bold")
        reshaped_text = _prepare_arabic_text(text)
        
        # 3. رسم صندوق خلفية للنص لضمان الوضوح (نصف شفاف)
        # تقسيم النص لسطور إذا كان طويلاً
        lines = []
        words = text.split()
        current_line = []
        for word in words:
            current_line.append(word)
            test_line = " ".join(current_line)
            if draw.textlength(_prepare_arabic_text(test_line), font=font) > 900:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        lines.append(" ".join(current_line))
        
        line_height = 70
        total_height = len(lines) * line_height + 40
        
        # رسم مستطيل خلفية داكن وشفاف في الأسفل
        rect_y = height - total_height - 60
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.rounded_rectangle([40, rect_y, width - 40, height - 40], 
                                      radius=20, fill=(0, 0, 0, 160))
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
        draw = ImageDraw.Draw(img)
        
        # 4. رسم النصوص المختزلة
        for i, line in enumerate(lines):
            line_reshaped = _prepare_arabic_text(line)
            lw = draw.textlength(line_reshaped, font=font)
            lx = (width - lw) // 2
            ly = rect_y + 20 + (i * line_height)
            draw.text((lx, ly), line_reshaped, font=font, fill=(255, 255, 255))

        img.save(output_path, quality=95, subsampling=0)
        return output_path
    except Exception as e:
        print(f"❌ Error in overlay_text_on_image: {e}")
        return None
