import os
from openai import OpenAI

# Initialize client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def create_character_reference(image_url):
    """
    Analyzes the photo and creates a character description for consistency.
    """
    try:
        # Using Vision capabilities to describe the child
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Using mini vision for cost efficiency
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this child's appearance in detail for a 3D Pixar-style character generation. Mention hair color, style, skin tone, eye shape, and clothing colors. Be concise."},
                        {"type": "image_url", "image_url": {"url": image_url}}
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
            model="gpt-image-1-mini", # The cost-effective model
            prompt=full_prompt,
            n=1,
            size="1024x1024"
        )
        return response.data[0].url
    except Exception as e:
        print(f"Error generating page: {e}")
        return None

def transform_photo_to_character(image_url):
    """
    Legacy function for single-image transformation.
    """
    char_desc = create_character_reference(image_url)
    return generate_storybook_page(char_desc, "A professional character portrait")
