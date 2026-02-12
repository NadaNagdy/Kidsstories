from PIL import Image, ImageDraw, ImageFont
import os
import requests
from io import BytesIO
import arabic_reshaper
from bidi.algorithm import get_display


# ---------------------------------------------------------------------------
# Arabic typography helpers
# ---------------------------------------------------------------------------

def _prepare_arabic_text(text: str) -> str:
    """
    Reshape + apply bidi so Pillow renders Arabic text correctly.
    """
    if not text:
        return ""
    reshaped = arabic_reshaper.reshape(text)
    return get_display(reshaped)


def _wrap_arabic_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int):
    """
    Simple word-based wrapper that measures visual (reshaped+bidi) width
    and returns a list of *visual-order* lines ready for drawing.
    """
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
            # finalize current line
            lines.append(current)
            current = word

    if current:
        lines.append(current)

    # Convert all logical lines to visual form for drawing
    return [_prepare_arabic_text(line) for line in lines]


def _get_arabic_font(size: int, weight: str = "regular") -> ImageFont.FreeTypeFont:
    """
    Load Amiri (preferred) with optional bold weight, fall back gracefully.
    """
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
            except Exception:
                continue

    # Fallback – keeps code robust even if fonts are missing
    return ImageFont.load_default()


def _draw_story_text_box(
    draw: ImageDraw.ImageDraw,
    panel_width: int,
    panel_height: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    *,
    bottom_margin: int = 20,
    horizontal_margin: int = 40,
    padding_x: int = 24,
    padding_y: int = 18,
    radius: int = 16,
    bg_color=(255, 248, 240),  # Creamy, matches #FFF8F0
    text_color=(44, 24, 16),   # Dark brown #2C1810
    line_spacing: float = 1.4,
):
    """
    Draws the bottom 20–25% Arabic text box as per the style guide:
    - Semi-opaque cream background (simulated on white)
    - Rounded corners
    - Multi-line RTL text, visually centered horizontally
    """
    if not text:
        return

    # Max width for the whole box and for text inside
    box_width = panel_width - 2 * horizontal_margin
    max_text_width = box_width - 2 * padding_x

    # Wrap into multiple visual lines
    lines = _wrap_arabic_text(draw, text, font, max_text_width)
    if not lines:
        return

    # Approx line height
    sample_bbox = draw.textbbox((0, 0), lines[0], font=font)
    line_height = sample_bbox[3] - sample_bbox[1]

    total_text_height = 0
    for i, line in enumerate(lines):
        if i == 0:
            total_text_height += line_height
        else:
            total_text_height += int(line_height * line_spacing)

    box_height = total_text_height + 2 * padding_y

    # Position box at bottom with margin
    box_left = (panel_width - box_width) // 2
    box_right = box_left + box_width
    box_bottom = panel_height - bottom_margin
    box_top = box_bottom - box_height

    # Draw rounded rectangle background
    draw.rounded_rectangle(
        [box_left, box_top, box_right, box_bottom],
        radius=radius,
        fill=bg_color,
    )

    # Draw text, RTL: align each line to the right inside the box
    current_y = box_top + padding_y
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        line_width = bbox[2] - bbox[0]
        # Right edge minus padding → starting x for this line
        x_right = box_right - padding_x
        x = x_right - line_width

        draw.text((x, current_y), line, font=font, fill=text_color)

        if i < len(lines) - 1:
            current_y += int(line_height * line_spacing)

