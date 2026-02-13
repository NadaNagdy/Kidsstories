import os
import json
from typing import Optional, Dict, List

# ============================================================================
# 🌟 MAGICAL STORYBOOK STYLE (Universal for All Stories)
# ============================================================================

MAGICAL_STORYBOOK_STYLE = """
Art Style: Whimsical classic children's storybook illustration, rendered in soft digital watercolor washes blended with delicate colored pencil detailing and paper texture visible.
Atmosphere: Dreamy, magical, cozy, enchanting bedtime story aesthetic with warm, soft glowing light.
Environment Details: Richly pigmented soft background gradients (deep blues, warm yellows, pastel tones), glowing luminous elements like floating golden stars with halos, and soft, fluffy cotton-like clouds. Masterpiece quality, high definition illustration.
Technical Quality: Professional children's book illustration, publication-ready, vibrant yet gentle colors, perfect for ages 1-5.
"""

# ============================================================================
# 👶 FLEXIBLE CHARACTER BUILDER (Works with ANY child character)
# ============================================================================

class CharacterBuilder:
    """
    بناء مرن للشخصية - يشتغل مع أي طفل/طفلة
    """
    
    @staticmethod
    def build_character(
        name: str = "{child_name}",
        gender: str = "neutral",
        age: str = "3-4",
        hair_style: str = "curly",
        hair_color: str = "brown",
        skin_tone: str = "warm",
        eye_color: str = "brown",
        special_features: str = ""
    ) -> str:
        """
        إنشاء وصف الشخصية بشكل مرن
        """
        
        # Base character type
        if gender == "boy":
            base = f"cute toddler boy (age {age}) named {name}"
        elif gender == "girl":
            base = f"cute toddler girl (age {age}) named {name}"
        else:
            base = f"cute toddler (age {age}) named {name}"
        
        # Hair description with magical details
        hair_styles = {
            "curly": f"beautifully detailed, voluminous flowing curly {hair_color} hair with natural bounce and shine",
            "straight": f"beautifully detailed, silky straight {hair_color} hair flowing softly",
            "wavy": f"beautifully detailed, wavy {hair_color} hair with gentle movement",
            "short": f"beautifully detailed, neat short {hair_color} hair",
            "long": f"beautifully detailed, long flowing {hair_color} hair",
            "afro": f"beautifully detailed, voluminous {hair_color} afro hair with natural texture"
        }
        
        hair_desc = hair_styles.get(hair_style, f"{hair_style} {hair_color} hair")
        
        # Build full character description
        character = f"{base} with {hair_desc}, {skin_tone} skin tone, large glossy endearing {eye_color} eyes, softly airbrushed rosy cheeks, gentle sweet smile, huggable proportions"
        
        if special_features:
            character += f", {special_features}"
            
        return character

# ============================================================================
# 🎨 UNIVERSAL MAGICAL PROMPT GENERATOR
# ============================================================================

class MagicalPromptGenerator:
    """
    مولد Prompts سحري - يشتغل مع أي قصة وأي بطل
    """
    
    def __init__(self):
        self.style = MAGICAL_STORYBOOK_STYLE.strip()
        self.character_builder = CharacterBuilder()
    
    def create_prompt(
        self,
        scene_description: str,
        character_info: Optional[Dict] = None,
        lighting: str = "warm soft lighting",
        mood: str = "cozy and magical",
        additional_details: str = ""
    ) -> str:
        """
        إنشاء Prompt كامل لأي مشهد
        
        Args:
            scene_description: وصف المشهد من ملف JSON
            character_info: معلومات البطل/البطلة (اختياري)
            lighting: نوع الإضاءة
            mood: المزاج العام
            additional_details: تفاصيل إضافية
        """
        
        # Build character description (use default if not provided)
        if character_info:
            character_desc = self.character_builder.build_character(**character_info)
        else:
            # Default: flexible character that can be customized
            character_desc = self.character_builder.build_character()
        
        # Construct the magical prompt
        prompt = f"A soft watercolor children's book illustration showing {character_desc}. "
        prompt += f"Scene details: {scene_description}. "
        prompt += f"Lighting: {lighting}. Mood: {mood}. "
        
        if additional_details:
            prompt += f"{additional_details}. "
        
        prompt += f"{self.style}"
        
        # Clean and optimize for AI generators
        return prompt.replace('\n', ' ').replace('  ', ' ').strip()
    
    def create_simple_prompt(self, scene_description: str) -> str:
        """
        نسخة مبسطة - تستخدم الإعدادات الافتراضية
        """
        return self.create_prompt(scene_description)

# ============================================================================
# 📁 JSON STORY PROCESSOR (Works with our story format)
# ============================================================================

