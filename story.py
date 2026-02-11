def generate_story(child_name, value, age_group):
    """
    Generates a story based on child's name, moral value, and age group.
    """
    # Normalize age group string if needed, e.g., "1-2" -> "1-2"
    
    templates = {
        "1-2": {
            "style": "صور كبيرة، كلمات بسيطة، تكرار.",
            "content": """
هذا {child_name}. (صورة طفل يبتسم)
{child_name} يحب اللعب.
{child_name} يشارك اللعبة.
شكراً {child_name}!
المشاركة جميلة.
"""
        },
        "2-3": {
            "style": "روتين يومي، جمل قصيرة.",
            "content": """
استيقظ {child_name} من النوم. "صباح الخير!".
غسل {child_name} وجهه.
أكل {child_name} فطوره اللذيذ.
ذهب {child_name} ليلعب.
وجد صديقه يبكي.
قال {child_name}: "لا تبك، خذ لعبتي".
ضحك الصديق.
{child_name} سعيد.
"""
        },
        "3-4": {
            "style": "مغامرة بسيطة، أسئلة تفاعلية.",
            "content": """
كان يا ما كان، أرنب صغير اسمه {child_name}.
كان {child_name} يقفز في الحديقة.
ماذا وجد {child_name}؟ وجد جزرة كبيرة!
هل أكلها وحده؟
لا، تذكر {child_name} أصدقاءه.
نادى {child_name}: "تعالوا يا أصدقاء!".
أكل الجميع وشبعوا.
قالوا: "شكراً يا {child_name}، أنت كريم!".
"""
        },
        "4-5": {
            "style": "أحداث متسلسلة، القرار الصحيح.",
            "content": """
في يوم مشمس، كان {child_name} يلعب بالكرة.
ركل {child_name} الكرة بقوة... طرااااخ!
انكسرت زهرية ماما المفضلة.
خاف {child_name} جداً. "ماذا أفعل؟ هل أخفيها؟".
تذكر {child_name} أن {value} هو الأهم.
ذهب {child_name} إلى ماما وقال: "أنا آسف، أنا كسرت الزهرية".
ابتسمت ماما وقالت: "أنا فخورة بك لأنك قلت الصدق يا {child_name}".
"""
        },
        "default": {
             "style": "عام.",
             "content": """
كان يا ما كان، في قديم الزمان، كان هناك بطل اسمه {child_name}.
كان {child_name} يواجه تحديات كثيرة في حياته اليومية.
وفي كل مرة، كان يستخدم {value} ليتغلب على المصاعب.
لكن الدرس الأهم كان: {value} هو كنز لا يفنى.
"""
        }
    }

    story_data = templates.get(age_group, templates["default"])
    
    # If it's a dict (structured), return content formatted with actual values
    if isinstance(story_data, dict):
        return story_data["content"].format(child_name=child_name, value=value)
    return story_data.format(child_name=child_name, value=value)
