from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import requests
import base64
from io import BytesIO
import arabic_reshaper
from bidi.algorithm import get_display

# ---------------------------------------------------------------------------
# 1. مساعدات الطباعة الاحترافية (Arabic Typography)
# ---------------------------------------------------------------------------

def _prepare_arabic_text(text: str) -> str:
    """تحضير النص العربي مع دعم كامل للحروف المركبة والروابط (مثل لا)"""
    if not text: return ""
    
    # إعدادات متقدمة للمشكل (Reshaper) لضمان عدم سقوط أي حرف
    configuration = {
        'delete_harakat': False,      # الحفاظ على التشكيل إن وجد
        'support_ligatures': True,     # دعم الحروف المركبة مثل "لا"
        'arabic': True
    }
    reshaper = arabic_reshaper.ArabicReshaper(configuration=configuration)
    reshaped_text = reshaper.reshape(text)
    return get_display(reshaped_text)

def _wrap_arabic_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int):
    """تقسيم النص العربي إلى أسطر مع الحفاظ على التنسيق"""
    words = text.split()
    if not words: return []
    lines, current = [], ""
    for word in words:
        candidate_raw = (current + " " + word).strip()
        candidate_vis = _prepare_arabic_text(candidate_raw)
        bbox = draw.textbbox((0, 0), candidate_vis, font=font)
        if (bbox[2] - bbox[0]) <= max_width or not current:
            current = candidate_raw
        else:
            lines.append(current)
            current = word
    if current: lines.append(current)
    return [_prepare_arabic_text(line) for line in lines]

def _get_arabic_font(size: int, weight: str = "bold") -> ImageFont.FreeTypeFont:
    """تحميل الخطوط مع أولوية لخط Cairo Bold لضمان أعلى وضوح"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(base_dir, "fonts")
    
    suffix = "-Bold.ttf" if weight.lower() == "bold" else "-Regular.ttf"
    font_path = os.path.join(fonts_dir, f"Cairo{suffix}")

    if os.path.exists(font_path):
        return ImageFont.truetype(font_path, size)
    
    alt_path = os.path.join(fonts_dir, f"Almarai{suffix}")
    if os.path.exists(alt_path):
        return ImageFont.truetype(alt_path, size)

    return ImageFont.load_default()

# ---------------------------------------------------------------------------
# 2. معالجة الصور والنصوص (Image Processing)
# ---------------------------------------------------------------------------

def get_image_source(image_input):
    try:
        if str(image_input).startswith("data:image") or ";base64," in str(image_input):
            encoded = str(image_input).split(",", 1)[1] if "," in str(image_input) else image_input
            return Image.open(BytesIO(base64.b64decode(encoded)))
        else:
            response = requests.get(image_input, timeout=20)
            return Image.open(BytesIO(response.content)) if response.status_code == 200 else None
    except Exception as e:
        print(f"Source Error: {e}")
    return None

def create_cover_page(image_url, top_text, bottom_text, output_path):
    """إنشاء غلاف احترافي مع معالجة ذكية للخطوط لتبدو حادة وغير ممسوحة"""
    try:
        width, height = 1024, 1024
        img = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        title_font = _get_arabic_font(130, weight="bold")
        name_font = _get_arabic_font(115, weight="bold")

        # 1. العنوان العلوي (بطل القيمة) - استخدام Stroke للوضوح العالي
        reshaped_top = _prepare_arabic_text(top_text)
        tw = draw.textbbox((0, 0), reshaped_top, font=title_font)[2]
        tx, ty = (width - tw) // 2, 70
        
        # إضافة حد خارجي (Stroke) بسيط يجعل الخط حاداً جداً
        draw.text((tx, ty), reshaped_top, font=title_font, fill=(45, 30, 20), 
                  stroke_width=2, stroke_fill=(45, 30, 20))

        # 2. الصورة (مرتبطة بالذكاء الاصطناعي - نظيفة وبدون نصوص)
        art_source = get_image_source(image_url)
        if art_source:
            art = art_source.convert("RGBA")
            art = art.resize((660, 660), Image.LANCZOS)
            mask = Image.new('L', (660, 660), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, 660, 660), fill=255)
            img.paste(art, ((width - 660) // 2, 220), mask=mask)

        # 3. اسم الطفل السفلي (تأثير Glow + Stroke)
        reshaped_name = _prepare_arabic_text(bottom_text)
        nw = draw.textbbox((0, 0), reshaped_name, font=name_font)[2]
        nx, ny = (width - nw) // 2, 865
        
        # رسم توهج خلفي (Glow)
        for off in [(-3,-3), (3,-3), (-3,3), (3,3)]:
            draw.text((nx+off[0], ny+off[1]), reshaped_name, font=name_font, fill=(245, 245, 245))
        
        # النص الأساسي مع Stroke خفيف
        draw.text((nx, ny), reshaped_name, font=name_font, fill=(60, 40, 30),
                  stroke_width=1, stroke_fill=(60, 40, 30))

        img.save(output_path, quality=100, subsampling=0) 
        return output_path
    except Exception as e:
        print(f"Cover Error: {e}")
        return None

def overlay_text_on_image(image_url, text, output_path):
    """دمج صفحات القصة بنص عربي واضح داخل صندوق ناعم وبخط عريض"""
    try:
        width, height = 1024, 1024
        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        art_source = get_image_source(image_url)
        if art_source:
            art = art_source.convert("RGB")
            art.thumbnail((940, 780), Image.LANCZOS)
            img.paste(art, ((width - art.width) // 2, 35))

        # استخدام حجم خط كبير (60) لضمان سهولة القراءة
        font = _get_arabic_font(60, weight="bold")
        _draw_story_text_box(draw, width, height, text, font)
        
        img.save(output_path, quality=95, subsampling=0)
        return output_path
    except Exception as e:
        print(f"Page Error: {e}")
        return None

def _draw_story_text_box(draw, panel_width, panel_height, text, font):
    """رسم صندوق النص بنمط 'كريمي' وحواف دائرية ونصوص حادة"""
    horizontal_margin = 60
    padding_x, padding_y = 45, 40
    box_width = panel_width - 2 * horizontal_margin
    lines = _wrap_arabic_text(draw, text, font, box_width - 2 * padding_x)
    if not lines: return

    line_bbox = draw.textbbox((0, 0), lines[0], font=font)
    line_height = line_bbox[3] - line_bbox[1]
    box_height = int((line_height * 1.7 * len(lines)) + 2 * padding_y)
    box_top = (panel_height - 50) - box_height

    # رسم خلفية الصندوق
    draw.rounded_rectangle(
        [horizontal_margin, box_top, horizontal_margin + box_width, panel_height - 50],
        radius=35, fill=(255, 255, 254)
    )

    current_y = box_top + padding_y
    for line in lines:
        line_w = draw.textbbox((0, 0), line, font=font)[2] - draw.textbbox((0, 0), line, font=font)[0]
        # كتابة النص مع Stroke بسيط لضمان عدم اختفاء أي حرف في الطباعة
        draw.text((horizontal_margin + box_width - padding_x - line_w, current_y), 
                  line, font=font, fill=(40, 30, 20), stroke_width=1, stroke_fill=(40, 30, 20))
        current_y += line_height * 1.7
