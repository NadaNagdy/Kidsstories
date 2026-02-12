"""
HONESTY & TRUTH THEMED STORYBOOK PROMPTS
Transforming the uploaded child photo into watercolor illustrations
Theme: الصدق (Honesty/Truthfulness)
"""

import json

# Same character description from the photo
CHARACTER_DESC = """
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

# Same watercolor style
WATERCOLOR_STYLE = """
Soft watercolor and colored pencil illustration style, classic children's book aesthetic,
gentle hand-drawn quality with visible brush strokes and pencil textures,
warm pastel color palette (soft blues, gentle greens, peachy skin tones, creamy whites),
delicate thin brown outlines, slight texture and grain like traditional watercolor paper,
clean white background with subtle vignette fade at edges,
friendly approachable art style suitable for ages 1-5,
professional children's book illustration quality similar to classic picture books
"""


class HonestyStoriesGenerator:
    """Generates prompts for Honesty-themed stories"""
    
    def __init__(self, child_name: str = "لانا"):
        self.child_name = child_name
    
    def story_1_spilled_water(self) -> list:
        """Story 1: The Spilled Water (Ages 1-2) - Simple truth-telling"""
        return [
            {
                "page": 1,
                "scene_action": "playing energetically in a bright room, accidentally bumping a small table with a glass of water on it, water splashing",
                "emotion": "surprised and startled, eyes wide, mouth forming 'oh!' shape, innocent shock",
                "setting": "cozy living room with soft carpet, wooden table, warm afternoon light through window",
                "additional": "glass of water tipping over with water splashing out in mid-air, water droplets frozen in motion, wet spot forming on floor, simple home environment",
                "text": "المية دلقت.. طش! الهدوم مبلولة!"
            },
            {
                "page": 2,
                "scene_action": "standing still looking up at mother with thoughtful expression, hand on chin in thinking pose",
                "emotion": "thoughtful and contemplative, eyes looking upward, considering what to say, innocent thinking face",
                "setting": "same living room, mother standing nearby looking down with gentle questioning expression",
                "additional": "caring mother in pastel dress with kind face, wet spot visible on floor, mother's body language is questioning but not angry, warm supportive atmosphere",
                "text": "ماما سألت: مين؟ بطلنا فكر.."
            },
            {
                "page": 3,
                "scene_action": "pointing at own chest with small finger, looking directly up at mother with honest open expression, standing brave",
                "emotion": "brave and truthful, clear honest eyes making eye contact, small proud smile, no fear, confident in truth",
                "setting": "close-up view in living room, focus on toddler and mother interaction",
                "additional": "toddler's finger pointing to own chest, direct eye contact with mother showing honesty, open body language, wet floor still visible, moment of truth",
                "text": "بطلنا قال: أنا! هو مش خايف، هو صادق."
            },
            {
                "page": 4,
                "scene_action": "watching mother kneel down wiping the water with a cloth, mother smiling warmly at the toddler",
                "emotion": "relieved and happy, gentle smile, feeling good about telling truth, relaxed shoulders",
                "setting": "living room, mother kneeling on floor cleaning, toddler standing nearby",
                "additional": "mother wiping water with soft cloth, big warm smile on mother's face showing approval, 'برافو!' text effect near mother, hearts floating subtly, positive reinforcement moment",
                "text": "ماما قالت: برافو! إنت بطل عشان قلت الحق"
            },
            {
                "page": 5,
                "scene_action": "playing happily with mother, both laughing together, sitting on clean floor with toys",
                "emotion": "joyful and content, big happy laugh, eyes crinkled with joy, peaceful satisfaction",
                "setting": "same living room now clean and tidy, golden afternoon light, warm cozy atmosphere",
                "additional": "mother and toddler playing together with colorful blocks or soft toys, both smiling and laughing, floor is clean and dry, hearts and gentle sparkles showing love and trust, happy ending",
                "text": "بطلنا فرحان.. الصدق جميل يا أبطال."
            }
        ]
    
    def story_2_garden_ball(self) -> list:
        """Story 2: The Garden Ball (Ages 2-3) - Taking responsibility"""
        return [
            {
                "page": 1,
                "scene_action": "playing with a colorful soft ball in a beautiful garden, kicking it gently, full of energy",
                "emotion": "playful and energetic, big smile, eyes focused on the ball, innocent joy",
                "setting": "sunny garden with green grass, few trees in background, blue sky, outdoor play area",
                "additional": "cute fluffy white sheep nearby saying 'ماء ماء' with speech bubble, colorful ball in mid-kick, flowers and plants scattered around, cheerful garden scene",
                "text": f"كان يا ما كان.. فيه شجر كتير وخروف بيقول ماء ماء. {self.child_name} كان بيلعب بالكورة."
            },
            {
                "page": 2,
                "scene_action": "watching in shock as the ball flies through air and hits a beautiful potted flower, plant tipping over",
                "emotion": "shocked and worried, hands to face, eyes very wide, 'oh no!' expression, concerned",
                "setting": "garden with focus on the accident moment, plant in decorative pot",
                "additional": "colorful ball in mid-flight with motion lines, beautiful flower in terracotta pot falling and breaking, soil spilling, 'بوم!' effect text, dramatic accident moment, sheep watching from distance",
                "text": "الكورة طارت.. بوم! خبطت في الزرع ووقعته على الأرض. يا خبر!"
            },
            {
                "page": 3,
                "scene_action": "standing near the broken plant, looking at it while mother approaches asking questions",
                "emotion": "nervous but thinking, biting lip slightly, eyes darting between mother and plant, contemplating",
                "setting": "garden scene with mother arriving, broken plant visible on ground",
                "additional": "mother in pastel dress walking toward scene with questioning expression, white sheep hiding behind a large tree trunk peeking out, broken pot and scattered soil visible, tension moment",
                "text": "ماما جت وسألت: مين عمل كده؟ الخروف جري واستخبى ورا الشجرة."
            },
            {
                "page": 4,
                "scene_action": "standing tall with hand raised bravely, holding the ball, looking at mother with determined honest expression",
                "emotion": "brave and courageous, standing straight, honest eyes looking up, determined to tell truth, heroic moment",
                "setting": "garden with mother and toddler in focus, trees in background",
                "additional": "toddler holding the colorful ball in one hand, other hand raised like taking oath, brave confident stance despite being small, mother listening attentively, sheep still peeking from behind tree, moment of courage",
                "text": f"{self.child_name} البطل فكر.. وقال بصوت شجاع: أنا يا ماما.. أنا قولت الحق!"
            },
            {
                "page": 5,
                "scene_action": "being hugged warmly by mother, both smiling, embraced in loving hug in the garden",
                "emotion": "happy and loved, peaceful smile, eyes closed in contentment, feeling safe and proud",
                "setting": "sunny garden with warm golden light, flowers in background",
                "additional": "mother kneeling and hugging toddler tightly, both with big happy smiles, large glowing heart shape in background, checkmark symbol floating nearby, sheep coming out happily from behind tree, warm colors, celebration of honesty",
                "text": "ماما حضنته أوي: يا روحي يا بطل! عشان إنت صادق، أنا مش زعلانة.. إنت بطل الصدق!"
            }
        ]
    
    def story_3_broken_vase(self) -> list:
        """Story 3: The Broken Vase (Ages 3-4) - Honesty even when scared"""
        return [
            {
                "page": 1,
                "scene_action": "kicking a soft colorful ball energetically in a cozy room, playing near a table with a beautiful decorative vase",
                "emotion": "joyful and energetic, mouth open in playful 'hoop!' expression, full of innocent play energy",
                "setting": "warm home interior, wooden table with colorful ceramic vase, soft carpet, afternoon sunlight",
                "additional": "beautiful colorful vase on wooden table (toddler is half the table height), soft ball in motion, simple cozy room with minimal background, focus on joyful play moment",
                "text": f"كان يا ما كان.. فيه فازة جميلة أوي ماما بتحبها. {self.child_name} كان بيلعب كورة.. 'هوب!'."
            },
            {
                "page": 2,
                "scene_action": "standing in frozen shock, hands on cheeks, watching the vase falling and shattering after ball hit the table",
                "emotion": "extreme shock and horror, mouth wide open, eyes huge with fear and surprise, hands on face",
                "setting": "same room, focus on the accident happening in slow motion",
                "additional": "ball hitting table edge, beautiful vase tumbling through air mid-fall, pieces breaking apart, 'كررراش!' sound effect, toddler (half height of table) standing nearby frozen in shock, dramatic accident moment with motion lines",
                "text": "الكورة خبطت في الفازة.. 'كررراش!'. الفازة وقعت واتكسرت. يا خبر! أعمل إيه دلوقتي؟"
            },
            {
                "page": 3,
                "scene_action": "thinking hard with finger on chin, looking between mother who just entered and a toy cat in the corner",
                "emotion": "conflicted and thinking deeply, worried expression, eyebrows furrowed, considering options, internal struggle",
                "setting": "room with broken vase pieces on floor, mother entering doorway",
                "additional": "gentle mother in pastel clothing entering with concerned expression (toddler is hip-height to mother), toddler thinking with finger on chin, small toy cat visible in background, broken vase pieces scattered on floor, moment of decision",
                "text": "ماما جت سألت: 'مين كسر الفازة؟'. بطلنا فكر.. ممكن أقول القطة؟ لا، أنا بطل."
            },
            {
                "page": 4,
                "scene_action": "standing straight and tall with back straight, facing mother directly, hands open honestly, looking up sincerely",
                "emotion": "brave and sincere, clear honest eyes making direct contact, standing proud despite being scared, courageous honesty",
                "setting": "close view in room, focus on honest interaction between toddler and mother",
                "additional": "toddler standing with perfect posture (exactly half mother's height), back straight, facing mother with open hands showing sincerity, mother listening with visible compassion and warmth, moment of truth and courage",
                "text": "بطلنا وقف ضهره مفرود وقال: 'أنا يا ماما.. أنا اللي خبطتها غصب عني.. أنا آسف'."
            },
            {
                "page": 5,
                "scene_action": "being hugged tightly by mother, both smiling warmly, together cleaning up the vase pieces safely with a small broom",
                "emotion": "relieved and happy, peaceful loving smile, feeling safe in mother's embrace, content and proud",
                "setting": "sunlit room with warm golden light, clean and safe atmosphere",
                "additional": "mother hugging small toddler tightly (toddler is much smaller embraced by mother), both with warm smiles, small child-safe broom nearby for cleaning together, broken vase pieces being carefully managed, glowing heart shapes, warm sunny light through window, happy resolution",
                "text": "ماما حضنته وقالت: 'الفازة تتصلح، بس صدقك هو الأغلى عندي! إنت بطل الصدق يا حبيبي'."
            }
        ]
    
    def story_4_emperor_seeds(self) -> list:
        """Story 4: The Emperor's Seeds (Ages 4-5) - Truth vs. peer pressure"""
        return [
            {
                "page": 1,
                "scene_action": "standing in an ancient Chinese palace courtyard, receiving a small flower pot with soil and seeds from a wise emperor, holding it carefully",
                "emotion": "excited and proud, happy smile, eyes bright with anticipation, feeling special and chosen",
                "setting": "beautiful ancient Chinese palace courtyard with traditional architecture, decorative gardens, other children in traditional clothing in background",
                "additional": "wise elderly emperor in simple robes giving seed to toddler, other children also receiving pots, toddler holding small terracotta pot carefully, traditional Chinese palace with curved roofs in background, ceremonial atmosphere",
                "text": f"الملك أدى لكل أطفال المدينة بذور وقال: اللي هيزرع أجمل وردة هيكون هو البطل. {self.child_name} أخد البذرة وزرعها وسقاها كل يوم."
            },
            {
                "page": 2,
                "scene_action": "sitting sadly looking at empty flower pot with only soil, while other children nearby have huge beautiful colorful flowers",
                "emotion": "sad and disappointed, looking down at empty pot, trying to understand why nothing grew, gentle sadness",
                "setting": "garden area with other children showing off their flowers",
                "additional": "toddler holding empty pot with just brown soil, other children in background with enormous gorgeous flowers (roses, lilies, sunflowers) in their pots looking proud, toddler feeling alone and confused but still watering the empty pot with small watering can",
                "text": "كل الأطفال ورداتهم طلعت أوي تجنن، لكن إناء بطلنا فضل فاضي. بطلنا كان حزين بس فضل يسقيها."
            },
            {
                "page": 3,
                "scene_action": "standing nervously in grand palace hall, holding only the empty pot with soil, surrounded by children with beautiful flowers, looking brave despite being scared",
                "emotion": "nervous but determined, biting lip, eyes showing worry but also courage, standing straight despite fear",
                "setting": "magnificent palace throne room with high ceilings, grand architecture, emperor's throne in distance",
                "additional": "small toddler in large palace hall looking tiny, holding empty pot bravely, all other children around holding gorgeous flowers looking confident, wise emperor on throne in background watching, moment of vulnerability and courage",
                "text": "جه يوم المسابقة، كل الأطفال معاهم ورد، وبطلنا راح بالإناء الفاضي وهو خايف بس قال: لازم أقول الحقيقة."
            },
            {
                "page": 4,
                "scene_action": "talking directly to the emperor, pointing to the empty pot, speaking with brave honest voice, standing tall",
                "emotion": "brave and truthful, clear honest eyes, speaking with courage, standing proud despite having no flower",
                "setting": "close view in palace throne room, emperor leaning forward listening",
                "additional": "toddler looking up at kind elderly emperor, pointing to empty pot with small finger, speaking honestly, emperor listening carefully with gentle smile, other children watching in background with confusion, moment of honest confession",
                "text": f"الملك سأل {self.child_name}: فين وردتك؟ بطلنا رد بشجاعة: أنا زرعتها وسقيتها بس م طلعتش، أنا آسف."
            },
            {
                "page": 5,
                "scene_action": "emperor laughing kindly and placing a beautiful golden crown on toddler's head, celebration happening around",
                "emotion": "shocked surprise turning to joy, mouth open in amazement, eyes wide with happy disbelief, pure delight",
                "setting": "palace throne room, celebration atmosphere, colorful banners and decorations",
                "additional": "wise emperor smiling and placing ornate golden crown on toddler's head, toddler looking up in amazed joy, other children looking shocked and surprised (some with guilty faces), celebration confetti and sparkles, grand reveal moment, emperor's wisdom shining through",
                "text": "الملك ضحك وقال: إنت البطل! لأن البذور كانت مطبوخة ومستحيل تطلع ورد، والكل كذب إلا إنت!"
            }
        ]


