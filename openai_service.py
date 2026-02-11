import os
import base64
import requests
from openai import OpenAI

# Initialize client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

        # Using Vision capabilities to describe the child
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Using mini vision for cost efficiency
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this child's appearance in detail for a 3D Pixar-style character generation. Mention hair color, style, skin tone, and eye shape. IMPORTANT: The character MUST be wearing a striped sweatshirt. Be concise."},
                        {"type": "image_url", "image_url": image_content}
                    ],
                }
            ],
            max_tokens=150
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
        # Combining the page-specific prompt with the consistent character description
        full_prompt = f"{page_prompt}. The main character is: {character_description}. High-quality 3D render, Pixar style, consistent lighting."
        response = client.images.generate(
            model="dall-e-3", # Corrected model name
            prompt=full_prompt,
            n=1,
            size="1024x1024"
        )
        return response.data[0].url
    except Exception as e:
        print(f"Error generating page: {e}")
        return None

def transform_photo_to_character(image_data, is_url=False):
    """
    Legacy function for single-image transformation.
    Defaulting to is_url=False because we now download images in main.py.
    """
    char_desc = create_character_reference(image_data, is_url=is_url)
    return generate_storybook_page(char_desc, "A professional character portrait")
