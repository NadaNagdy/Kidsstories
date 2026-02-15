import json
import os
import logging

logger = logging.getLogger(__name__)

# ==========================================================
# GLOBAL MASTER STYLE LOCK
# ==========================================================

MASTER_STYLE = """
Classic children's book illustration in traditional soft watercolor and pencil style,
Limited pastel color palette with low contrast and visible paper grain textures,
Focus on a flat, painterly aesthetic with delicate pencil outlines and hand-drawn details,
Warm and inviting atmosphere with gentle, diffused lighting,
Whimsical, heartwarming mood,
No cinematic lighting, no 3D effects, no intense glowing highlights.
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
        import re 
        
        if self.gender == "ولد":
            return text
            
        # Dictionary of Masculine -> Feminine replacements
        replacements = {
            # Nouns/Titles
            "بطل": "بطلة",
            "ولد": "بنت",
            "صديق": "صديقة",
            "ابني": "بنتي",
            "يا حبيبي": "يا حبيبتي",
            "حبيبي": "حبيبتي",
            "مستكشف": "مستكشفة",
            "شاطر": "شاطرة",
            "صغير": "صغيرة",
            "جميل": "جميلة",
            "كبير": "كبيرة",
            "مخضوض": "مخضوضة",
            "آسف": "آسفة",
            "غلطان": "غلطانة",

            # Pronouns/Suffixes
            "هو": "هي",
            "هم": "هن",
            "أنت": "أنتي",
            "لك": "ليكي",
            "بنفسه": "بنفسها",
            "نفسه": "نفسها",
            "لنفسه": "لنفسها",
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
            "أصحابه": " أصحابها",
            "سريره": "سريرها",
            "شنطته": "شنطتها",
            "لعبته": "لعبتها",
            "هدومه": "هدومها",
            "إنه": "إنها",
            "له": "لها",
            "عنده": "عندها",
            "منه": "منها",
            "شجاعته": "شجاعتها",

            # Adjectives / States
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
            "عايز": "عايزة",
            "واثقة": "واثقة", # Already fem usually but good to have
            "سعيد": "سعيدة",
            "رايح": "رايحة",

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
            "عرف": "عرفت",
            "ساعده": "ساعدها",
            "كدب": "كدبت",
            "حط": "حطت",
            "حضنه": "حضنته",
            "زعل": "زعلت", 
            "عاش": "عاشت",
            
            # Verbs (Present)
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
            "بيشارك": "بتشارك",
            "بيديها": "بتديها",
            "بيرتبهم": "بترتبهم",
            "بيتخيل": "بتتخيل",
            "بيحضر": "بتحضر",
            
            # Imperative / Future
            "تعالى": "تعالي",
            "هيقابلهم": "هتقابلهم",
            "مبقاش": "مبقتش",
            "ماجاش": "ماجاتش",
            "مستخباش": "مستخبتش",

            # Verbs (Y-prefix -> T-prefix)
            "يضحك": "تضحك",
            "يبتسم": "تبتسم",
            "يقول": "تقول",
            "يروح": "تروح",
            "يسيبه": "تسيبه", 
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
            "يجيب": "تجيب",
            "يحس": "تحس",
            "يخاف": "تخاف",
            "يجيبه": "تجيبه",
            "يحضر": "تحضر",
            "يساعد": "تساعد",
            "يشيل": "تشيل",
            "يرتب": "ترتب",
            "يكلم": "تكلم",
            "يسمع": "تسمع",
            "يحترم": "تحترم"
        }
        
        words = text.split()
        new_words = []
        
        # Tashkeel removal regex
        tashkeel_pattern = re.compile(r'[\u0617-\u061A\u064B-\u0652]')
        
        for word in words:
            # Clean punctuation for matching using Regex
            match = re.match(r"^([وفب]?)(.*?)([\.,!؟:\"]*)$", word)
            
            if match:
                prefix, body, suffix = match.groups()
                
                # Remove tashkeel from body for lookup
                clean_body = tashkeel_pattern.sub("", body)
                clean_full_core = prefix + clean_body
                
                # Normalization (Alef)
                clean_body = clean_body.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")
                clean_full_core = clean_full_core.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا")

                # Strategy 1: Check FULL word 
                if clean_full_core in replacements:
                    replacement = replacements[clean_full_core]
                    new_word = replacement + suffix
                    new_words.append(new_word)
                    continue
                
                # Strategy 2: Check BODY only
                if clean_body in replacements:
                    replacement = replacements[clean_body]
                    new_word = prefix + replacement + suffix
                    new_words.append(new_word)
                    continue
                
                # Strategy 3: Check "Al-" + body
                if clean_body.startswith("ال") and clean_body[2:] in replacements:
                    replacement = replacements[clean_body[2:]]
                    new_word = prefix + "ال" + replacement + suffix
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
