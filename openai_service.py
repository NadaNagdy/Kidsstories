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
        return "A cute child character, Pixar style"

def generate_storybook_page(character_description, page_prompt):
    """
    Generates a storybook page ensuring character consistency using the description.
    """
    try:
        # Define the consistent style prompt
        style_prompt = "Soft watercolor and colored pencil textures, gentle pastel color palette (soft yellows, blues, pinks), clean white background, hand-drawn, cute, and friendly aesthetic, high-quality children's book illustration."
        
        # Combining the page-specific prompt with the consistent character description and style
        full_prompt = (
            f"{style_prompt} Scene: {page_prompt}. "
            f"The main character is the SAME child in every page: {character_description}. "
            f"Ensure character consistency and facial features match exactly."
        )
        
        # OpenRouter image generation via Chat Completions
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://kidsstories.railway.app",
            "X-Title": "Kids Story Bot",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "google/gemini-2.5-flash-image", # Correct model for image output modality
            "messages": [
                {
                    "role": "user",
                    "content": full_prompt
                }
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
