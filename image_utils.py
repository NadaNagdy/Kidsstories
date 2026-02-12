from PIL import Image, ImageDraw, ImageFont
import os
import requests
from io import BytesIO
import arabic_reshaper
from bidi.algorithm import get_display

def overlay_text_on_image(image_url, text, output_path):
    """
    Downloads an image, overlays Arabic text, and saves it.
    """
    try:
        print(f"DEBUG: Overlaying text: {text[:20]}...")
        # Download image or decode base64
        if image_url.startswith('data:'):
            import base64
            # Extract base64 part
            header, encoded = image_url.split(",", 1)
            image_data = base64.b64decode(encoded)
            img = Image.open(BytesIO(image_data)).convert("RGBA")
        else:
            response = requests.get(image_url, timeout=15)
            if response.status_code != 200:
                print(f"Error: Failed to download image from {image_url}. Status: {response.status_code}")
                return None
            img = Image.open(BytesIO(response.content)).convert("RGBA")
        overlay = Image.new('RGBA', img.size, (0,0,0,0))
        draw = ImageDraw.Draw(overlay)
        
        # Prepare Arabic text - Reshaping line by line for better multiline support
        lines = text.split('\n')
        processed_lines = []
        for line in lines:
            reshaped_line = arabic_reshaper.reshape(line)
            bidi_line = get_display(reshaped_line)
            processed_lines.append(bidi_line)
        
        bidi_text = '\n'.join(processed_lines)
        
        # Load font (Bundled version for consistency across platforms)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        font_paths = [
            os.path.join(base_dir, "fonts", "Amiri-Regular.ttf"),
            "/System/Library/Fonts/GeezaPro.ttc",
            "/System/Library/Fonts/SFArabic.ttf"
        ]
        
        font = None
        for path in font_paths:
            if os.path.exists(path):
                try:
                    font = ImageFont.truetype(path, 50) # Increased from 35 for mobile readability
                    print(f"DEBUG: Loaded font: {path}")
                    break
                except Exception as e:
                    print(f"Error loading font {path}: {e}")
                    continue
        
        if not font:
            print("Warning: Falling back to default font (Arabic will likely not render)")
            font = ImageFont.load_default()
            
        # Draw semi-transparent background for text readability
        width, height = img.size
        margin = 40
        
        # multiline_textbbox handles multiple lines correctly
        text_bbox = draw.multiline_textbbox((0, 0), bidi_text, font=font, align="center")
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Place text at the bottom with some padding
        padding = 15
        rect_x0 = margin
        rect_y0 = height - text_height - margin - (padding * 2)
        rect_x1 = width - margin
        rect_y1 = height - margin
        
        # Draw the rectangle on the overlay
        draw.rectangle([rect_x0, rect_y0, rect_x1, rect_y1], fill=(255, 255, 255, 200))
        
        # Draw the multiline text
        text_x = width // 2 - text_width // 2
        text_y = rect_y0 + padding
        draw.multiline_text((text_x, text_y), bidi_text, font=font, fill=(0, 0, 0), align="center")
        
        # Composite and save
        out = Image.alpha_composite(img, overlay).convert("RGB")
        out.save(output_path)
        print(f"DEBUG: Saved image with text to {output_path}")
        return output_path
    except Exception as e:
        print(f"Error overlaying text: {e}")
        import traceback
        traceback.print_exc()
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
        
        # Load fonts
        base_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(base_dir, "fonts", "Amiri-Regular.ttf")
        title_font = ImageFont.truetype(font_path, 80) if os.path.exists(font_path) else ImageFont.load_default()
        name_font = ImageFont.truetype(font_path, 65) if os.path.exists(font_path) else ImageFont.load_default()
        
        # 1. Top Title (expects format "بطل الـ[Value]")
        reshaped_top = get_display(arabic_reshaper.reshape(top_text))
        t_bbox = draw.textbbox((0, 0), reshaped_top, font=title_font)
        tw = t_bbox[2] - t_bbox[0]
        draw.text(((width - tw)//2, 100), reshaped_top, font=title_font, fill=(50, 50, 150)) # Colorful Blue
        
        # 2. Central Circular Art
        # If we have the AI generated image, use it. If not, fallback to photo.
        response = requests.get(image_url, timeout=15)
        if response.status_code == 200:
            art = Image.open(BytesIO(response.content)).convert("RGBA")
        else:
            return None
            
        # Circular crop logic
        size = (650, 650)
        art = art.resize(size, Image.LANCZOS)
        mask = Image.new('L', size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0) + size, fill=255)
        
        circular_art = Image.new('RGBA', size, (0, 0, 0, 0))
        circular_art.paste(art, (0, 0), mask=mask)
        
        # Add a soft colored pencil border around the circle
        draw.ellipse([(width-size[0])//2 - 5, 250 - 5, (width+size[0])//2 + 5, 250 + size[1] + 5], outline=(200, 200, 230), width=10)
        
        img.paste(circular_art, ((width - size[0])//2, 250), circular_art)
        
        # 3. Bottom Name
        reshaped_bottom = get_display(arabic_reshaper.reshape(bottom_text))
        n_bbox = draw.textbbox((0, 0), reshaped_bottom, font=name_font)
        nw = n_bbox[2] - n_bbox[0]
        draw.text(((width - nw)//2, 850), reshaped_bottom, font=name_font, fill=(0, 0, 0))
        
        # Decoration: Add some simple stars/hearts effect (optional but nice)
        # For brevity, we'll keep it clean as requested.
        
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
        
        # Load font
        base_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(base_dir, "fonts", "Amiri-Regular.ttf")
        title_font = ImageFont.truetype(font_path, 80) if os.path.exists(font_path) else ImageFont.load_default()
        name_font = ImageFont.truetype(font_path, 60) if os.path.exists(font_path) else ImageFont.load_default()
        
        # 1. Title: "بطل الـ[Value]"
        title_text = f"بطل {value}"
        reshaped_title = get_display(arabic_reshaper.reshape(title_text))
        t_bbox = draw.textbbox((0, 0), reshaped_title, font=title_font)
        tw = t_bbox[2] - t_bbox[0]
        draw.text(((width - tw)//2, 80), reshaped_title, font=title_font, fill=(50, 50, 150)) # Colorful title
        
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
        reshaped_name = get_display(arabic_reshaper.reshape(child_name))
        n_bbox = draw.textbbox((0, 0), reshaped_name, font=name_font)
        nw = n_bbox[2] - n_bbox[0]
        draw.text(((width - nw)//2, 780), reshaped_name, font=name_font, fill=(0, 0, 0))
        
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
        img = Image.new('RGB', (width, height), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Paste art scaled down slightly to leave room for text/frame
        art_size = 800
        art = art.resize((art_size, art_size), Image.LANCZOS)
        img.paste(art, ((width - art_size)//2, 80))
        
        # Text at bottom
        base_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(base_dir, "fonts", "Amiri-Regular.ttf")
        font = ImageFont.truetype(font_path, 40) if os.path.exists(font_path) else ImageFont.load_default()
        
        reshaped_text = get_display(arabic_reshaper.reshape(text))
        t_bbox = draw.textbbox((0, 0), reshaped_text, font=font)
        tw = t_bbox[2] - t_bbox[0]
        draw.text(((width - tw)//2, 900), reshaped_text, font=font, fill=(0, 0, 0))
        
        # Hand-drawn frame effect (thick border)
        border_w = 20
        draw.rectangle([border_w//2, border_w//2, width-border_w//2, height-border_w//2], outline=(120, 120, 120), width=border_w)
        
        img.save(output_path)
        return output_path
    except Exception as e:
        print(f"Error creating story panel: {e}")
        return None
