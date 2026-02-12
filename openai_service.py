import os
import base64
import requests
import re
from openai import OpenAI

# 1. API Setup
api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY") or "not_set"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

# 2. Refined Global Style
# JUSTIFICATION: We added explicit "Negative Prompts" here to stop the AI from 
# drawing its own text boxes (like the "Adventures of" box you saw).
GLOBAL_STORYBOOK_STYLE = """
You are a professional children's book illustrator.
STYLE: Soft watercolor and colored pencil, classic aesthetic, warm pastel tones, clean white background.
CHARACTER CONSISTENCY: The hero child must stay identical on all pages.
- Same face, skin tone, and curly hair.
- CRITICAL: The child MUST always wear the same outfit (e.g., striped sweatshirt).

LAYOUT RULES:
- Absolutely NO text, letters, words, or banners inside the image.
- DO NOT draw any frames or boxes around the character.
- Leave the TOP 15% and BOTTOM 15% of the image as PURE WHITE SPACE to allow for external text overlay.
- Centralize the character in the middle of the square canvas.
""".strip()

def create_character_reference(image_data, is_url=True):
    """Analyzes child's photo to extract visual identity."""
    try:
        image_content = {"url": image_data} if is_url else {"url": f"data:image/jpeg;base64,{image_data}"}
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-lite-001",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this child's photo. Focus on: face shape, curly hair texture, and eye shape. State they are wearing a striped sweatshirt."},
                        {"type": "image_url", "image_url": image_content}
                    ],
                }
            ],
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error creating character reference: {e}")
        return "A cute child with curly hair wearing a striped sweatshirt, watercolor style."

def verify_payment_screenshot(image_data, target_handle):
    """Verifies payment transfer."""
    try:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://kidsstories.railway.app"
        }
        prompt = f"Does this payment screenshot show a successful transfer to '{target_handle}'? Reply with ONLY 'YES' or 'NO'."
        
        payload = {
            "model": "google/gemini-2.0-flash-001",
            "messages": [
                {
                    "role": "user", 
                    "content": [
                        {"type": "text", "text": prompt}, 
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}}
                    ]
                }
            ]
        }
        
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=20)
        answer = response.json()["choices"][0]["message"]["content"].strip().upper()
        return "YES" in answer
    except Exception as e:
        print(f"Error in verification: {e}")
        return False

def generate_storybook_page(character_description, page_prompt, child_name=None, is_cover=False, is_final=False):
    """Generates a storybook page without AI-generated text."""
    try:
        page_type = "COVER ART" if is_cover else ("FINAL REWARD ART" if is_final else "STORY ART")
        
        # JUSTIFICATION: For the cover, we explicitly command the AI to focus 
        # only on the character and the background elements, forbidding text boxes.
        cover_extra = "This is a cover: Center the child, surrounded by magical storybook elements. NO BANNERS. NO TEXT." if is_cover else ""

        user_content = f"""
        TASK: {page_type}
        CHARACTER: {character_description}
        SCENE: {page_prompt}
        {cover_extra}
        REMINDER: No text in image. Keep top and bottom margins clear and white.
        """.strip()

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://kidsstories.railway.app",
            "X-Title": "Kids Story Bot"
        }

        payload = {
            "model": "google/gemini-2.5-flash-image",
            "messages": [
                {"role": "system", "content": GLOBAL_STORYBOOK_STYLE},
                {"role": "user", "content": user_content}
            ],
            "modalities": ["image"]
        }
        
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        
        # Extract logic (Base64/URL)
        try:
            choices = data.get('choices', [])
            if choices:
                images = choices[0].get('message', {}).get('images', [])
                if images:
                    img_url = images[0].get('image_url', {}).get('url', '')
                    if img_url: return img_url
        except: pass

        full_response_text = str(data)
        if "data:image" in full_response_text:
            match = re.search(r'data:image/[^;]+;base64,[^"\'\s]+', full_response_text)
            if match: return match.group(0)

        url_match = re.search(r'https://[^\s"\'<>]+(?:\.png|\.jpg|\.jpeg|\b)', full_response_text)
        if url_match: return url_match.group(0).rstrip(').')
        
        return None
    except Exception as e:
        print(f"Error generating page: {e}")
        return None
