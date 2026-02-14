from image_utils import _prepare_arabic_text, _get_arabic_font
from PIL import Image, ImageDraw

def test_arabic_render():
    text = "الصدق والشجاعة"
    reshaped = _prepare_arabic_text(text)
    
    img = Image.new('RGB', (500, 200), color='white')
    draw = ImageDraw.Draw(img)
    font = _get_arabic_font(50)
    
    # Draw with stroke (as in the app)
    draw.text((50, 50), reshaped, font=font, fill='black', stroke_width=0)
    draw.text((50, 120), reshaped, font=font, fill='yellow', stroke_width=5, stroke_fill='black')
    
    img.save('test_arabic.png')
    print(f"Original: {text}")
    print(f"Reshaped: {reshaped}")
    print("Saved test_arabic.png")

if __name__ == "__main__":
    test_arabic_render()