class StoryProcessor:
    """
    معالج ملفات القصص JSON
    """
    
    def __init__(self, character_info: Optional[Dict] = None):
        self.generator = MagicalPromptGenerator()
        self.character_info = character_info
    
    def process_story_file(
        self,
        input_filepath: str,
        output_filepath: str,
        character_customization: Optional[Dict] = None
    ):
        """
        معالجة ملف قصة واحد
        """
        try:
            with open(input_filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            story_title = data.get("story_title", "Unknown Story")
            print(f"\n✨ Processing Story: {story_title}")
            
            # Use provided character or default
            char_info = character_customization or self.character_info
            
            # Process each page
            pages_count = 0
            for page in data.get("pages", []):
                original_prompt = page.get("prompt", "")
                
                # Determine lighting based on page number (optional progression)
                page_num = page.get("page_number", 1)
                lighting = self._get_lighting_for_page(page_num, len(data.get("pages", [])))
                
                # Create magical prompt
                magic_prompt = self.generator.create_prompt(
                    scene_description=original_prompt,
                    character_info=char_info,
                    lighting=lighting,
                    mood="enchanting and age-appropriate"
                )
                
                # Add to page data
                page["magic_image_prompt"] = magic_prompt
                pages_count += 1
            
            # Save enhanced JSON
            with open(output_filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ Processed {pages_count} pages successfully!")
            print(f"📁 Saved to: {output_filepath}")
            
        except FileNotFoundError:
            print(f"❌ Error: File not found - {input_filepath}")
        except json.JSONDecodeError:
            print(f"❌ Error: Invalid JSON in {input_filepath}")
        except Exception as e:
            print(f"❌ Error: {str(e)}")
    
    def _get_lighting_for_page(self, page_num: int, total_pages: int) -> str:
        """
        اختيار الإضاءة حسب رقم الصفحة (progression)
        """
        if total_pages <= 1:
            return "warm soft lighting"
        
        # Create lighting progression through the story
        progress = page_num / total_pages
        
        if progress < 0.3:
            return "bright morning sunlight with golden glow"
        elif progress < 0.6:
            return "warm afternoon light with soft shadows"
        elif progress < 0.8:
            return "golden hour glow with magical warmth"
        else:
            return "enchanting sunset light with dreamy pink and orange hues"
    
    def batch_process(self, file_pairs: List[tuple], character_info: Optional[Dict] = None):
        """
        معالجة عدة ملفات دفعة واحدة
        """
        print("\n🎨 Starting Batch Processing...")
        print(f"📚 Files to process: {len(file_pairs)}\n")
        
        for input_file, output_file in file_pairs:
            if os.path.exists(input_file):
                self.process_story_file(input_file, output_file, character_info)
            else:
                print(f"⚠️ Skipping {input_file} - File not found")
        
        print("\n🎉 Batch Processing Complete!")

# ============================================================================
# 🚀 EXAMPLE USAGE & TEMPLATES
# ============================================================================

def example_1_default_character():
    """
    مثال 1: استخدام الشخصية الافتراضية (curly hair)
    """
    print("\n" + "="*80)
    print("EXAMPLE 1: Using Default Character (Curly Hair)")
    print("="*80)
    
    processor = StoryProcessor()
    
    files = [
        ("courage.json", "courage_magical.json"),
        ("honesty.json", "honesty_magical.json"),
        ("cooperation.json", "cooperation_magical.json"),
        ("politeness.json", "politeness_magical.json")
    ]
    
    processor.batch_process(files)

def example_2_custom_character():
    """
    مثال 2: تخصيص البطل/البطلة
    """
    print("\n" + "="*80)
    print("EXAMPLE 2: Custom Character - Girl with Long Straight Hair")
    print("="*80)
    
    # تخصيص البطلة
    custom_character = {
        "name": "ليلى",
        "gender": "girl",
        "age": "4",
        "hair_style": "long",
        "hair_color": "dark brown",
        "skin_tone": "olive",
        "eye_color": "hazel",
        "special_features": "wearing a beautiful pink dress with flower patterns"
    }
    
    processor = StoryProcessor()
    
    files = [
        ("courage.json", "courage_layla_magical.json"),
    ]
    
    processor.batch_process(files, character_info=custom_character)

def example_3_boy_character():
    """
    مثال 3: بطل ولد
    """
    print("\n" + "="*80)
    print("EXAMPLE 3: Custom Character - Boy with Short Hair")
    print("="*80)
    
    # تخصيص البطل
    custom_character = {
        "name": "عمر",
        "gender": "boy",
        "age": "3",
        "hair_style": "short",
        "hair_color": "black",
        "skin_tone": "brown",
        "eye_color": "dark brown",
        "special_features": "wearing a blue striped t-shirt and comfortable shorts"
    }
    
    processor = StoryProcessor()
    
    files = [
        ("cooperation.json", "cooperation_omar_magical.json"),
    ]
    
    processor.batch_process(files, character_info=custom_character)

def example_4_single_prompt():
    """
    مثال 4: توليد prompt واحد فقط
    """
    print("\n" + "="*80)
    print("EXAMPLE 4: Generate Single Prompt")
    print("="*80)
    
    generator = MagicalPromptGenerator()
    
    # Scene from story
    scene = "child playing happily in a sunny garden with colorful flowers"
    
    # Custom character
    character = {
        "name": "نور",
        "gender": "girl",
        "age": "3",
        "hair_style": "curly",
        "hair_color": "light brown",
        "skin_tone": "fair",
        "eye_color": "green"
    }
    
    prompt = generator.create_prompt(
        scene_description=scene,
        character_info=character,
        lighting="bright cheerful morning light",
        mood="joyful and playful"
    )
    
    print("\n📝 Generated Prompt:")
    print("-" * 80)
    print(prompt)
    print("-" * 80)

# ============================================================================
# 🎯 MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🎨 MAGICAL STORYBOOK ILLUSTRATION GENERATOR")
    print("نظام مرن لتوليد رسومات سحرية لأي قصة مع أي بطل/بطلة")
    print("="*80)
    
    # اختر المثال اللي تحب تجربه:
    
    # For default character (curly hair girl from reference image):
    example_1_default_character()
    
    # Uncomment to try custom characters:
    # example_2_custom_character()
    # example_3_boy_character()
    # example_4_single_prompt()
    
    print("\n✨ Processing Complete!")
    print("\n💡 TIP: Copy the 'magic_image_prompt' from output files")
    print("   and use them in Midjourney, DALL-E 3, or Stable Diffusion!")
    print("\n" + "="*80)
