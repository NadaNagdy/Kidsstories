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
        # Download image
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content)).convert("RGB")
        draw = ImageDraw.Draw(img)
        
        # Prepare Arabic text
        reshaped_text = arabic_reshaper.reshape(text)
        bidi_text = get_display(reshaped_text)
        
        # Load font (Need a .ttf file that supports Arabic)
        # For now, we'll try to find a system font or use a placeholder
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" # Example path
        if not os.path.exists(font_path):
            font_path = "/Library/Fonts/Arial.ttf" # Mac path
            
        try:
            font = ImageFont.truetype(font_path, 40)
        except:
            font = ImageFont.load_default()
            
        # Draw semi-transparent background for text readability
        width, height = img.size
        margin = 50
        text_bbox = draw.textbbox((0, 0), bidi_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Place text at the bottom
        rect_x0 = margin
        rect_y0 = height - text_height - margin - 20
        rect_x1 = width - margin
        rect_y1 = height - margin
        
        draw.rectangle([rect_x0, rect_y0, rect_x1, rect_y1], fill=(0, 0, 0, 128))
        draw.text((width//2 - text_width//2, rect_y0 + 10), bidi_text, font=font, fill=(255, 255, 255))
        
        img.save(output_path)
        return output_path
    except Exception as e:
        print(f"Error overlaying text: {e}")
        return None