def create_full_prompt(scene_data: dict, character_desc: str, style: str) -> str:
    """Combine all elements into complete prompt"""
    return f"""{style}

MAIN CHARACTER:
{character_desc}
Character's expression: {scene_data['emotion']}
Character's pose/action: {scene_data['scene_action']}

SCENE SETTING:
{scene_data['setting']}

ADDITIONAL ELEMENTS:
{scene_data['additional']}

COMPOSITION:
- Simple clean layout with main focus on the character
- Character positioned for visual interest and story flow
- Soft gradient background fading to white at edges
- Gentle natural lighting creating soft shadows
- Warm inviting atmosphere safe for young children
- Leave space at top or bottom for Arabic text overlay

TECHNICAL DETAILS:
- Square format (1024x1024)
- Clean white borders/margins
- Professional children's book illustration quality
- Consistent character appearance matching the description exactly
- Soft watercolor textures throughout
- No harsh lines or scary elements
- Age-appropriate and emotionally safe content
"""


def export_honesty_stories(child_name: str = "لانا"):
    """Export all honesty story prompts"""
    generator = HonestyStoriesGenerator(child_name)
    
    all_stories = {
        "spilled_water": {
            "title": "The Spilled Water",
            "age": "1-2 years",
            "theme": "Simple truth-telling",
            "pages": []
        },
        "garden_ball": {
            "title": "The Garden Ball",
            "age": "2-3 years",
            "theme": "Taking responsibility",
            "pages": []
        },
        "broken_vase": {
            "title": "The Broken Vase",
            "age": "3-4 years",
            "theme": "Honesty when scared",
            "pages": []
        },
        "emperor_seeds": {
            "title": "The Emperor's Seeds",
            "age": "4-5 years",
            "theme": "Truth vs. peer pressure",
            "pages": []
        }
    }
    
    stories_map = {
        "spilled_water": generator.story_1_spilled_water(),
        "garden_ball": generator.story_2_garden_ball(),
        "broken_vase": generator.story_3_broken_vase(),
        "emperor_seeds": generator.story_4_emperor_seeds()
    }
    
    for story_key, pages_data in stories_map.items():
        for i, page_data in enumerate(pages_data, 1):
            full_prompt = create_full_prompt(page_data, CHARACTER_DESC, WATERCOLOR_STYLE)
            
            all_stories[story_key]["pages"].append({
                "page_number": i,
                "arabic_text": page_data["text"],
                "full_prompt": full_prompt,
                "scene_summary": page_data["scene_action"]
            })
    
    with open("honesty_stories_prompts.json", 'w', encoding='utf-8') as f:
        json.dump(all_stories, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Exported honesty stories for {child_name}")
    return all_stories


if __name__ == "__main__":
    export_honesty_stories("لانا")
