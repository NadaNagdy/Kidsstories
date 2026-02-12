from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import requests
import base64
from io import BytesIO
import arabic_reshaper
from bidi.algorithm import get_display

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

def create_cover_page(image_url, top_text, bottom_text, output_path):
    """إنشاء الغلاف بخطوط حادة جداً ومساحات نظيفة"""
    try:
        width, height = 1024, 1024
        img = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # أحجام الخطوط المثالية للغلاف
        title_font = _get_arabic_font(130, weight="bold")
        name_font = _get_arabic_font(115, weight="bold")

        # 1. رسم العنوان (بطل القيمة) مع Stroke لزيادة الحدة
        reshaped_top = _prepare_arabic_text(top_text)
        tw = draw.textbbox((0, 0), reshaped_top, font=title_font)[2]
        tx, ty = (width - tw) // 2, 70
        
        # رسم النص بـ Stroke يمنع بهتان الحواف
        draw.text((tx, ty), reshaped_top, font=title_font, fill=(45, 30, 20), 
                  stroke_width=2, stroke_fill=(45, 30, 20))

        # 2. رسم صورة الطفل (دائرية)
        art_source = get_image_source(image_url)
        if art_source:
            art = art_source.convert("RGBA").resize((660, 660), Image.LANCZOS)
            mask = Image.new('L', (660, 660), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 660, 660), fill=255)
            img.paste(art, ((width - 660) // 2, 220), mask=mask)

        # 3. اسم الطفل مع توهج وحماية خلفية
        reshaped_name = _prepare_arabic_text(bottom_text)
        nw = draw.textbbox((0, 0), reshaped_name, font=name_font)[2]
        nx, ny = (width - nw) // 2, 865
        
        # رسم "هالة" بيضاء خفيفة خلف الاسم لزيادة التباين
        draw.text((nx, ny), reshaped_name, font=name_font, fill=(60, 40, 30),
                  stroke_width=3, stroke_fill=(255, 255, 255))

        img.save(output_path, quality=100, subsampling=0) 
        return output_path
    except Exception as e:
        return None

def overlay_text_on_image(image_url, text, output_path):
    """دمج صفحات القصة بصندوق نص واضح"""
    try:
        width, height = 1024, 1024
        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        art_source = get_image_source(image_url)
        if art_source:
            art = art_source.convert("RGB")
            art.thumbnail((940, 780), Image.LANCZOS)
            img.paste(art, ((width - art.width) // 2, 35))

        # حجم خط كبير (60) لضمان سهولة القراءة
        font = _get_arabic_font(60, weight="bold")
        _draw_story_text_box(draw, width, height, text, font)
        
        img.save(output_path, quality=95, subsampling=0)
        return output_path
    except Exception as e:
        return None
