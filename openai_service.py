import os
from openai import OpenAI

# Initialize client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def transform_photo_to_character(image_url):
    """
    Calls OpenAI GPT-Image-1 Mini to transform a photo into a cartoon character.
    Returns the URL of the generated image.
    """
    try:
        # Note: As of my latest knowledge, GPT-Image-1 Mini uses the specific endpoint
        # for multimodal image generation/transformation.
        # This is a placeholder for the actual API call structure.
        response = client.images.generate(
            model="gpt-image-1-mini",
            prompt="A Pixar-style 3D cartoon character based on this child's photo. Maintain hair color, skin tone, and features. White background.",
            image=image_url, # Image-to-image/Multimodal support
            n=1,
            size="1024x1024"
        )
        return response.data[0].url
    except Exception as e:
        print(f"Error in OpenAI transformation: {e}")
        return None
