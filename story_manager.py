import json
import os
import logging

logger = logging.getLogger(__name__)

# ==========================================================
# GLOBAL MASTER STYLE LOCK
# ==========================================================

MASTER_STYLE = """
High-end 3D CGI Animated Movie Style (Pixar/Disney inspired),
Octane Render, 8k resolution, volumetric lighting,
Subsurface scattering on skin, detailed hair strands,
Cinematic composition, depth of field,
Vibrant and warm color palette,
Expressive character animation style,
No 2D, no drawing, no watercolor, no sketch style.
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

    def __init__(self, child_name, gender="ولد"):
        self.child_name = child_name
        self.gender = gender
        self.character_desc = ""
        self.personality_block = ""
        self.outfit_lock = ""

    # ------------------------------------------------------
    # Gender Adaptation Logic
    # ------------------------------------------------------
    
    def _apply_gender_replacements(self, text):
        """
        Adapts Arabic text from masculine (default) to feminine if the child is a girl.
        Covers common verbs, adjectives, and pronouns used in the stories.
        """
        if self.gender == "ولد":
            return text
            
        # Dictionary of Masculine -> Feminine replacements
        # Sorted by length (descending) to avoid partial replacements (e.g. replacing 'هو' inside 'هواية')
        replacements = {
            "بطل": "بطلة",
            "صديقه": "صديقتها",
            "هو": "هي",
            "بنفسه": "بنفسها",
            "مستخباش": "مستخبتش",
            "راح": "راحت",
            "شاور": "شاورت",
            "زعلان": "زعلانه",
            "بيحضنوه": "بيحضنوها",
            "يحبوه": "يحبوها",
            "شاطر": "شاطرة",
            "صغير": "صغيرة",
            "جميل": "جميلة",
            "كبير": "كبيرة",
            "قال": "قالت",
            "كان": "كانت",
            "قرر": "قررت",
            "استخبى": "استخبت",
            "صرخ": "صرخت",
            "يضحك": "تضحك",
            "واقف": "واقفة",
            "خايف": "خايفة",
            "مخضوض": "مخضوضة",
            "ماجاش": "ماجاتش",
            "شافه": "شافها",
            "عرف": "عرفت",
            "ساعده": "ساعدها",
            "بيصرخ": "بتصرخ",
            "نفسه": "نفسها",
            "لوحده": "لوحدها",
            "شعره": "شعرها",
            "إيده": "إيدها",
            "رجله": "رجلها",
            "وجعته": "وجعتها",
            "افتكره": "افتكرها",
            "بيعيط": "بتعيط",
            "كدب": "كدبت",
            "سألت": "سألت", # Already feminine/neutral or correct context
            "يا حبيبي": "يا حبيبتي",
            "ابني": "بنتي",
            "ولد": "بنت"
        }
        
        # Simple word boundary replacement to avoid messing up substrings
        # Note: This is a basic implementation. For complex Arabic NLP, a library would be needed.
        words = text.split()
        new_words = []
        for word in words:
            # Check for exact matches first (ignoring simple punctuation attached)
            clean_word = word.strip(".,!؟")
            if clean_word in replacements:
                # Replace the core word but keep punctuation
                replacement = replacements[clean_word]
                new_word = word.replace(clean_word, replacement)
                new_words.append(new_word)
            else:
                new_words.append(word)
                
        return " ".join(new_words)

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

    def set_outfit_by_age(self, age_group, extracted_outfit=None):
        """
        Sets the outfit lock. 
        If 'extracted_outfit' is provided (from AI analysis), it uses that.
        Otherwise, it falls back to age-appropriate defaults.
        """
        if extracted_outfit:
            self.outfit_lock = f"Wearing {extracted_outfit}"
            return

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
Wide environmental shots,
Detailed background setting visible,
Dynamic camera angles (low angle, side view, etc.),
Rule of thirds,
Balanced framing,
Rich scene details.
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

            # Ensure we don't overwrite the outfit if it was already set externally
            # self.set_outfit_by_age(age_group) # Removed to preserve extracted outfit

            generated_pages = []

            for page in age_data.get('pages', []):

                raw_prompt = page.get('magic_image_prompt', page.get('prompt', ''))

                full_prompt = self.build_full_prompt(base_prompt=raw_prompt)

                # 1. Replace name first
                display_text = page.get('text', '').replace("{child_name}", self.child_name)
                
                # 2. Apply gender adaptation (if girl)
                display_text = self._apply_gender_replacements(display_text)

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
