from fastapi import FastAPI, Request, BackgroundTasks
import os
import uvicorn
from messenger_api import send_text_message, send_quick_replies, send_file
from story import generate_story
from pdf_utils import create_pdf

app = FastAPI()

# Environment variables
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "my_verify_token")

# Simple in-memory state management
# sender_id -> {"step": "waiting_for_photo" | "waiting_for_value", "child_name": "...", "photo_url": "..."}
user_state = {}

@app.get("/")
def home():
    return {"status": "Kids Story Bot is running!"}

@app.get("/webhook")
def verify_webhook(request: Request):
    """
    Verifies the webhook for Facebook.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    if mode and token:
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("WEBHOOK_VERIFIED")
            return int(challenge)
        else:
            return "Verification token mismatch", 403
    return "Hello World", 200

@app.post("/webhook")
async def webhook_handler(request: Request, background_tasks: BackgroundTasks):
    """
    Handles incoming messages from Messenger.
    """
    data = await request.json()
    
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event["sender"]["id"]
                
                # Initialize state if new user
                if sender_id not in user_state:
                    # step: start -> waiting_for_photo -> waiting_for_age -> waiting_for_value -> done
                    user_state[sender_id] = {"step": "start"}

                # Handle Text Message
                if "message" in messaging_event:
                    start_processing(sender_id, messaging_event, background_tasks)
                    
    return {"status": "ok"}

def start_processing(sender_id, messaging_event, background_tasks):
    """
    Process the message logic based on state.
    """
    message = messaging_event["message"]
    
    # Check for Quick Reply
    if "quick_reply" in message:
        payload = message["quick_reply"]["payload"]
        
        # Determine if payload is Age or Value based on current state
        current_step = user_state.get(sender_id, {}).get("step")
        
        if current_step == "waiting_for_age":
            handle_age_selection(sender_id, payload)
        elif current_step == "waiting_for_value":
            handle_value_selection(sender_id, payload, background_tasks)
        return

    # Check for Attachments (Image)
    if "attachments" in message:
        for attachment in message["attachments"]:
            if attachment["type"] == "image":
                image_url = attachment["payload"]["url"]
                handle_image_reception(sender_id, image_url)
                return

    # Check for Text
    text = message.get("text", "").lower()
    
    if text == "start" or user_state.get(sender_id, {}).get("step") == "start":
        send_welcome_message(sender_id)
    else:
        # Fallback
        send_text_message(sender_id, "مرحباً! أرسل 'Start' للبدء من جديد.")

def send_welcome_message(sender_id):
    user_state[sender_id] = {"step": "waiting_for_photo"}
    send_text_message(sender_id, "👋 أهلاً بك في بوت قصص الأطفال الذكية!")
    send_text_message(sender_id, "⚠️ باستخدام البوت، أنتِ موافقة على استخدام الصورة لتوليد قصة فقط ولن يتم حفظها.")
    send_text_message(sender_id, "📸 من فضلك أرسلي صورة طفلك لكي نبدأ.")

def handle_image_reception(sender_id, image_url):
    # Update state
    user_state[sender_id]["step"] = "waiting_for_age"
    user_state[sender_id]["photo_url"] = image_url
    user_state[sender_id]["child_name"] = "بطلنا الصغير" # Placeholder
    
    # Ask for Age
    # Groups: 1-2, 2-3, 3-4, 4-5, 5-6, 6-7...
    # Messenger limits Quick Replies to 13. We have 10 groups.
    # We will send them as ranges.
    age_options = [
        "1-2", "2-3", "3-4", "4-5", "5-6", 
        "6-7", "7-8", "8-9", "9-10", "10-12"
    ]
    send_quick_replies(sender_id, "كم عمر طفلك؟ (بالسنوات)", age_options)

def handle_age_selection(sender_id, age_group):
    # Update state
    user_state[sender_id]["step"] = "waiting_for_value"
    user_state[sender_id]["age_group"] = age_group
    
    # Ask for Value
    options = ["الصدق", "التعاون", "الاحترام", "الشجاعة"]
    send_quick_replies(sender_id, f"عظيم! لعمر {age_group}، ما هي القيمة التي تودين أن تكون القصة عنها؟", options)

def handle_value_selection(sender_id, value, background_tasks):
    send_text_message(sender_id, f"📖 جاري كتابة قصة عن {value}... لحظات فقط!")
    
    # Process story generation in background
    background_tasks.add_task(process_story_generation, sender_id, value)

def process_story_generation(sender_id, value):
    child_name = user_state[sender_id].get("child_name", "بطلنا")
    age_group = user_state[sender_id].get("age_group", "4-5") # Default
    
    # 1. Generate Story
    story_text = generate_story(child_name, value, age_group)
    
    # 2. Create PDF
    pdf_path = create_pdf(child_name, value, story_text)
    
    # 3. Send PDF
    send_file(sender_id, pdf_path)
    
    # 4. Cleanup / Reset
    send_text_message(sender_id, "أتمنى أن تعجبكم القصة! 📚✨\nأرسل 'Start' لعمل قصة جديدة.")
    # Optional: cleanup file
    # os.remove(pdf_path) 
    user_state[sender_id] = {"step": "start"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
