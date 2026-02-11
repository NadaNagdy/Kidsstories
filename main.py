from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import PlainTextResponse
import os
import uvicorn
import logging
import requests
import base64
from messenger_api import send_text_message, send_quick_replies, send_file
from story import generate_story
from pdf_utils import create_pdf
from openai_service import transform_photo_to_character

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Environment variables
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "my_verify_token")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")

# Startup Banner (AFTER variables are defined)
logger.info("=" * 60)
logger.info("🚀 KIDS STORY BOT v5.1 - BASE64 FIX 🚀")
logger.info("=" * 60)
logger.info(f"VERIFY_TOKEN: {VERIFY_TOKEN}")
logger.info(f"PAGE_ACCESS_TOKEN: {'SET' if PAGE_ACCESS_TOKEN else 'MISSING!!!'}")
logger.info("=" * 60)

# Simple in-memory state management
user_state = {}

@app.get("/")
def home():
    return {"status": "Kids Story Bot is running on Railway!"}

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
            logger.info("WEBHOOK_VERIFIED")
            return PlainTextResponse(content=challenge, status_code=200)
        else:
            logger.error(f"Verification mismatch. Received: {token}, Expected: {VERIFY_TOKEN}")
            raise HTTPException(status_code=403, detail="Verification token mismatch")
    return PlainTextResponse(content="Hello World", status_code=200)

@app.post("/webhook")
async def webhook_handler(request: Request, background_tasks: BackgroundTasks):
    """
    Handles incoming messages from Messenger.
    """
    try:
        data = await request.json()
        
        if data.get("object") == "page":
            for entry in data.get("entry", []):
                for messaging_event in entry.get("messaging", []):
                    sender_id = messaging_event["sender"]["id"]
                    
                    # Initialize state if new user
                    if sender_id not in user_state:
                        user_state[sender_id] = {"step": "start"}

                    # Handle Text Message
                    if "message" in messaging_event:
                        start_processing(sender_id, messaging_event, background_tasks)
                        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}

def start_processing(sender_id, messaging_event, background_tasks):
    """
    Process the message logic based on state.
    """
    message = messaging_event["message"]
    
    # Check for Quick Reply
    if "quick_reply" in message:
        payload = message["quick_reply"]["payload"]
        
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
                handle_image_reception(sender_id, image_url, background_tasks)
                return

    # Check for Text
    text = message.get("text", "")
    if text:
        handle_text_reception(sender_id, text)

def send_welcome_message(sender_id):
    user_state[sender_id] = {"step": "waiting_for_name"}
    send_text_message(sender_id, "👋 أهلاً بك في بوت قصص الأطفال الذكية!")
    send_text_message(sender_id, "ما اسم بطل القصة أو بطلتنا الصغيرة؟")

def handle_text_reception(sender_id, text):
    current_step = user_state[sender_id].get("step")
    
    if current_step == "waiting_for_name":
        user_state[sender_id]["child_name"] = text
        user_state[sender_id]["step"] = "waiting_for_photo"
        send_text_message(sender_id, f"تشرفنا يا {text}! 😊")
        send_text_message(sender_id, "📸 أرسلي الآن صورة واضحة ومباشرة لوجه بطلنا الصغير لنحولها لشخصية في القصة. (نحن نحترم خصوصيتكم: الصور لا تُحفظ ويتم استخدامها فقط لإنشاء شخصية القصة).")
    elif text.lower() == "start":
        send_welcome_message(sender_id)
    else:
        send_text_message(sender_id, "مرحباً! أرسل 'Start' للبدء من جديد.")

def download_image_as_base64(url):
    """
    Downloads an image from a URL and returns it as a base64 encoded string.
    """
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            logger.info(f"Successfully downloaded and encoded image from {url[:50]}...")
            return base64.b64encode(response.content).decode("utf-8")
        else:
            logger.error(f"Failed to download image from {url}. Status: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error downloading image: {e}")
        return None

def handle_image_reception(sender_id, image_url, background_tasks):
    user_state[sender_id]["step"] = "processing_ai"
    user_state[sender_id]["photo_url"] = image_url
    
    send_text_message(sender_id, "🎨 جاري تحويل صورتك لشخصية كرتونية رائعة... لحظات!")
    
    # Move heavy processing to background to prevent Messenger timeout
    background_tasks.add_task(process_image_ai, sender_id, image_url)

