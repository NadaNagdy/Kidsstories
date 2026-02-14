import logging
import os
import json
from dotenv import load_dotenv
load_dotenv() # Load env vars BEFORE importing services

from story_manager import StoryManager
from openai_service import create_character_reference

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Mock User State
user_state = {}
sender_id = "test_user_123"

def print_section(title):
    print(f"\n{'='*50}")
    print(f"🤖 BOT SIMULATION: {title}")
    print(f"{'='*50}")

def simulate_flow():
    # 1. Start
    print_section("STEP 1: User sends 'Start'")
    user_state[sender_id] = {"step": "waiting_for_name"}
    print(f"📥 RECEIVED: 'Start'")
    print(f"📤 BOT RESPONSE: 'What is the hero's name?'")
    
    # 2. Name
    print_section("STEP 2: User sends Name")
    child_name = "Lana"
    user_state[sender_id].update({"child_name": child_name, "step": "waiting_for_gender"})
    print(f"📥 RECEIVED: '{child_name}'")
    print(f"📤 BOT RESPONSE: 'Boy or Girl?'")

    # 3. Gender
    print_section("STEP 3: User sends Gender")
    gender = "بنت"
    user_state[sender_id].update({"gender": gender, "step": "waiting_for_photo"})
    print(f"📥 RECEIVED: '{gender}'")
    print(f"📤 BOT RESPONSE: 'Please send a photo...'")

    # 4. Image Reception & Analysis
    print_section("STEP 4: User sends Photo")
    # Using a dummy base64 string or URL to simulate
    # For simulation, we will bypass the download and just call the character ref logic directly
    # with a dummy inputs to show what valid output looks like.
    
    print(f"📥 RECEIVED: [PHOTO IMAGE DATA]")
    print(f"⚙️  PROCESSING: Analyzing image features...")

    # Calling the actual logic (without AI to save tokens/time if key missing, or with if present)
    # We will force use_ai_analysis=False to see the "Improved Default" logic in action 
    # since we don't have a real image to upload here easily.
    # OR we can try with a real logic if keys are set.

    try:
        # Simulate what process_image_ai does
        char_desc = create_character_reference(
            image_url=None, 
            gender=gender, 
            is_url=False, 
            use_ai_analysis=True, # Try True to verify API connectivity
            child_name=child_name,
            skin_tone="warm tan skin", # Simulating what main.py might pass or default
            hair_color="dark brown"
        )
        
        user_state[sender_id]["char_desc"] = char_desc
        print(f"✅ GENERATED CHARACTER DNA:\n{char_desc}")
        print(f"📤 BOT RESPONSE: 'Photo received! How old is {child_name}?'")
        
    except Exception as e:
        print(f"❌ ERROR in Analysis: {e}")
        return

    # 5. Age & Value
    print_section("STEP 5: User selects Age & Value")
    age_group = "3-4"
    value = "الصدق" # Honesty
    user_state[sender_id]["age_group"] = age_group
    user_state[sender_id]["selected_value"] = value
    
    print(f"📥 RECEIVED: Age='{age_group}', Value='{value}'")
    print(f"⚙️  PROCESSING: Generating Story Prompts...")

    # 6. Story Generation
    print_section("STEP 6: Story Manager Generation")
    
    manager = StoryManager(child_name)
    manager.inject_character_dna(user_state[sender_id]["char_desc"])
    manager.inject_personality(
        traits=[value, "curious", "brave"],
        core_value=value
    )
    
    # We need to map value to filename as in main.py
    value_map = {
        "الشجاعة": "courage.json", 
        "الصدق": "honesty.json", 
        "التعاون": "cooperation.json", 
        "الاحترام": "respect.json" 
    }
    json_filename = value_map.get(value)
    
    if json_filename:
        pages = manager.generate_story_prompts(json_filename, age_group)
        if pages:
            print(f"✅ GENERATED {len(pages)} PAGES:")
            for p in pages:
                print(f"\n--- Page {p['page']} ---")
                print(f"📜 TEXT: {p['text']}")
                print(f"🎨 PROMPT (Snippet): {p['prompt'][:150]}...")
        else:
            print("❌ Failed to generate pages.")
    else:
        print(f"❌ Unknown value: {value}")

if __name__ == "__main__":
    simulate_flow()
