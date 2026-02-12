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
GLOBAL_STORYBOOK_STYLE = """
You are a professional children's book illustrator.
STYLE: Soft watercolor and colored pencil, classic aesthetic, warm pastel tones, clean white background.
CHARACTER CONSISTENCY: The hero child must stay identical on all pages.
- Respect the gender of the child provided in the prompt.
- Same face, skin tone, and hair texture.
- CRITICAL: The child MUST always wear the same outfit (e.g., striped sweatshirt).

LAYOUT RULES:
- Absolutely NO text, letters, words, or banners inside the image.
- DO NOT draw any frames or boxes around the character.
- Leave the TOP 15% and BOTTOM 15% of the image as PURE WHITE SPACE.
""".strip()

def create_character_reference(image_data, gender="boy", is_url=True):
    """Analyzes child's photo while knowing the gender for better accuracy."""
    try:
        image_content = {"url": image_data} if is_url else {"url": f"data:image/jpeg;base64,{image_data}"}
        
        # JUSTIFICATION: Telling the vision model the gender helps it identify 
        # specific features (like hair length or facial softness) more effectively.
        gender_context = "a little girl" if gender == "girl" else "a little boy"
        
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-lite-001",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"Analyze this photo of {gender_context}. Focus on: face shape, hair texture, and eye shape. State they are wearing a striped sweatshirt."},
                        {"type": "image_url", "image_url": image_content}
                    ],
                }
            ],
            max_tokens=150
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error creating character reference: {e}")
        return f"A cute {gender} with curly hair wearing a striped sweatshirt, watercolor style."

def generate_storybook_page(character_description, page_prompt, gender="boy", is_cover=False):
    """Generates a page with specific gender descriptors for the image model."""
    try:
        page_type = "COVER ART" if is_cover else "STORY ART"
        
        # JUSTIFICATION: Image models respond better to explicit gender subjects 
        # (e.g., 'a beautiful girl') to avoid generic or boyish defaults.
        gender_subject = "a beautiful little girl" if gender == "girl" else "a brave little boy"
        
        user_content = f"""
        TASK: {page_type}
        SUBJECT: {gender_subject}
        CHARACTER: {character_description}
        SCENE: {page_prompt}
        REMINDER: No text in image. Keep top and bottom margins clear.
        """.strip()

        payload = {
            "model": "google/gemini-2.5-flash-image",
            "messages": [
                {"role": "system", "content": GLOBAL_STORYBOOK_STYLE},
                {"role": "user", "content": user_content}
            ],
            "modalities": ["image"]
        }
        
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=90)
        data = response.json()
        
        # Logic to extract image (Base64 or URL)
        full_response_text = str(data)
        if "data:image" in full_response_text:
            match = re.search(r'data:image/[^;]+;base64,[^"\'\s]+', full_response_text)
            if match: return match.group(0)
        url_match = re.search(r'https://[^\s"\'<>]+(?:\.png|\.jpg|\.jpeg|\b)', full_response_text)
        return url_match.group(0).rstrip(').') if url_match else None

    except Exception as e:
        print(f"Error: {e}")
        return None
