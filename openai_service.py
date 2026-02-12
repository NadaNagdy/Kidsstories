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

# 2. Global Style
GLOBAL_STORYBOOK_STYLE = """
You are an image generation model specialized in classic children's storybooks.
STYLE: Soft watercolor and colored pencil illustration, classic aesthetic, warm pastel colors, clean white background.
CHARACTER CONSISTENCY: The hero child must stay identical on ALL pages.
- Same face, skin tone, and hair.
- CRITICAL: The child MUST always wear a striped sweatshirt.
- Layout: Square (1:1). Top 75% artwork, bottom 25% kept empty/clean for text overlay.
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
                        {"type": "text", "text": "Analyze this child's photo and provide a CONCISE description (MAX 100 words). Focus on: face shape, hair texture/color, and eye shape. IMPORTANT: Always state they are wearing a striped sweatshirt for the story."},
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

# --- THIS IS THE MISSING FUNCTION ---
def verify_payment_screenshot(image_data, target_handle):
    """Verifies InstaPay or wallet number in the screenshot."""
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
    """Generates a storybook page, handling both URLs and Base64 data."""
    try:
        page_type = "COVER PAGE" if is_cover else ("FINAL REWARD PAGE" if is_final else "STORY PAGE")
        
        user_content = f"""
        TASK: {page_type}
        CHARACTER DESCRIPTION: {character_description}
        SCENE DESCRIPTION: {page_prompt}
        {f'CHILD NAME: {child_name}' if child_name else ''}
        REMINDER: Child MUST wear the striped sweatshirt. Leave bottom 25% empty.
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
        
        # Check structured 'images' field first (Base64 or URL)
        try:
            choices = data.get('choices', [])
            if choices:
                images = choices[0].get('message', {}).get('images', [])
                if images:
                    img_url = images[0].get('image_url', {}).get('url', '')
                    if img_url: return img_url
        except: pass

        # Fallback to Regex search
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
