import json
import os
import logging

logger = logging.getLogger(__name__)

# 1. DEFINE YOUR MASTER STYLE
MASTER_STYLE = """
Soft watercolor and colored pencil illustration style, classic children's book aesthetic, 
gentle hand-drawn quality, warm pastel colors, clean white background, 
professional children's book illustration.
"""

class StoryManager:
    def __init__(self, child_name):
        self.child_name = child_name
        self.character_desc = ""  # This will be injected from main.py after photo analysis

    def build_full_prompt(self, scene, emotion):
        """Combines all elements into the final PRO prompt"""
        char = self.character_desc if self.character_desc else "A cute child character"
        return f"""
{MASTER_STYLE}

MAIN CHARACTER:
{char}
Expression: {emotion}

SCENE ACTION:
{scene}

COMPOSITION:
Square format, consistent character, plenty of white space for text.
"""

    def generate_story_prompts(self, json_filename, age_group):
        """
        Loads the story from stories_content/ folder and prepares prompts.
        Matches the call in main.py: manager.generate_story_prompts(json_filename, age_group)
        """
        # Ensure path points to your stories_content folder
        filepath = os.path.join("stories_content", json_filename)
        
        if not os.path.exists(filepath):
            logger.error(f"❌ Error: Could not find {filepath}")
            return None
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Navigate to the specific age group
            age_data = data.get(age_group)
            if not age_data:
                logger.error(f"❌ Error: Age group {age_group} not found in {json_filename}")
                return None

            generated_pages = []
            
            for page in age_data['pages']:
                full_prompt = self.build_full_prompt(
                    scene=page['scene_description'],
                    emotion=page['emotion']
                )
                
                # Format text to include the child's name
                display_text = page['text'].replace("{child_name}", self.child_name)
                
                page_payload = {
                    "page": page['page_number'],
                    "text": display_text,
                    "prompt": full_prompt
                }
                generated_pages.append(page_payload)
                
            return generated_pages

        except Exception as e:
            logger.error(f"❌ Error loading JSON: {e}")
            return None
