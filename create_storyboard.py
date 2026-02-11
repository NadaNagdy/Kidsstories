import os
import requests
import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from openai_service import generate_storybook_page, create_character_reference
from image_utils import overlay_text_on_image

def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# Style Configuration
STYLE_DESC = "Classic, soft watercolor and colored pencil illustration style, friendly hand-drawn feel, gentle pastel colors, clean white background, soft outlines"

def create_storyboard(child_name="بطلنا", value="الشجاعة", photo_path=None):
    os.makedirs("storyboard_output", exist_ok=True)
    
    # 1. Character Reference
    if photo_path and os.path.exists(photo_path):
        print(f"Creating character reference from {photo_path}...")
        base64_photo = get_base64_image(photo_path)
        character_desc = create_character_reference(base64_photo, is_url=False)
    else:
        print("Using default character description...")
        character_desc = "a toddler with dark hair, a small cute face, wearing a simple white tank top"
        base64_photo = None

    # Specialized Panel 1: Cover
    from image_utils import create_grid_cover_panel, create_story_panel
    
    generated_paths = []
    
    # Panel 1: Cover
    print("Generating Panel 1 (Cover)...")
    cover_path = "storyboard_output/panel_1.png"
    if base64_photo:
        create_grid_cover_panel(base64_photo, child_name, value, cover_path)
        generated_paths.append(cover_path)
    else:
        # fallback placeholder
        print("No photo provided for cover panel!")
        generated_paths.append(None)

    # Panels 2-6: Story Scenes
    # We'll use some generic story content for testing/default
    scenes = [
        {"prompt": "The child is looking at a tall slide.", "text": "السلم عالي.. وبطلنا خايف؟"},
        {"prompt": "The child climbs the first step.", "text": "تاتا تاتا.. بطلنا بدأ يطلع!"},
        {"prompt": "The child is halfway up, smiling.", "text": "أنا أقدر.. أنا شجاع أوي!"},
        {"prompt": "The child is at the top, proud.", "text": "هييييه! أنا فوق!"},
        {"prompt": "The child slides down with joy.", "text": "وووووي! برافو يا بطل!"}
    ]

    for i, scene in enumerate(scenes, 2):
        print(f"Generating Panel {i}...")
        img_url = generate_storybook_page(character_desc, scene['prompt'])
        if img_url:
            p_path = f"storyboard_output/panel_{i}.png"
            create_story_panel(img_url, scene['text'], p_path)
            generated_paths.append(p_path)
        else:
            generated_paths.append(None)

    # Grid Assembly: 3 rows x 2 columns
    if any(generated_paths):
        print("Assembling 3-row x 2-column storyboard grid...")
        pw, ph = 1024, 1024
        grid = Image.new('RGB', (pw * 2, ph * 3), (255, 255, 255))
        
        for i, path in enumerate(generated_paths):
            if path and os.path.exists(path):
                img = Image.open(path)
                col = i % 2
                row = i // 2
                grid.paste(img, (col * pw, row * ph))
        
        final_path = f"storyboard_output/storyboard_{child_name}.png"
        grid.save(final_path)
        print(f"Storyboard saved to {final_path}")
        return final_path
    return None

if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "لانا"
    photo = sys.argv[2] if len(sys.argv) > 2 else None
    create_storyboard(name, photo)