def overlay_text_on_image(image_url, text, output_path):
    """
    Downloads an image, places it on a square panel, and adds a styled
    Arabic text box in the bottom 20–25% following the Arabic text
    layout guide.
    """
    try:
        # 1. Background & Dimensions (square panel)
        width, height = 1024, 1024
        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        # 2. Download & Paste Illustration (top ~75%)
        if image_url.startswith("data:"):
            import base64

            header, encoded = image_url.split(",", 1)
            image_data = base64.b64decode(encoded)
            art = Image.open(BytesIO(image_data)).convert("RGB")
        else:
            response = requests.get(image_url, timeout=15)
            if response.status_code != 200:
                print(f"Error: Failed to download image from {image_url}")
                return None
            art = Image.open(BytesIO(response.content)).convert("RGB")

        # Keep aspect ratio, but constrain to leave generous room for text
        max_art_width = int(width * 0.9)
        max_art_height = int(height * 0.7)
        art.thumbnail((max_art_width, max_art_height), Image.LANCZOS)

        art_x = (width - art.width) // 2
        art_y = 60  # small top margin
        img.paste(art, (art_x, art_y))

        # 3. Add Thick Border (classic framed panel)
        border_w = 25
        draw.rectangle(
            [border_w // 2, border_w // 2, width - border_w // 2, height - border_w // 2],
            outline=(150, 150, 150),
            width=border_w,
        )

        # 4. Add Arabic Text Box at Bottom
        font = _get_arabic_font(40, weight="regular")
        _draw_story_text_box(
            draw,
            width,
            height,
            text=text,
            font=font,
            bottom_margin=30,
            horizontal_margin=40,
            padding_x=26,
            padding_y=20,
        )

        img.save(output_path)
        return output_path
    except Exception as e:
        print(f"Error creating story page: {e}")
        return None

def create_cover_page(image_url, top_text, bottom_text, output_path, child_photo_base64=None):
    """
    Creates a professional cover page with:
    1. Title at top ("بطل الشجاعة")
    2. Circular illustration of the child in the center.
    3. Child's name at the bottom.
    """
    try:
        width, height = 1024, 1024
        # Create clean white background
        img = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Load fonts (Arabic classic style)
        title_font = _get_arabic_font(80, weight="bold")
        name_font = _get_arabic_font(65, weight="regular")
        
        # 1. Top Title (expects format "بطل الشجاعة")
        #    Styled as bold dark-brown Arabic title with subtle white stroke.
        reshaped_top = _prepare_arabic_text(top_text)
        t_bbox = draw.textbbox((0, 0), reshaped_top, font=title_font)
        tw = t_bbox[2] - t_bbox[0]
        title_x = (width - tw) // 2
        title_y = 80
        draw.text(
            (title_x, title_y),
            reshaped_top,
            font=title_font,
            fill=(44, 24, 16),  # Dark brown
            stroke_width=2,
            stroke_fill=(255, 255, 255),  # subtle white outline
        )
        
        # 2. Central Circular Art
        # If we have the AI generated image, use it. If not, fallback to photo.
        response = requests.get(image_url, timeout=15)
        if response.status_code == 200:
            art = Image.open(BytesIO(response.content)).convert("RGBA")
        else:
            return None
            
        # Circular crop logic
        size = (620, 620) # Slightly smaller to ensure fit
        art = art.resize(size, Image.LANCZOS)
        mask = Image.new('L', size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0) + size, fill=255)
        
        circular_art = Image.new('RGBA', size, (0, 0, 0, 0))
        circular_art.paste(art, (0, 0), mask=mask)
        
        # Add a soft colored pencil border around the circle
        circle_y = 200
        draw.ellipse([(width-size[0])//2 - 5, circle_y - 5, (width+size[0])//2 + 5, circle_y + size[1] + 5], outline=(200, 200, 230), width=10)
        
        img.paste(circular_art, ((width - size[0])//2, circle_y), circular_art)
        
        # 3. Add Outer Border (Consistency with story pages)
        border_w = 25
        draw.rectangle([border_w//2, border_w//2, width-border_w//2, height-border_w//2], outline=(150, 150, 150), width=border_w)
        
        # 4. Bottom Name
        reshaped_bottom = _prepare_arabic_text(bottom_text)
        n_bbox = draw.textbbox((0, 0), reshaped_bottom, font=name_font)
        nw = n_bbox[2] - n_bbox[0]
        draw.text(((width - nw)//2, 880), reshaped_bottom, font=name_font, fill=(44, 24, 16))
        
        img.save(output_path)
        return output_path
    except Exception as e:
        print(f"Error creating refined cover: {e}")
        return None

def create_grid_cover_panel(photo_base64, child_name, value, output_path):
    """
    Creates the first panel of the grid (Cover).
    Includes title, circular photo of the child, and their name.
    """
    try:
        width, height = 1024, 1024
        # Background - clean white
        img = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Load fonts
        title_font = _get_arabic_font(80, weight="bold")
        name_font = _get_arabic_font(60, weight="regular")
        
        # 1. Title: "بطل [Value]" – styled top title for cover panel
        title_text = f"بطل {value}"
        reshaped_title = _prepare_arabic_text(title_text)
        t_bbox = draw.textbbox((0, 0), reshaped_title, font=title_font)
        tw = t_bbox[2] - t_bbox[0]
        # Position slightly toward top, visually balanced
        title_x = (width - tw) // 2
        title_y = 70
        draw.text(
            (title_x, title_y),
            reshaped_title,
            font=title_font,
            fill=(44, 24, 16),
            stroke_width=2,
            stroke_fill=(255, 255, 255),
        )
        
        # 2. Circular Photo
        # Decode photo
        import base64
        photo_data = base64.b64decode(photo_base64)
        photo = Image.open(BytesIO(photo_data)).convert("RGBA")
        
        # Resize and Crop to Circle
        size = (500, 500)
        photo = photo.resize(size, Image.LANCZOS)
        mask = Image.new('L', size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0) + size, fill=255)
        
        photo_circular = Image.new('RGBA', size, (0, 0, 0, 0))
        photo_circular.paste(photo, (0, 0), mask=mask)
        
        # Paste photo in middle
        img.paste(photo_circular, ((width - size[0])//2, 250), photo_circular)
        
        # 3. Name: "[Child's Name]"
        reshaped_name = _prepare_arabic_text(child_name)
        n_bbox = draw.textbbox((0, 0), reshaped_name, font=name_font)
        nw = n_bbox[2] - n_bbox[0]
        draw.text(((width - nw)//2, 780), reshaped_name, font=name_font, fill=(44, 24, 16))
        
        # Add a simple hand-drawn style frame (thick border)
        border_w = 40
        draw.rectangle([border_w//2, border_w//2, width-border_w//2, height-border_w//2], outline=(100, 100, 100), width=border_w)
        
        img.save(output_path)
        return output_path
    except Exception as e:
        print(f"Error creating grid cover: {e}")
        return None

def create_story_panel(image_url, text, output_path):
    """
    Creates a story panel with a frame and text below the illustration.
    """
    try:
        # download image
        response = requests.get(image_url, timeout=15)
        if response.status_code != 200: return None
        art = Image.open(BytesIO(response.content)).convert("RGB")
        
        width, height = 1024, 1024
        img = Image.new("RGB", (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)

        # Paste art scaled down to leave a dedicated bottom text band (~25%)
        max_art_width = int(width * 0.9)
        max_art_height = int(height * 0.7)
        art.thumbnail((max_art_width, max_art_height), Image.LANCZOS)
        art_x = (width - art.width) // 2
        art_y = 60
        img.paste(art, (art_x, art_y))

        # Text box at bottom following the Arabic layout guide
        font = _get_arabic_font(40, weight="regular")
        _draw_story_text_box(
            draw,
            width,
            height,
            text=text,
            font=font,
            bottom_margin=30,
            horizontal_margin=40,
            padding_x=26,
            padding_y=20,
        )

        # Hand-drawn frame effect (thick border)
        border_w = 20
        draw.rectangle(
            [border_w // 2, border_w // 2, width - border_w // 2, height - border_w // 2],
            outline=(120, 120, 120),
            width=border_w,
        )

        img.save(output_path)
        return output_path
    except Exception as e:
        print(f"Error creating story panel: {e}")
        return None
