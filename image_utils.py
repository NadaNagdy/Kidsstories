from PIL import Image, ImageDraw, ImageFont
import os
import requests
import base64
from io import BytesIO
import arabic_reshaper
from bidi.algorithm import get_display

# ---------------------------------------------------------------------------
# Arabic typography helpers
# ---------------------------------------------------------------------------

def _prepare_arabic_text(text: str) -> str:
    """تحضير النص العربي ليظهر بشكل صحيح في Pillow"""
    if not text:
        return ""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)

def _wrap_arabic_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int):
    """تقسيم النص العربي إلى أسطر بناءً على عرض الصندوق"""
    words = text.split()
    if not words:
        return []

    lines = []
    current = ""

    for word in words:
        candidate_raw = (current + " " + word).strip()
        candidate_vis = _prepare_arabic_text(candidate_raw)
        bbox = draw.textbbox((0, 0), candidate_vis, font=font)
        candidate_width = bbox[2] - bbox[0]

        if candidate_width <= max_width or not current:
            current = candidate_raw
        else:
            lines.append(current)
            current = word

    if current:
        lines.append(current)

    return [_prepare_arabic_text(line) for line in lines]

def _get_arabic_font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    """تحميل الخطوط العربية مع معالجة الأخطاء"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(base_dir, "fonts")

    candidates = []
    if weight.lower() == "bold":
        candidates.append(os.path.join(fonts_dir, "Amiri-Bold.ttf"))
    candidates.append(os.path.join(fonts_dir, "Amiri-Regular.ttf"))

    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    return ImageFont.load_default()

# ---------------------------------------------------------------------------
# Image Processing Core
# ---------------------------------------------------------------------------

def get_image_source(image_input):
    """دالة ذكية لتحويل الرابط أو نص Base64 إلى صورة قابلة للمعالجة"""
    try:
        # الحالة الأولى: بيانات Base64
        if str(image_input).startswith("data:image") or ";base64," in str(image_input):
            if "," in str(image_input):
                header, encoded = str(image_input).split(",", 1)
            else:
                encoded = image_input
            image_data = base64.b64decode(encoded)
            return Image.open(BytesIO(image_data))
        
        # الحالة الثانية: رابط URL
        else:
            response = requests.get(image_input, timeout=20)
            if response.status_code == 200:
                return Image.open(BytesIO(response.content))
    except Exception as e:
        print(f"Error in get_image_source: {e}")
    return None

def _draw_story_text_box(draw, panel_width, panel_height, text, font, **kwargs):
    """رسم صندوق النص السفلي بنمط يتناسب مع قصص الأطفال"""
    if not text: return

    bg_color = kwargs.get('bg_color', (255, 251, 245)) 
    text_color = kwargs.get('text_color', (50, 30, 20)) 
    
    horizontal_margin = 50
    padding_x, padding_y = 30, 25
    box_width = panel_width - 2 * horizontal_margin
    max_text_width = box_width - 2 * padding_x

    lines = _wrap_arabic_text(draw, text, font, max_text_width)
    if not lines: return

    sample_bbox = draw.textbbox((0, 0), lines[0], font=font)
    line_height = sample_bbox[3] - sample_bbox[1]
    total_text_height = sum([line_height * 1.5 for _ in lines])
    box_height = int(total_text_height + 2 * padding_y)

    box_left = horizontal_margin
    box_bottom = panel_height - 40
    box_top = box_bottom - box_height

    draw.rounded_rectangle(
        [box_left, box_top, box_left + box_width, box_bottom],
        radius=20,
        fill=bg_color
    )

    current_y = box_top + padding_y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        draw.text((box_left + box_width - padding_x - line_w, current_y), line, font=font, fill=text_color)
        current_y += line_height * 1.5

def overlay_text_on_image(image_url, text, output_path):
    """دمج رسمة القصة مع النص العربي"""
    try:
        width, height = 1024, 1024
        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        # استخدام الدالة المساعدة الجديدة لدعم Base64/URL
        art_source = get_image_source(image_url)
        if not art_source: return None
        art = art_source.convert("RGB")
        
        art.thumbnail((900, 700), Image.LANCZOS)
        img.paste(art, ((width - art.width) // 2, 50))
        draw.rectangle([10, 10, 1014, 1014], outline=(200, 200, 200), width=15)

        font = _get_arabic_font(42)
        _draw_story_text_box(draw, width, height, text, font)

        img.save(output_path)
        return output_path
    except Exception as e:
        print(f"Error in overlay_text: {e}")
        return None

def create_cover_page(image_url, top_text, bottom_text, output_path):
    """إنشاء غلاف القصة الاحترافي"""
    try:
        width, height = 1024, 1024
        img = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        title_font = _get_arabic_font(85, weight="bold")
        name_font = _get_arabic_font(60)

        reshaped_top = _prepare_arabic_text(top_text)
        tw = draw.textbbox((0, 0), reshaped_top, font=title_font)[2]
        draw.text(((width - tw) // 2, 70), reshaped_top, font=title_font, fill=(60, 40, 30))

        # معالجة صورة الغلاف (دعم Base64/URL)
        art_source = get_image_source(image_url)
        if not art_source: return None
        art = art_source.convert("RGBA")
        
        size = (600, 600)
        art = art.resize(size, Image.LANCZOS)
        mask = Image.new('L', size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0) + size, fill=255)
        
        circular_art = Image.new('RGBA', size, (0, 0, 0, 0))
        circular_art.paste(art, (0, 0), mask=mask)
        img.paste(circular_art, ((width - size[0]) // 2, 200), circular_art)

        reshaped_name = _prepare_arabic_text(bottom_text)
        nw = draw.textbbox((0, 0), reshaped_name, font=name_font)[2]
        draw.text(((width - nw) // 2, 850), reshaped_name, font=name_font, fill=(80, 60, 50))

        img.save(output_path)
        return output_path
    except Exception as e:
        print(f"Cover Error: {e}")
        return None
