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
        Now includes prefix handling (waw, fa) for better matching.
        """
        import re # Import locally to avoid messing up global imports if not needed elsewhere
        
        if self.gender == "ولد":
            return text
            
        # Dictionary of Masculine -> Feminine replacements
        # Sorted roughly by specificity/length to ensure correct matching
        replacements = {
            # Nouns/Titles
            "بطل": "بطلة",
            "ولد": "بنت",
            "صديق": "صديقة",
            "ابني": "بنتي",
            "يا حبيبي": "يا حبيبتي",
            "حبيبي": "حبيبتي",
            
            # Pronouns/Suffixes (Contextual)
            "هو": "هي",
            "هم": "هن",
            "بنفسه": "بنفسها",
            "نفسه": "نفسها",
            "لوحده": "لوحدها",
            "صاحبه": "صاحبتها",
            "أخوه": "أخوها",
            "جده": "جدها",
            "إيده": "إيدها",
            "رجله": "رجلها",
            "بؤه": "بؤها",
            "قلبه": "قلبها",
            "حواليه": "حواليها",
            "وراه": "وراها",
            "مكانه": "مكانها",
            "بيته": "بيتها",
            "أصحابه": "أصحابها",
            
            # Adjectives / States (Masculine -> Feminine)
            "شجاع": "شجاعة",
            "ذكي": "ذكية",
            "متعاون": "متعاونة",
            "مؤدب": "مؤدبة",
            "محترم": "محترمة",
            "لطيف": "لطيفة",
            "حنين": "حنينة",
            "مبسوط": "مبسوطة",
            "فرحان": "فرحانة",
            "زعلان": "زعلانة",
            "خايف": "خايفة",
            "تعبان": "تعبانة",
            "وحيد": "وحيدة",
            "جديد": "جديدة",
            "طيب": "طيبة",
            "واقف": "واقفة",
            "قاعد": "قاعدة",
            "ماسك": "ماسكة",
            "نايم": "نايمة",
            "جاهز": "جاهزة",
            "مستعد": "مستعدة",
            "شاطر": "شاطرة",
            "صغير": "صغيرة",
            "جميل": "جميلة",
            "كبير": "كبيرة",
            "مخضوض": "مخضوضة",
            
            # Verbs (Past)
            "قال": "قالت",
            "كان": "كانت",
            "حب": "حبت",
            "حس": "حست",
            "افتكر": "افتكرت",
            "وقع": "وقعت",
            "قرر": "قررت",
            "طلع": "طلعت",
            "عدى": "عدت",
            "مد": "مدت",
            "شد": "شدت",
            "قدر": "قدرت",
            "شاف": "شافت",
            "أنقذ": "أنقذت",
            "قام": "قامت",
            "فتح": "فتحت",
            "ضحك": "ضحكت",
            "وقف": "وقفت",
            "لبس": "لبست",
            "ابتسم": "ابتسمت",
            "وصل": "وصلت",
            "لقاها": "لقتها",
            "مشي": "مشيت",
            "قعد": "قعدت",
            "رجع": "رجعت",
            "خلص": "خلصت",
            "جاب": "جابت",
            "بدأ": "بدأت",
            "فكر": "فكرت",
            "وسع": "وسعت",
            "نزل": "نزلت",
            "صرخ": "صرخت",
            "اتعلم": "اتعلمت",
            "ساب": "سابت",
            "راح": "راحت",
            "لف": "لفت",
            "قسم": "قسمت",
            "عمل": "عملت",
            "همس": "همست",
            "قرب": "قربت",
            "خطف": "خطفت",
            "استأذن": "استأذنت",
            "انتبه": "انتبهت",
            "استخبى": "استخبت",
            "شاور": "شاورت",
            "دلق": "دلقت",
            "مستخباش": "مستخبتش",
            "ماجاش": "ماجاتش",
            "عرف": "عرفت",
            "ساعده": "ساعدها",
            "كدب": "كدبت",
            
            # Verbs (Present - B-prefix)
            "بيحب": "بتحب",
            "بيلعب": "بتلعب",
            "بيسلم": "بتسلم",
            "بيستخبى": "بتستخبى",
            "بيمد": "بتمد",
            "بيقف": "بتقف",
            "بيمشي": "بتمشي",
            "بيتوازن": "بتتوازن",
            "بيدور": "بتدور",
            "بيفتش": "بتفتش",
            "بيبعد": "بتبعد",
            "بيجري": "بتجري",
            "بيقول": "بتقول",
            "بيصرخ": "بتصرخ",
            "بيعيط": "بتعيط",
            "بيحضنوه": "بيحضنوها",
            "يحبوه": "يحبوها",
            "بيشارك": "بتشارك",
            "بيديها": "بتديها",
            "بيرتبهم": "بترتبهم",
            
            # Verbs (Present - Y-prefix)
            "يضحك": "تضحك",
            "يبتسم": "تبتسم",
            "يقول": "تقول",
            "يروح": "تروح",
            "يسيبه": "تسيبها", # Contextual
            "يعمل": "تعمل",
            "ينقذ": "تنقذ",
            "يكون": "تكون",
            "يصحى": "تصحى",
            "يزعل": "تزعل",
            "يقدر": "تقدر",
            "يرتاح": "ترتاح",
            "يعوز": "تعوز",
            "يطلبها": "تطلبها",
            "يضرب": "تضرب",
            "يطبطب": "تطبطب",
            "يشدها": "تشدها",
            "يأذيها": "تأذيها",
            "ياخد": "تاخد",
            "يشده": "تشده",
            "يخطفه": "تخطفه",
            "يجيب": "تجيب"
        }
        
        words = text.split()
        new_words = []
        
        for word in words:
            # Clean punctuation for matching
            # Keep punctuation separate to re-attach later
            match = re.match(r"^([وفب]?)(.+?)([\.,!؟:\"]*)$", word)
            
            if match:
                prefix, core, suffix = match.groups()
                
                # Check for direct match
                if core in replacements:
                    new_word = prefix + replacements[core] + suffix
                    new_words.append(new_word)
                    continue
                    
                # Try handling Al- (definite article)
                if core.startswith("ال") and core[2:] in replacements:
                     new_word = prefix + "ال" + replacements[core[2:]] + suffix
                     new_words.append(new_word)
                     continue
                     
                new_words.append(word)
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
