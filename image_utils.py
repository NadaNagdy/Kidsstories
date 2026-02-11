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
                    font = ImageFont.truetype(path, 35) # Slightly smaller for multiline
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

def create_cover_page(image_url, top_text, bottom_text, output_path):
    """
    Creates a cover page with text at the top and bottom.
    """
    try:
        # Download image or decode base64 (reuse download logic)
        img_temp_path = output_path + ".base.png"
        img_path = overlay_text_on_image(image_url, "", img_temp_path) # Get pure image
        
        if not img_path: return None
        
        img = Image.open(img_path).convert("RGBA")
        overlay = Image.new('RGBA', img.size, (0,0,0,0))
        draw = ImageDraw.Draw(overlay)
        
        # Load font
        base_dir = os.path.dirname(os.path.abspath(__file__))
        font_path = os.path.join(base_dir, "fonts", "Amiri-Regular.ttf")
        font = ImageFont.truetype(font_path, 50) if os.path.exists(font_path) else ImageFont.load_default()
        
        width, height = img.size
        padding = 20
        margin = 40
        
        # Prepare Top Text (Child's Name)
        reshaped_top = get_display(arabic_reshaper.reshape(top_text))
        top_bbox = draw.textbbox((0, 0), reshaped_top, font=font)
        top_w = top_bbox[2] - top_bbox[0]
        top_h = top_bbox[3] - top_bbox[1]
        
        # Draw Top Background + Text
        draw.rectangle([margin, margin, width-margin, margin+top_h+(padding*2)], fill=(255, 255, 255, 220))
        draw.text(((width - top_w)//2, margin+padding), reshaped_top, font=font, fill=(0,0,0))
        
        # Prepare Bottom Text ("Hero in [Value]")
        reshaped_bottom = get_display(arabic_reshaper.reshape(bottom_text))
        bot_bbox = draw.textbbox((0, 0), reshaped_bottom, font=font)
        bot_w = bot_bbox[2] - bot_bbox[0]
        bot_h = bot_bbox[3] - bot_bbox[1]
        
        # Draw Bottom Background + Text
        draw.rectangle([margin, height-margin-bot_h-(padding*2), width-margin, height-margin], fill=(255, 255, 255, 220))
        draw.text(((width - bot_w)//2, height-margin-bot_h-padding), reshaped_bottom, font=font, fill=(0,0,0))
        
        # Composite and save
        out = Image.alpha_composite(img, overlay).convert("RGB")
        out.save(output_path)
        if os.path.exists(img_temp_path): os.remove(img_temp_path)
        return output_path
    except Exception as e:
        print(f"Error creating cover: {e}")
        return None
