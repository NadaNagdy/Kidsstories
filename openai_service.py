import os
import requests
import base64
import hashlib
import json
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime

# ==========================================================
# CONFIG
# ==========================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY missing")

VISION_ENDPOINT = "https://api.openai.com/v1/chat/completions"
IMAGE_ENDPOINT = "https://api.openai.com/v1/images/generations"

HEADERS = {
    "Authorization": f"Bearer {OPENAI_API_KEY}",
    "Content-Type": "application/json"
}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# ==========================================================
# DATABASE SIMULATION (replace with real DB)
# ==========================================================

CHARACTER_DB = {}
STORY_MEMORY_DB = {}

# ==========================================================
# MODELS
# ==========================================================

class StoryRequest(BaseModel):
    image_base64: str
    gender: str
    child_name: str
    age_group: str
    personality_traits: List[str]
    core_value: str
    scenes: List[str]


# ==========================================================
# CHARACTER ID
# ==========================================================

def generate_character_id(image_base64: str):
    return hashlib.sha256(image_base64.encode()).hexdigest()[:20]


# ==========================================================
# 1️⃣ VISION DNA EXTRACTOR
# ==========================================================

def extract_dna(image_base64: str, gender: str):

    prompt = f"""
Extract permanent physical DNA from this child image.

Return STRICT JSON:

{{
 "face_shape":"",
 "eye_shape":"",
 "eye_size":"",
 "eye_expression":"",
 "eyebrows":"",
 "nose":"",
 "lips":"",
 "skin_tone":"",
 "hair_color":"",
 "hair_texture":"",
 "hair_length":"",
 "unique_marks":""
}}

Only physical traits.
No personality.
Gender: {gender}
"""

    payload = {
        "model": "gpt-4o",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                }
            ]
        }],
        "max_tokens": 800
    }

    r = requests.post(VISION_ENDPOINT, headers=HEADERS, json=payload, timeout=60)
    if r.status_code != 200:
        raise Exception(r.text)

    content = r.json()["choices"][0]["message"]["content"]

    return json.loads(content)


# ==========================================================
# 2️⃣ STYLE LOCK SYSTEM
# ==========================================================

def build_style_lock():

    return """
GLOBAL STYLE LOCK:

- 3D Pixar-style soft rendering
- Soft cinematic lighting
- Warm child-friendly color palette
- Rounded shapes
- High facial consistency
- No realism
- No hyper detail
- No adult proportions
"""


# ==========================================================
# 3️⃣ OUTFIT ENGINE
# ==========================================================

def generate_default_outfit(age_group: str):

    if age_group == "1-2":
        return "soft cotton romper, pastel colors"
    if age_group == "2-3":
        return "cute overalls with colorful t-shirt"
    if age_group == "3-4":
        return "playful shorts and bright t-shirt"
    return "colorful casual kids outfit"


# ==========================================================
# 4️⃣ PERSONALITY MEMORY ENGINE
# ==========================================================

def build_personality_block(name, traits, value):

    traits_text = ", ".join(traits)

    return f"""
CHARACTER PERSONALITY MEMORY:

Name: {name}
Core traits: {traits_text}
Core value focus: {value}

Behavior must reflect these traits in posture and expression.
"""


# ==========================================================
# 5️⃣ CHARACTER LOCK BUILDER
# ==========================================================

def build_character_lock(dna, outfit, personality_block):

    dna_block = "\n".join([f"{k}: {v}" for k, v in dna.items()])

    return f"""
CHARACTER DNA LOCK (NEVER MODIFY):

{dna_block}

Outfit: {outfit}

{personality_block}

All physical traits MUST remain identical in every scene.
"""


# ==========================================================
# 6️⃣ STORY PAGE GENERATOR
# ==========================================================

def generate_page(style_lock, character_lock, scene_prompt):

    full_prompt = f"""
{style_lock}

{character_lock}

SCENE:
{scene_prompt}

Rules:
- Maintain identical facial structure
- Maintain identical skin tone
- Maintain identical eye and hair structure
- Expression must align with personality memory
"""

    payload = {
        "model": "gpt-image-1",
        "prompt": full_prompt,
        "size": "1024x1024"
    }

    r = requests.post(IMAGE_ENDPOINT, headers=HEADERS, json=payload, timeout=60)

    if r.status_code != 200:
        raise Exception(r.text)

    return r.json()["data"][0]["b64_json"]


# ==========================================================
# MAIN ENDPOINT
# ==========================================================

@app.post("/generate-premium-story")
def generate_premium_story(req: StoryRequest):

    try:

        character_id = generate_character_id(req.image_base64)

        # If character exists → reuse DNA
        if character_id in CHARACTER_DB:
            dna = CHARACTER_DB[character_id]["dna"]
        else:
            dna = extract_dna(req.image_base64, req.gender)
            CHARACTER_DB[character_id] = {
                "dna": dna,
                "created_at": str(datetime.utcnow())
            }

        style_lock = build_style_lock()

        outfit = generate_default_outfit(req.age_group)

        personality_block = build_personality_block(
            req.child_name,
            req.personality_traits,
            req.core_value
        )

        character_lock = build_character_lock(dna, outfit, personality_block)

        pages = []

        for scene in req.scenes:
            img = generate_page(style_lock, character_lock, scene)
            pages.append(img)

        STORY_MEMORY_DB[character_id] = {
            "last_story_value": req.core_value,
            "last_generated": str(datetime.utcnow())
        }

        return {
            "character_id": character_id,
            "pages_generated": len(pages),
            "pages": pages
        }

    except Exception as e:
        logger.error(str(e))
        raise HTTPException(status_code=500, detail=str(e))