def process_image_ai(sender_id, image_url):
    try:
        # Download image and convert to base64
        base64_image = download_image_as_base64(image_url)
        
        if base64_image:
            ai_photo_url = transform_photo_to_character(base64_image)
        else:
            ai_photo_url = None
        
        if ai_photo_url:
            user_state[sender_id]["ai_photo_url"] = ai_photo_url
            user_state[sender_id]["step"] = "waiting_for_age"
            age_options = ["1-2", "2-3", "3-4", "4-5"]
            send_quick_replies(sender_id, "تم التحويل! ✨ كم عمر طفلك؟", age_options)
        else:
            user_state[sender_id]["step"] = "waiting_for_photo"
            send_text_message(sender_id, "عذراً، لم نتمكن من معالجة الصورة. يرجى محاولة إرسال صورة أخرى واضحة ومباشرة للوجه. (تنبيه: الصور لا تُحفظ لضمان خصوصيتكم).")
    except Exception as e:
        logger.error(f"Error in process_image_ai: {e}")
        user_state[sender_id]["step"] = "waiting_for_photo"
        send_text_message(sender_id, "عذراً، حدث خطأ فني أثناء معالجة الصورة. يرجى المحاولة مرة أخرى.")

def handle_age_selection(sender_id, age_group):
    user_state[sender_id]["step"] = "waiting_for_value"
    user_state[sender_id]["age_group"] = age_group
    
    options = ["الصدق", "التعاون", "الاحترام", "الشجاعة"]
    send_quick_replies(sender_id, f"عظيم! لعمر {age_group}، ما هي القيمة التي تودين أن تكون القصة عنها؟", options)

def handle_value_selection(sender_id, value, background_tasks):
    send_text_message(sender_id, f"📖 جاري كتابة قصة عن {value}... لحظات فقط!")
    background_tasks.add_task(process_story_generation, sender_id, value)

import json
from image_utils import overlay_text_on_image
from openai_service import create_character_reference, generate_storybook_page

def process_story_generation(sender_id, value):
    try:
        child_name = user_state[sender_id].get("child_name", "بطلنا")
        photo_url = user_state[sender_id].get("photo_url")
        age_group = user_state[sender_id].get("age_group", "2-3")
        
        # 1. Create a consistent character description from the photo
        send_text_message(sender_id, "🔍 جاري تحليل ملامح بطلنا الصغير لضمان ظهور الشخصية بشكل متناسق في كل الصفحات...")
        
        # Download image and convert to base64 for vision processing
        base64_image = download_image_as_base64(photo_url)
        if base64_image:
            char_desc = create_character_reference(base64_image, is_url=False)
        else:
            char_desc = "A cute child character, Pixar style"
        
        # 2. Load story config from category-specific file
        try:
            config_path = f"stories_content/{value}.json"
            with open(config_path, "r", encoding="utf-8") as f:
                story_config = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load story config for {value}: {e}")
            send_text_message(sender_id, f"عذراً، قصة {value} غير متوفرة حالياً.")
            return

        story_data = story_config.get(age_group)
        if not story_data:
            # Fallback to 2-3 if age not found
            story_data = story_config.get("2-3")
            
        if not story_data:
            send_text_message(sender_id, "عذراً، هذه القصة غير متوفرة لهذا العمر.")
            return

        pages = story_data["pages"]
        generated_images = []
        
        # 3. Generate pages in a loop
        for i, page in enumerate(pages):
            send_text_message(sender_id, f"🎨 جاري رسم الصفحة {i+1} من {len(pages)}...")
            
            # Generate Background + Character
            ai_image_url = generate_storybook_page(char_desc, page["prompt"])
            
            if ai_image_url:
                # Overlay Text
                page_text = page["text"].format(child_name=child_name)
                temp_img_path = f"/tmp/page_{sender_id}_{i}.png"
                result_path = overlay_text_on_image(ai_image_url, page_text, temp_img_path)
                
                if result_path:
                    generated_images.append(temp_img_path)
                else:
                    logger.error(f"Failed to overlay text for page {i+1}")
            else:
                logger.error(f"Failed to generate image for page {i+1}")
        
        if not generated_images:
            send_text_message(sender_id, "عذراً، حدث خطأ أثناء إنشاء صفحات القصة.")
            return

        # 4. Create PDF from images
        send_text_message(sender_id, "📚 جاري تجميع الصفحات في الكتاب النهائي...")
        pdf_name = f"story_{sender_id}.pdf"
        pdf_path = f"/tmp/{pdf_name}"
        create_pdf(generated_images, pdf_path)
        
        # 5. Send PDF
        send_file(sender_id, pdf_path)
        
        # 6. Cleanup
        send_text_message(sender_id, f"أتمنى أن تعجبكم قصة {value}! 📚✨\nأرسل 'Start' لعمل قصة جديدة.")
        user_state[sender_id] = {"step": "start"}
        
        # Optional: Remove temp files
        for img_path in generated_images:
            try: os.remove(img_path)
            except: pass
        try: os.remove(pdf_path)
        except: pass

    except Exception as e:
        logger.error(f"Error in process_story_generation: {e}")
        send_text_message(sender_id, "عذراً، حدث خطأ غير متوقع. جاري العمل على إصلاحه!")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
