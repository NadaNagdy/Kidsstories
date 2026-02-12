"""
Enhanced Storybook Generator - Transforms Real Child Photos into Watercolor Stories
Optimized for the soft watercolor/colored pencil style shown in reference
"""

import os
import json
from typing import Optional, Dict, List

# ============================================================================
# STYLE ANALYSIS FROM REFERENCE IMAGE
# ============================================================================

STORYBOOK_STYLE = """
Soft watercolor and colored pencil illustration style, classic children's book aesthetic, 
gentle hand-drawn quality with visible brush strokes and pencil textures, 
warm pastel color palette (soft blues, gentle greens, peachy skin tones, creamy whites),
delicate thin brown outlines, slight texture and grain like traditional watercolor paper,
clean white background with subtle vignette fade at edges,
friendly approachable art style suitable for ages 1-5,
professional children's book illustration quality similar to classic picture books
"""

# ============================================================================
# CHARACTER DESCRIPTION FROM UPLOADED PHOTO
# ============================================================================

def get_character_description_from_photo() -> str:
    """
    Based on the uploaded photo of the child:
    - Young toddler (approximately 2-3 years old)
    - Dark brown/black straight hair with neat styling
    - Warm brown skin tone
    - Large expressive dark brown eyes
    - Sweet innocent facial features with full cheeks
    - Small build, toddler proportions
    - Wearing simple white tank top/sleeveless shirt
    """
    return """
a young toddler boy, approximately 2-3 years old,
dark brown straight hair neatly styled,
warm brown/tan skin tone,
large expressive dark brown eyes with long eyelashes,
sweet innocent face with full round cheeks,
small button nose,
gentle smile,
small toddler build with chubby arms and legs,
wearing a simple white sleeveless tank top and light-colored shorts,
barefoot or simple sandals
"""

# ============================================================================
# ENHANCED PROMPT TEMPLATES
# ============================================================================

def create_master_prompt(
    character_desc: str,
    scene_action: str,
    emotion: str,
    setting: str,
    additional_elements: str = ""
) -> str:
    """
    Master prompt builder that combines style + character + scene
    """
    prompt = f"""
{STORYBOOK_STYLE}

MAIN CHARACTER:
{character_desc}
Character's expression: {emotion}
Character's pose/action: {scene_action}

SCENE SETTING:
{setting}

ADDITIONAL ELEMENTS:
{additional_elements}

COMPOSITION:
- Simple clean layout with main focus on the character
- Character positioned slightly off-center for visual interest
- Soft gradient background fading to white at edges
- Gentle lighting from upper left creating soft shadows
- Warm inviting atmosphere safe for young children
- Leave space at top or bottom for Arabic text overlay

TECHNICAL DETAILS:
- Square format (1024x1024)
- Clean white borders/margins
- Professional children's book illustration quality
- Consistent character appearance matching the description exactly
- Soft watercolor textures throughout
- No harsh lines or scary elements
"""
    return prompt.strip()


# ============================================================================
# STORY-SPECIFIC PROMPTS (Matching Your 4 Stories)
# ============================================================================

