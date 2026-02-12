import json
import os

# 1. DEFINE YOUR MASTER STYLE (One place to change it all!)
MASTER_STYLE = """
Soft watercolor and colored pencil illustration style, classic children's book aesthetic, 
gentle hand-drawn quality, warm pastel colors, clean white background, 
professional children's book illustration.
"""

# 2. DEFINE MASTER CHARACTER (Loaded from your photo analysis)
# In the real app, this comes from the uploaded photo analysis
DEFAULT_CHARACTER = """
A toddler boy, 2-3 years old, curly brown hair, warm skin tone, 
wearing a striped t-shirt and denim shorts.
"""

def load_story_data(theme_name):
    """Loads the clean story data from JSON"""
    filename = f"{theme_name}.json"
    if not os.path.exists(filename):
        print(f"❌ Error: Could not find {filename}")
        return None
        
    with open(filename, 'r', encoding='utf-8') as f:
        return json.load(f)

def build_full_prompt(scene, emotion, character_desc=DEFAULT_CHARACTER):
    """Combines all elements into the final PRO prompt"""
    return f"""
{MASTER_STYLE}

MAIN CHARACTER:
{character_desc}
Expression: {emotion}

SCENE ACTION:
{scene}

COMPOSITION:
Square format, consistent character, plenty of white space for text.
"""

# 3. GENERATE THE ASSETS
def prepare_story_for_generation(theme, character_desc):
    data = load_story_data(theme)
    if not data: return
    
    print(f"📘 Preparing Story: {data.get('title', theme)}")
    
    generated_pages = []
    
    for page in data['pages']:
        full_prompt = build_full_prompt(
            scene=page['scene_description'],
            emotion=page['emotion'],
            character_desc=character_desc
        )
        
        # This is what you send to the API
        page_payload = {
            "page": page['page_number'],
            "text": page['arabic_text'],
            "prompt": full_prompt
        }
        generated_pages.append(page_payload)
        
    return generated_pages

# Example Usage:
# final_story = prepare_story_for_generation("courage", DEFAULT_CHARACTER)
