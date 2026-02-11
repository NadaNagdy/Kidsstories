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
STYLE_DESC = "Classic children's book illustration, soft watercolor and colored pencil textures, hand-drawn look, gentle pastel color palette, clean white background, expressive faces, soft pencil outlines"

def create_storyboard(child_name="بطلنا", photo_path=None):
    os.makedirs("storyboard_output", exist_ok=True)
    
    # Character Reference
    if photo_path and os.path.exists(photo_path):
        print(f"Creating character reference from {photo_path}...")
        base64_image = get_base64_image(photo_path)
        character_desc = create_character_reference(base64_image, is_url=False)
    else:
        print("Using default character description...")
        character_desc = "a toddler with dark hair, a small cute face, wearing a simple white tank top"

    # Storyboard Content with dynamic name
    panels_data = [
        {
            "id": 1,
            "prompt": f"The toddler stands bravely and proudly next to a friendly, large, fluffy lion lying down calmly on a white background. Title text 'Batal Al Shajaa' (بطل الشجاعة) is subtly integrated. Top left panel.",
            "text": "بطل الشجاعة"
        },
        {
            "id": 2,
            "prompt": "A big, fluffy-maned lion sleeping peacefully under a large tree in a green forest clearing. Top middle panel.",
            "text": "كان يا ما كان.. في الغابة أسد كبير نائم.. ششش"
        },
        {
            "id": 3,
            "prompt": f"The lion is sitting up, looking sad and crying, holding one paw up. The toddler {child_name} approaches with a concerned and empathetic look. Top right panel.",
            "text": f"اقتربت {child_name}.. الأسد يبكي: 'آي يا قدمي!' شوكة كبيرة تؤلمه."
        },
        {
            "id": 4,
            "prompt": f"The toddler {child_name} stands very close to the lion, holding its big paw gently with both hands, looking into its eyes with a brave and comforting smile. Bottom left panel.",
            "text": f"{child_name} قالت بشجاعة: 'لا تخف يا أسد، سأساعدك!'"
        },
        {
            "id": 5,
            "prompt": f"The toddler {child_name} is pulling a sharp thorn out of the lion's paw with determination. A small visual text effect bubbles 'POP' nearby. Bottom middle panel.",
            "text": f"سحبت {child_name} الشوكة بقوة.. 'بوب!' زال الألم!"
        },
        {
            "id": 6,
            "prompt": f"The toddler {child_name} is sitting happily on the lion's back as the lion walks through a beautiful garden. Bottom right panel.",
            "text": f"الأسد فرح وقال: 'شكراً يا {child_name} الشجاعة!' وأصبحا صديقين."
        }
    ]

    panel_images = []

    print(f"Generating panels for {child_name}...")
    for panel in panels_data:
        print(f"Generating Panel {panel['id']}...")
        # Add style and character to the prompt
        img_url = generate_storybook_page(character_desc, panel['prompt'])
        
        if img_url:
            output_path = f"storyboard_output/panel_{panel['id']}.png"
            # Overlay text
            final_panel_path = overlay_text_on_image(img_url, panel['text'], output_path)
            if final_panel_path:
                panel_images.append(Image.open(final_panel_path))
            else:
                print(f"Failed to overlay text on panel {panel['id']}")
        else:
            print(f"Failed to generate panel {panel['id']}")

    if len(panel_images) == 6:
        print("Assembling storyboard grid...")
        width, height = 1024, 1024
        grid = Image.new('RGB', (width * 3, height * 2), (255, 255, 255))
        
        for i, img in enumerate(panel_images):
            col = i % 3
            row = i // 3
            grid.paste(img, (col * width, row * height))
        
        final_path = f"storyboard_output/storyboard_{child_name}.png"
        grid.save(final_path)
        print(f"Storyboard saved to {final_path}")
        return final_path
    else:
        print(f"Only generated {len(panel_images)} panels. Grid assembly skipped.")
        return None

if __name__ == "__main__":
    import sys
    name = sys.argv[1] if len(sys.argv) > 1 else "لانا"
    photo = sys.argv[2] if len(sys.argv) > 2 else None
    create_storyboard(name, photo)