class StoryPromptGenerator:
    """Generates prompts for each story with the specific child"""
    
    def __init__(self, child_name: str = "لانا"):
        self.child_name = child_name
        self.character_desc = get_character_description_from_photo()
    
    def building_blocks_story(self) -> List[Dict]:
        """Story 1: Building Together (Ages 1-2)"""
        return [
            {
                "page": 1,
                "scene_action": "sitting on colorful play mat, holding a bright red wooden block above their head excitedly",
                "emotion": "excited and joyful, mouth open in delight, eyes sparkling",
                "setting": "sunny playroom with soft natural light from window, warm wooden floor, simple background",
                "additional": "cute brown teddy bear sitting nearby holding a yellow block in its paws, scattered colorful blocks around",
                "text": "بطلنا عاوز يبني برج كبيييير!"
            },
            {
                "page": 2,
                "scene_action": "carefully placing a red block on the floor, leaning forward with concentration",
                "emotion": "focused and determined, tongue slightly out in concentration, gentle smile",
                "setting": "same playroom, view from slightly above showing the play mat",
                "additional": "teddy bear reaching with paw to place yellow block on top, teamwork moment, soft toys in background",
                "text": "واحد ليا.. وواحد ليك. إحنا فريق!"
            },
            {
                "page": 3,
                "scene_action": "reaching up high to place a block on a tower of 6-7 colorful blocks, standing on tiptoes",
                "emotion": "proud and happy, big smile, eyes wide with accomplishment",
                "setting": "playroom with colorful block tower in center, afternoon sunlight",
                "additional": "teddy bear also reaching up to help, rainbow-colored blocks (red, blue, yellow, green), motion lines showing building action",
                "text": "سوا.. سوا.. البرج بقى عالي!"
            },
            {
                "page": 4,
                "scene_action": "sitting on floor laughing with hands raised in surprise as blocks tumble down",
                "emotion": "laughing with pure joy, mouth wide open, eyes crinkled with happiness, no sadness at all",
                "setting": "playroom with blocks scattered around mid-fall",
                "additional": "teddy bear also laughing, colorful blocks falling through air with gentle motion blur, 'بوم' effect, warm happy atmosphere",
                "text": "بوم! وقع؟ مش مهم.. يلا نبني تاني سوا."
            },
            {
                "page": 5,
                "scene_action": "hugging the teddy bear warmly with eyes closed in contentment",
                "emotion": "peaceful, happy, grateful expression, gentle satisfied smile",
                "setting": "playroom with golden sunset light streaming through window",
                "additional": "successfully built tall tower of 10+ blocks in background, soft pink and orange sunset glow, heart-shaped light particles floating, emotional heartwarming moment",
                "text": "التعاون حلو.. شكراً يا صاحبي!"
            }
        ]
    
    def giant_carrot_story(self) -> List[Dict]:
        """Story 2: Giant Carrot (Ages 2-3) - Family teamwork"""
        return [
            {
                "page": 1,
                "scene_action": "standing beside an enormous orange carrot with green leafy top half-buried in soil, looking up at it with wonder",
                "emotion": "curious and amazed, eyes wide, slight smile of surprise",
                "setting": "sunny garden with rich brown soil, blue sky with fluffy white clouds, green grass, rural countryside",
                "additional": "kind elderly grandfather with white beard pulling on carrot leaves with exaggerated effort, funny strained expression, carrot is twice grandfather's size, butterflies nearby",
                "text": "كان يا ما كان.. فيه جزرة كبيييييرة أوي في الأرض. جدو جه يشدها: يا هيلة هيلة.. مش راضية!"
            },
            {
                "page": 2,
                "scene_action": "watching grandmother grab grandfather's waist as they both pull the giant carrot together",
                "emotion": "interested and engaged, watching the action, gentle smile",
                "setting": "same garden, view showing the pulling chain forming",
                "additional": "sweet grandmother with gray hair in bun wearing flowery apron, both grandparents leaning back straining, red faces from effort, motion lines, small dust clouds at their feet",
                "text": "تيتا جت تمسك في جدو: يا هيلة هيلة.. يا هيلة هيلة.. برضه الجزرة مش راضية تطلع!"
            },
            {
                "page": 3,
                "scene_action": "running into the scene excitedly, grabbing onto grandmother's apron from behind, looking at viewer with big confident smile",
                "emotion": "determined and confident, big happy smile, eyes sparkling with helpfulness, proud to help",
                "setting": "garden with all three generations in a line",
                "additional": "grandmother smiling over shoulder welcomingly, grandfather still holding carrot top, the name {child_name} visible on child's white shirt, encouraging warm atmosphere",
                "text": f"مين جه يساعد؟ البطل {self.child_name}! مسك في تيتا وقال: أنا هساعدكم يا جدو."
            },
            {
                "page": 4,
                "scene_action": "pulling hard with all might, leaning back at 45-degree angle with grandfather and grandmother",
                "emotion": "straining with maximum effort, face showing determination, teeth gritted, eyes squeezed in concentration",
                "setting": "dramatic action moment in garden, dynamic diagonal composition",
                "additional": "all three in synchronized pulling pose, strong motion lines, giant carrot beginning to move, soil cracking around it, dust and pebbles flying, intense teamwork energy",
                "text": "كلنا مع بعض: واحد.. اتنين.. تلاتة.. شِددد!"
            },
            {
                "page": 5,
                "scene_action": "jumping and clapping with arms raised high in celebration, muddy but extremely happy",
                "emotion": "triumphant joy, huge smile showing teeth, eyes closed in pure happiness, victorious",
                "setting": "bright sunny garden with blue sky",
                "additional": "gigantic orange carrot flying in air above with trailing dirt, grandfather and grandmother also jumping and clapping, sparkles and confetti-like effect, golden celebratory light, all covered in mud but delighted",
                "text": f"تراااااخ! الجزرة طلعت. جدو قال: شكراً يا {self.child_name}! لولا تعاونك ماكانتش طلعت!"
            }
        ]
    
    def stubborn_jar_story(self) -> List[Dict]:
        """Story 3: The Stubborn Jar (Ages 3-4) - Family cooperation"""
        return [
            {
                "page": 1,
                "scene_action": "sitting at wooden table struggling to open a large clear glass jar filled with rainbow-colored clay, both hands gripping the lid tightly",
                "emotion": "frustrated but determined, face scrunched with effort, puffed cheeks, not giving up",
                "setting": "bright playroom with wooden craft table, toys visible in background, afternoon sunlight through window",
                "additional": "large transparent jar full of bright modeling clay (red, blue, yellow, green, purple), lid sealed tight, child's small hands barely wrapping around it",
                "text": "بطلنا عاوز يلعب بالصلصال، بس العلبة مقفولة أوي.. يا هيلة هيلة.. مش بتفتح!"
            },
            {
                "page": 2,
                "scene_action": "pulling on jar lid together with father, both pairs of hands overlapping on the lid",
                "emotion": "straining with effort, face showing exertion, squinted eyes, determined expression",
                "setting": "warm home interior, wooden table, cozy domestic scene",
                "additional": "caring father with rolled-up sleeves kneeling beside child, father's larger hands covering child's small hands, both pulling hard, veins showing strain, comedic struggle faces",
                "text": "بابا جه يساعد: يلا يا بطل.. زق معايا! برضه العلبة مش راضية تفتح."
            },
            {
                "page": 3,
                "scene_action": "in middle of family chain - mother holding father, father gripping jar with child, all leaning back in synchronized pulling motion",
                "emotion": "maximum effort, face red from straining, countdown energy, teeth showing from effort",
                "setting": "family home, all in living room or kitchen area",
                "additional": "mother joining from behind holding father's waist, three generations working together, dynamic diagonal composition showing teamwork, rainbow clay visible through glass jar",
                "text": "ماما جت كمان ومسكت فيهم.. واحد.. اتنين.. تلاتة.. شِدددد!"
            },
            {
                "page": 4,
                "scene_action": "falling backward with mouth open in delighted surprise as jar lid pops off",
                "emotion": "shocked surprise turning to joy, mouth wide open laughing, eyes huge with amazement",
                "setting": "home interior with action happening",
                "additional": "jar lid flying off with 'POP' effect and sparkles, colorful modeling clay balls bouncing out (red, blue, yellow, green, purple), all three family members tumbling backward, motion blur showing sudden release, celebration chaos",
                "text": "بببببببببب! العلبة اتفتحت وكلنا فرحنا بالصلصال الملون."
            },
            {
                "page": 5,
                "scene_action": "sitting at craft table making a colorful clay snake, focused on creative play, hands shaping the clay",
                "emotion": "peaceful happiness, gentle smile, eyes focused on craft, content expression",
                "setting": "wooden craft table with warm afternoon sunlight streaming through window",
                "additional": "father making a clay star, mother making a clay flower, clay scattered on table, all three engaged in bonding moment, cozy homey atmosphere, hearts floating subtly in air",
                "text": "بطلنا قال: شكراً يا فريق التعاون! إيد لوحدها متسقفش، بس إيدينا سوا بتفتح المستحيل."
            }
        ]
    
    def magic_stone_soup_story(self) -> List[Dict]:
        """Story 4: Magic Stone Soup (Ages 4-5) - Sharing and community"""
        return [
            {
                "page": 1,
                "scene_action": "standing proudly beside large black cooking pot over glowing campfire, holding up a smooth gray stone with both hands",
                "emotion": "confident and enthusiastic, big proud smile, eyes shining with excitement, leader energy",
                "setting": "forest clearing at dusk, tall trees in background, orange fire glow, magical atmosphere",
                "additional": "4-5 cute animal friends gathered around (fluffy rabbit, small squirrel, colorful bird, friendly fox) looking curious with hungry expressions, 'سر شوربة الحجر السحرية' written in glowing text in sky",
                "text": "بطلنا كان جعان هو وأصحابه ومفيش أكل. جاب حلة مية وحط فيها حجرة نظيفة وقال: أنا هعمل شوربة حجارة طعمها يجنن!"
            },
            {
                "page": 2,
                "scene_action": "receiving a bright orange carrot from rabbit friend, both hands reaching out gratefully",
                "emotion": "grateful and welcoming, warm smile, kind eyes, generous spirit",
                "setting": "around the steaming pot, firelight on faces, forest at dusk",
                "additional": "friendly brown rabbit character offering the carrot proudly, rabbit looking happy to help, white steam rising beautifully from pot, other animal friends watching with interest in background",
                "text": "صاحبه سأله: ممكن أساعد؟ بطلنا قال: يا ريت لو معاك جزرة. صاحبه جاب جزرة وحطها."
            },
            {
                "page": 3,
                "scene_action": "enthusiastically dropping vegetables into the bubbling pot, leaning forward with excitement",
                "emotion": "joyful and energized, big smile, eyes wide with delight at community forming",
                "setting": "campfire scene with multiple friends arriving, golden hour lighting",
                "additional": "gray squirrel carrying brown potatoes, blue bird flying with red tomatoes in tiny basket, orange fox bringing leafy greens, vegetables floating mid-air before entering pot, community gathering energy",
                "text": "صاحبتهم التانية جابت بطاطس، والتالت جاب طماطم. كل واحد بدأ يحط حاجة صغننة من عنده في الحلة."
            },
            {
                "page": 4,
                "scene_action": "stirring the large pot with a long wooden spoon, rising on tiptoes to reach, focused on the magical cooking",
                "emotion": "focused and happy, gentle smile, eyes watching the soup swirl, chef-like concentration",
                "setting": "around glowing campfire with magical atmosphere, evening sky",
                "additional": "delicious swirling steam clouds rising in beautiful shapes (hearts, stars, swirls), all animal friends gathered close watching eagerly with wide eyes, some sniffling the air happily, sparkles in the aromatic steam",
                "text": "الحلة بقت مليانة خضار وريحتها تحفة! بطلنا فضل يقلبها وكلهم بيساعدوا سوا بفرحة."
            },
            {
                "page": 5,
                "scene_action": "sitting in circle around fire holding wooden bowl of soup, raising the bowl in celebration",
                "emotion": "peaceful satisfaction, content smile, grateful expression, community happiness",
                "setting": "nighttime campfire scene, stars twinkling in dark blue sky above, warm fire glow",
                "additional": "all animal friends sitting together in circle with wooden bowls of steaming vegetable soup, everyone eating happily with big smiles, the removed stone sitting beside pot, communal sharing moment, magical peaceful atmosphere with friendship and abundance, hearts and sparkles floating",
                "text": "في الآخر، الحجرة طلعت شوربة حقيقية تكفي الكل! بطلنا قال: شفتوا؟ التعاون خلى الحجرة تبقى أحلى عشاء في العالم."
            }
        ]
    
    def get_story(self, story_name: str) -> List[Dict]:
        """Get prompts for specified story"""
        stories = {
            "building_blocks": self.building_blocks_story,
            "giant_carrot": self.giant_carrot_story,
            "stubborn_jar": self.stubborn_jar_story,
            "magic_stone_soup": self.magic_stone_soup_story
        }
        
        if story_name in stories:
            return stories[story_name]()
        else:
            raise ValueError(f"Unknown story: {story_name}. Choose from: {list(stories.keys())}")
    
    def generate_prompt(self, story_name: str, page_number: int) -> str:
        """Generate complete prompt for specific page"""
        story_pages = self.get_story(story_name)
        
        if page_number < 1 or page_number > len(story_pages):
            raise ValueError(f"Page {page_number} out of range for {story_name} (1-{len(story_pages)})")
        
        page_data = story_pages[page_number - 1]
        
        prompt = create_master_prompt(
            character_desc=self.character_desc,
            scene_action=page_data["scene_action"],
            emotion=page_data["emotion"],
            setting=page_data["setting"],
            additional_elements=page_data["additional"]
        )
        
        return prompt


