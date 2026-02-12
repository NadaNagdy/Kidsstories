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
    if not text: return ""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)

def _wrap_arabic_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int):
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

def _get_arabic_font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(base_dir, "fonts")
    
    # الترتيب: Cairo ثم Almarai لضمان أفضل مظهر للأطفال
    candidates = []
    suffix = "-Bold.ttf" if weight.lower() == "bold" else "-Regular.ttf"
    for family in ["Cairo", "Almarai", "Amiri"]:
        candidates.append(os.path.join(fonts_dir, family + suffix))

    for path in candidates:
        if os.path.exists(path):
            try: return ImageFont.truetype(path, size)
            except: continue
    return ImageFont.load_default()

# ---------------------------------------------------------------------------
# Image Processing Core
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
    """إنشاء غلاف احترافي مع تأثير الظل (Glow) للنصوص"""
    try:
        width, height = 1024, 1024
        img = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # خطوط ضخمة وواضحة
        title_font = _get_arabic_font(120, weight="bold")
        name_font = _get_arabic_font(105, weight="bold")

        # 1. رسم العنوان العلوي (بطل/بطلة الشجاعة) مع ظل خفيف
        reshaped_top = _prepare_arabic_text(top_text)
        tw = draw.textbbox((0, 0), reshaped_top, font=title_font)[2]
        tx, ty = (width - tw) // 2, 60
        
        # طبقة الظل (Offset Shadow)
        draw.text((tx+3, ty+3), reshaped_top, font=title_font, fill=(210, 210, 210)) 
        # النص الأساسي
        draw.text((tx, ty), reshaped_top, font=title_font, fill=(50, 35, 25))

        # 2. معالجة صورة الطفل في إطار دائري
        art_source = get_image_source(image_url)
        if not art_source: return None
        art = art_source.convert("RGBA")
        size = (620, 620)
        art = art.resize(size, Image.LANCZOS)
        mask = Image.new('L', size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0) + size, fill=255)
        circular_art = Image.new('RGBA', size, (0, 0, 0, 0))
        circular_art.paste(art, (0, 0), mask=mask)
        img.paste(circular_art, ((width - size[0]) // 2, 210), circular_art)

        # 3. رسم اسم الطفل مع تأثير البروز (Glow Effect)
        reshaped_name = _prepare_arabic_text(bottom_text)
        nw = draw.textbbox((0, 0), reshaped_name, font=name_font)[2]
        nx, ny = (width - nw) // 2, 850
        
        # رسم الظل بعدة اتجاهات لإعطاء مظهر التوهج (Soft Glow)
        shadow_color = (230, 230, 230)
        for off in [(-2,-2), (2,-2), (-2,2), (2,2), (3,3)]:
            draw.text((nx+off[0], ny+off[1]), reshaped_name, font=name_font, fill=shadow_color)
        
        # النص الأساسي (بني دافئ)
        draw.text((nx, ny), reshaped_name, font=name_font, fill=(70, 50, 40))

        img.save(output_path)
        return output_path
    except Exception as e:
        print(f"Cover Error: {e}")
        return None

def overlay_text_on_image(image_url, text, output_path):
    """دمج صفحات القصة الداخلية بنص واضح ومريح"""
    try:
        width, height = 1024, 1024
        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        art_source = get_image_source(image_url)
        if not art_source: return None
        art = art_source.convert("RGB")
        art.thumbnail((900, 720), Image.LANCZOS)
        img.paste(art, ((width - art.width) // 2, 40))

        font = _get_arabic_font(48) # تكبير طفيف لسهولة القراءة
        _draw_story_text_box(draw, width, height, text, font)
        img.save(output_path)
        return output_path
    except Exception as e:
        print(f"Page Error: {e}")
        return None

def _draw_story_text_box(draw, panel_width, panel_height, text, font):
    horizontal_margin = 50
    padding_x, padding_y = 35, 30
    box_width = panel_width - 2 * horizontal_margin
    lines = _wrap_arabic_text(draw, text, font, box_width - 2 * padding_x)
    if not lines: return

    line_height = draw.textbbox((0, 0), lines[0], font=font)[3] - draw.textbbox((0, 0), lines[0], font=font)[1]
    box_height = int((line_height * 1.8 * len(lines)) + 2 * padding_y)
    box_top = (panel_height - 40) - box_height

    draw.rounded_rectangle([horizontal_margin, box_top, horizontal_margin + box_width, panel_height - 40], radius=30, fill=(255, 252, 248))

    current_y = box_top + padding_y
    for line in lines:
        line_w = draw.textbbox((0, 0), line, font=font)[2] - draw.textbbox((0, 0), line, font=font)[0]
        draw.text((horizontal_margin + box_width - padding_x - line_w, current_y), line, font=font, fill=(50, 35, 25))
        current_y += line_height * 1.8
