import json
import os
import logging

logger = logging.getLogger(__name__)

# ==========================================================
# GLOBAL MASTER STYLE LOCK
# ==========================================================

MASTER_STYLE = """
Soft watercolor and colored pencil illustration style,
classic premium children's book aesthetic,
gentle hand-drawn texture,
warm pastel color palette,
clean white background,
professional publishing quality,
consistent character proportions,
no realism, no photographic style.
"""

ANTI_DRIFT_RULES = """
CRITICAL CHARACTER CONSISTENCY RULES:

- Face structure must remain IDENTICAL across all pages
- Eye shape and size must never change
- Skin tone must remain exactly the same
- Hair color and texture must not vary
- No random facial changes
- No aging or proportion shifts
"""


# ==========================================================
# STORY MANAGER PRO VERSION
# ==========================================================

class StoryManager:

    def __init__(self, child_name):
        self.child_name = child_name
        self.character_desc = ""
        self.personality_block = ""
        self.outfit_lock = ""

    # ------------------------------------------------------
    # Inject Character DNA (from Vision)
    # ------------------------------------------------------

    def inject_character_dna(self, dna_description: str):
        """Inject detailed physical description extracted from Vision"""
        self.character_desc = dna_description

    # ------------------------------------------------------
    # Inject Personality Memory
    # ------------------------------------------------------

    def inject_personality(self, traits=None, core_value=None):

        if not traits:
            traits = []

        traits_text = ", ".join(traits)

        self.personality_block = f"""
CHARACTER PERSONALITY MEMORY:

Name: {self.child_name}
Core traits: {traits_text}
Core value focus: {core_value if core_value else "kindness"}

Expressions and body language should reflect these traits.
"""

    # ------------------------------------------------------
    # Outfit Lock
    # ------------------------------------------------------

    def set_outfit_by_age(self, age_group):

        if age_group == "1-2":
            self.outfit_lock = "Soft pastel romper, toddler proportions"
        elif age_group == "2-3":
            self.outfit_lock = "Cute overalls with colorful shirt"
        elif age_group == "3-4":
            self.outfit_lock = "Playful shorts and bright t-shirt"
        else:
            self.outfit_lock = "Colorful casual children outfit"

    # ------------------------------------------------------
    # Build Full Prompt (Ultra Pro)
    # ------------------------------------------------------

    def build_full_prompt(self, base_prompt):

        character_block = self.character_desc if self.character_desc else "A cute child character"

        return f"""
{MASTER_STYLE}

{ANTI_DRIFT_RULES}

MAIN CHARACTER DNA (DO NOT MODIFY):

{character_block}

OUTFIT LOCK:
{self.outfit_lock}

{self.personality_block}

SCENE ACTION:
{base_prompt}

COMPOSITION:
Square format,
Plenty of white space for Arabic text,
Child centered,
Balanced framing,
Consistent lighting across pages.
"""

    # ------------------------------------------------------
    # Generate Story Prompts
    # ------------------------------------------------------

    def generate_story_prompts(self, json_filename, age_group):

        filepath = os.path.join("stories_content", json_filename)

        if not os.path.exists(filepath):
            logger.error(f"❌ Error: Could not find {filepath}")
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            age_data = data.get("age_groups", {}).get(age_group)

            if not age_data:
                logger.error(f"❌ Age group {age_group} not found in {json_filename}")
                return None

            # Ensure outfit matches age
            self.set_outfit_by_age(age_group)

            generated_pages = []

            for page in age_data.get('pages', []):

                raw_prompt = page.get('magic_image_prompt', page.get('prompt', ''))

                full_prompt = self.build_full_prompt(base_prompt=raw_prompt)

                display_text = page.get('text', '').replace("{child_name}", self.child_name)

                page_payload = {
                    "page": page.get('page_number'),
                    "text": display_text,
                    "prompt": full_prompt
                }

                generated_pages.append(page_payload)

            return generated_pages

        except Exception as e:
            logger.error(f"❌ Error loading JSON: {e}")
            return None