# ============================================================================
# USAGE FUNCTIONS
# ============================================================================

def export_all_prompts_to_json(child_name: str = "لانا", output_file: str = "all_story_prompts.json"):
    """Export all prompts for all stories to JSON file"""
    generator = StoryPromptGenerator(child_name)
    
    all_stories = {}
    
    for story_name in ["building_blocks", "giant_carrot", "stubborn_jar", "magic_stone_soup"]:
        story_pages = generator.get_story(story_name)
        
        all_stories[story_name] = {
            "pages": []
        }
        
        for i, page_data in enumerate(story_pages, 1):
            prompt = generator.generate_prompt(story_name, i)
            
            all_stories[story_name]["pages"].append({
                "page_number": i,
                "arabic_text": page_data["text"],
                "full_prompt": prompt,
                "scene_summary": page_data["scene_action"]
            })
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_stories, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Exported all prompts to {output_file}")
    return output_file


def print_story_prompts(story_name: str, child_name: str = "لانا"):
    """Print all prompts for a specific story"""
    generator = StoryPromptGenerator(child_name)
    story_pages = generator.get_story(story_name)
    
    print(f"\n{'='*80}")
    print(f"STORY: {story_name.upper().replace('_', ' ')}")
    print(f"Child Name: {child_name}")
    print(f"{'='*80}\n")
    
    for i in range(1, len(story_pages) + 1):
        prompt = generator.generate_prompt(story_name, i)
        print(f"\n{'─'*80}")
        print(f"PAGE {i}")
        print(f"{'─'*80}")
        print(f"\nARABIC TEXT: {story_pages[i-1]['text']}")
        print(f"\nFULL PROMPT:")
        print(prompt)
        print()


