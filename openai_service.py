import os
import base64
import requests
from openai import OpenAI

# Initialize OpenRouter client
# Note: Using OPENROUTER_API_KEY if available, else falling back to OPENAI_API_KEY
api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY") or "not_set"

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=api_key
)

# Global style / system prompt for all storybook images
GLOBAL_STORYBOOK_STYLE = """
You are an image generation model specialized in classic Arabic children's storybooks.

GLOBAL RULES:
- Style: classic children's storybook, soft watercolor + colored pencil, warm pastel colors, safe and gentle for ages 1–5.
- Format: square (1:1). Top ~75%% artwork, bottom ~25%% kept clean for Arabic text overlay (light cream panel, minimal detail).
- Character consistency: The hero is ALWAYS the same child as in the uploaded photo:
  - Keep the same face, skin tone, eye color/shape, hair color/length/style, and clothing on ALL pages (cover + story pages + final tips page).
  - You may ONLY change pose, camera angle, and background scene.
  - Do NOT change age, gender, or outfit colors unless explicitly told.
- Do NOT add narrative text in the bottom text area; leave it visually clean.
- For the cover page: leave empty space at the top for Arabic title and at the bottom for the child’s name.
- For the last page: design a reward/tips poster that still shows the same child hero.

You must produce images that look like a single coherent printed picture book.
""".strip()

def create_character_reference(image_data, is_url=True):
    """
    Analyzes the photo and creates a character description for consistency.
    image_data can be a URL or a base64 encoded string.
    """
    try:
        if is_url:
            image_content = {"url": image_data}
        else:
            image_content = {"url": f"data:image/jpeg;base64,{image_data}"}

        # Using a high-quality vision model from OpenRouter
        response = client.chat.completions.create(
            model="google/gemini-2.0-flash-lite-001", # Cheapest high-quality 2.0 vision model
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Analyze this child's photo in EXTREME DETAIL for a storybook illustration. Describe EXACTLY: 1) Face shape and structure, 2) Eye color, shape, and expression, 3) Eyebrow shape and thickness, 4) Nose shape, 5) Mouth and smile characteristics, 6) Hair color, texture, length, and exact style, 7) Skin tone (be very specific), 8) Any distinctive features (dimples, freckles, etc.). CRITICAL: The character MUST wear a striped sweatshirt. This description must capture ALL unique features so the AI-generated character looks EXACTLY like this child."},
                        {"type": "image_url", "image_url": image_content}
                    ],
                }
            ],
            max_tokens=250,
            extra_headers={
                "HTTP-Referer": "https://kidsstories.railway.app",
                "X-Title": "Kids Story Bot"
            }
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error creating character reference: {e}")
        return "A cute child character, classic children's book illustration style"

def verify_payment_screenshot(image_data, target_handle):
    """
    Uses vision to check if the target_handle is visible in the payment screenshot.
    """
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://kidsstories.railway.app",
            "X-Title": "Kids Story Bot",
            "Content-Type": "application/json"
        }
        
        prompt = (
            f"This is a screenshot of a mobile payment or bank transfer. "
            f"Can you see the number or handle '{target_handle}' as the recipient? "
            f"If you see it, reply with exactly 'YES'. If not, reply with 'NO'. "
            f"Be precise. Do not include any other text."
        )
        
        payload = {
            "model": "google/gemini-2.0-flash-001",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        result = response.json()
        
        if result and "choices" in result:
            answer = result["choices"][0]["message"]["content"].strip().upper()
            return "YES" in answer
            
    except Exception as e:
        print(f"Error in verify_payment_screenshot: {e}")
    return False

def generate_storybook_page(character_description, page_prompt, child_name=None, is_cover=False, is_final=False):
    """
    Generates a storybook page ensuring character consistency using the description.
    
    - Uses a global system message (GLOBAL_STORYBOOK_STYLE) so the model
      understands layout, style, and character consistency requirements.
    - page_prompt should describe ONLY the specific scene for this page.
    """
    try:
        # High-level page type hint
        if is_cover:
            page_type_instructions = "TASK: Generate the COVER PAGE (page 0) for this Arabic children's storybook.\n"
        elif is_final:
            page_type_instructions = "TASK: Generate the FINAL REWARD / TIPS PAGE (page 6) for this Arabic children's storybook.\n"
        else:
            page_type_instructions = "TASK: Generate a STORY PAGE for this Arabic children's storybook.\n"

        name_part = (
            f"Child name (for layout purposes only, do NOT render literal text): {child_name}.\n"
            if child_name
            else ""
        )

        user_content = f"""
{page_type_instructions}

CHARACTER DESCRIPTION (from the uploaded photo, MUST stay identical across all pages):
{character_description}

{name_part}
SCENE DESCRIPTION:
{page_prompt}

REMINDERS:
- Use the global rules from the system message.
- Do NOT change the child's identity or outfit; only pose, camera angle, and background may change.
- Keep the bottom ~25% visually clean for Arabic text overlay.
""".strip()

        # OpenRouter image generation via Chat Completions
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://kidsstories.railway.app",
            "X-Title": "Kids Story Bot",
            "Content-Type": "application/json"
        }

        payload = {
            "model": "google/gemini-2.5-flash-image",  # Correct model for image output modality
            "messages": [
                {
                    "role": "system",
                    "content": GLOBAL_STORYBOOK_STYLE,
                },
                {
                    "role": "user",
                    "content": user_content,
                },
            ],
            "modalities": ["image"]
        }
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # DEBUG: print data to understand structure
        # print(f"DEBUG Image Data: {data}")
        
        # OpenRouter returns image URL in the messages content for image models
        # or in a special 'images' field in choices[0]
        try:
            # Check for images in message (common structure)
            message = data['choices'][0]['message']
            if 'images' in message and message['images']:
                img_data = message['images'][0]
                if isinstance(img_data, dict) and 'image_url' in img_data:
                    return img_data['image_url']['url']
                return img_data
            
            # Check for top-level images array
            if 'images' in data['choices'][0]:
                return data['choices'][0]['images'][0]
        except (KeyError, IndexError):
            pass

        content = data['choices'][0]['message']['content']
        
        import re
        url_match = re.search(r'https://\S+', content)
        if url_match:
            return url_match.group(0).rstrip(')')
        
        return content # Fallback (might be empty but it's what we have)
    except Exception as e:
        print(f"Error generating page: {e}")
        if 'response' in locals():
            print(f"Response content: {response.text}")
        return None

def transform_photo_to_character(image_data, is_url=False):
    """
    Legacy function for single-image transformation.
    """
    char_desc = create_character_reference(image_data, is_url=is_url)
    return generate_storybook_page(char_desc, "A professional character portrait")