def create_quick_reference(child_name: str = "لانا", output_file: str = "quick_reference.md"):
    """Create a markdown quick reference guide"""
    generator = StoryPromptGenerator(child_name)
    
    content = f"""# 🎨 Quick Reference - Personalized Storybook Prompts

## Child Character Details
{generator.character_desc}

## Style Reference
{STORYBOOK_STYLE}

---

## 📚 Available Stories

1. **Building Blocks** (Ages 1-2) - Simple cooperation with teddy bear
2. **Giant Carrot** (Ages 2-3) - Family teamwork with grandparents
3. **Stubborn Jar** (Ages 3-4) - Family cooperation and persistence
4. **Magic Stone Soup** (Ages 4-5) - Community sharing with animal friends

---

## 🚀 How to Use These Prompts

### For ChatGPT (DALL-E 3):
1. Copy the FULL PROMPT exactly as written
2. Paste into ChatGPT with DALL-E 3 enabled
3. Generate the image
4. Save and move to next page

### For Midjourney:
- Add `--ar 1:1 --style raw --v 6` at the end
- May need to split very long prompts

### For Stable Diffusion:
- Use positive prompt from main section
- Add negative prompts: "scary, dark, violent, adult, realistic photo"

---

## 💡 Pro Tips

✅ **DO:**
- Use complete prompts without editing
- Generate all pages of one story in same session
- Save character description for consistency
- Keep the watercolor style specification

❌ **DON'T:**
- Shorten or simplify prompts
- Change character description mid-story
- Skip the style reference section
- Mix different art styles

---

## 📖 Story Pages Overview

"""
    
    for story_name in ["building_blocks", "giant_carrot", "stubborn_jar", "magic_stone_soup"]:
        story_pages = generator.get_story(story_name)
        content += f"\n### {story_name.replace('_', ' ').title()}\n\n"
        
        for i, page in enumerate(story_pages, 1):
            content += f"**Page {i}:** {page['scene_action'][:60]}...\n"
            content += f"*Text:* {page['text']}\n\n"
    
    content += """
---

## 🎯 Quality Checklist

Before accepting each generated image:

- [ ] Character matches the photo (dark hair, brown skin, white tank top)
- [ ] Watercolor/colored pencil style is consistent
- [ ] Soft pastel colors throughout
- [ ] Clean white background with vignette
- [ ] Expression matches the emotion described
- [ ] Space available for Arabic text overlay
- [ ] Safe and positive for young children
- [ ] Consistent with previous pages in same story

---

Generated for: **{child_name}**
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Created quick reference: {output_file}")
    return output_file


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    import sys
    
    # Get child name from command line or use default
    child_name = sys.argv[1] if len(sys.argv) > 1 else "لانا"
    
    print(f"\n🎨 Generating prompts for {child_name}...\n")
    
    # Export everything to JSON
    json_file = export_all_prompts_to_json(child_name, "personalized_story_prompts.json")
    
    # Create quick reference guide
    ref_file = create_quick_reference(child_name, "quick_reference_guide.md")
    
    # Print first story as example
    print("\n" + "="*80)
    print("EXAMPLE: BUILDING BLOCKS STORY - PAGE 1")
    print("="*80)
    
    generator = StoryPromptGenerator(child_name)
    example_prompt = generator.generate_prompt("building_blocks", 1)
    print(example_prompt)
    
    print(f"\n\n✅ All files generated successfully!")
    print(f"📄 Full prompts: {json_file}")
    print(f"📖 Quick reference: {ref_file}")
    print(f"\n💡 To see all prompts for a specific story, run:")
    print(f"   python script.py [child_name] [story_name]")
