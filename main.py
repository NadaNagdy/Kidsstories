from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import PlainTextResponse
import os
import uvicorn
import logging
import requests
import base64
import json
import time

from messenger_api import send_text_message, send_quick_replies, send_file, send_image
from pdf_utils import create_pdf
from openai_service import verify_payment_screenshot, generate_storybook_page, create_character_reference
from payment_service import generate_payment_link, PAYMOB_API_KEY
from image_utils import overlay_text_on_image, create_cover_page
from story_manager import StoryManager

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# متغيرات البيئة
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "my_verify_token")
INSTAPAY_HANDLE = os.getenv("INSTAPAY_HANDLE", "01060746538")

logger.info("=" * 60)
logger.info("🚀 KIDS STORY BOT v6.4 - GENDER SELECTION ADDED 🚀")
logger.info("=" * 60)

user_state = {}

@app.get("/")
def home():
    return {"status": "Running"}

@app.get("/webhook")
def verify_webhook(request: Request):
    params = request.query_params
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == VERIFY_TOKEN:
        return PlainTextResponse(content=params.get("hub.challenge"), status_code=200)
    raise HTTPException(status_code=403, detail="Mismatch")

@app.post("/webhook")
async def webhook_handler(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        if data.get("object") == "page":
            for entry in data.get("entry", []):
                for messaging_event in entry.get("messaging", []):
                    sender_id = messaging_event["sender"]["id"]
                    if sender_id not in user_state:
                        user_state[sender_id] = {"step": "start"}
                    if "message" in messaging_event:
                        start_processing(sender_id, messaging_event, background_tasks)
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook Error: {e}")
        return {"status": "error"}

def start_processing(sender_id, messaging_event, background_tasks):
    message = messaging_event["message"]
    
    # معالجة الردود السريعة (Quick Replies)
    if "quick_reply" in message:
        payload = message["quick_reply"]["payload"]
        current_step = user_state.get(sender_id, {}).get("step")
        
        # --- خطوة جديدة: معالجة اختيار الجنس ---
        if current_step == "waiting_for_gender":
            user_state[sender_id]["gender"] = payload # "ولد" أو "بنت"
            user_state[sender_id]["step"] = "waiting_for_photo"
            suffix = "بطلتنا الجميلة" if payload == "بنت" else "بطلنا الصغير"
            send_text_message(sender_id, f"عظيم! 📸 أرسلي الآن صورة واضحة لوجه {suffix} لنحولها لشخصية في القصة.")
        
        elif current_step == "waiting_for_age":
            handle_age_selection(sender_id, payload)
        elif current_step == "waiting_for_value":
            handle_value_selection(sender_id, payload, background_tasks)
        elif current_step == "waiting_for_payment":
            if payload in ["PAY_25_EGP", "تم الدفع", "تم التحويل ✅"]:
                send_text_message(sender_id, "بانتظار صورة التحويل (Screenshot) للتأكيد... 📸")
        return

    # معالجة الصور
    if "attachments" in message:
        for attachment in message["attachments"]:
            if attachment["type"] == "image":
                image_url = attachment["payload"]["url"]
                handle_image_reception(sender_id, image_url, background_tasks)
                return

    # معالجة النصوص
    text = message.get("text", "")
    if text:
        if text.lower() == "start":
            send_welcome_message(sender_id)
        elif user_state[sender_id].get("step") == "waiting_for_name":
            handle_text_reception(sender_id, text)

def send_welcome_message(sender_id):
    user_state[sender_id] = {"step": "waiting_for_name"}
    send_text_message(sender_id, "👋 أهلاً بك في بوت قصص الأطفال الذكية!")
    send_text_message(sender_id, "ما اسم بطل القصة أو بطلتنا الصغيرة؟")

def handle_text_reception(sender_id, text):
    user_state[sender_id]["child_name"] = text
    # --- التعديل هنا: الانتقال لخطوة الجنس بدلاً من الصورة ---
    user_state[sender_id]["step"] = "waiting_for_gender"
    send_quick_replies(sender_id, f"تشرفنا يا {text}! 😊 هل البطل الصغير ولد أم بنت؟", ["ولد", "بنت"])

def download_image_as_base64(url):
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode("utf-8")
        return None
    except Exception as e:
        logger.error(f"Download Error: {e}")
        return None

def handle_image_reception(sender_id, image_url, background_tasks):
    current_step = user_state.get(sender_id, {}).get("step")
    if current_step == "waiting_for_payment":
        send_text_message(sender_id, "🔍 جاري التحقق من صورة التحويل... لحظات!")
        background_tasks.add_task(process_payment_verification, sender_id, image_url)
    else:
        user_state[sender_id]["photo_url"] = image_url
        send_text_message(sender_id, "🎨 جاري تحليل ملامح البطل الصغير...")
        background_tasks.add_task(process_image_ai, sender_id, image_url)

def process_payment_verification(sender_id, image_url):
    try:
        base64_image = download_image_as_base64(image_url)
        if base64_image:
            is_valid = verify_payment_screenshot(base64_image, INSTAPAY_HANDLE)
            if is_valid:
                send_text_message(sender_id, "✅ تم التحقق من الدفع! جاري إكمال الكتاب...")
                value = user_state[sender_id].get("selected_value")
                process_story_generation(sender_id, value, is_preview=False)
            else:
                send_text_message(sender_id, "❌ لم نتمكن من التأكد من بيانات التحويل. يرجى إرسال صورة واضحة.")
    except Exception as e:
        logger.error(f"Verification Error: {e}")

def process_image_ai(sender_id, image_url):
    try:
        base64_image = download_image_as_base64(image_url)
        if base64_image:
            char_desc = create_character_reference(base64_image, is_url=False)
            if char_desc:
                user_state[sender_id]["char_desc"] = char_desc
                user_state[sender_id]["step"] = "waiting_for_age"
                send_quick_replies(sender_id, "تم استلام الصورة! ✨ كم عمر طفلك؟", ["1-2", "2-3", "3-4", "4-5"])
    except Exception as e:
        logger.error(f"AI Error: {e}")

def handle_age_selection(sender_id, age_group):
    user_state[sender_id]["step"] = "waiting_for_value"
    user_state[sender_id]["age_group"] = age_group
    send_quick_replies(sender_id, f"لعمر {age_group}، ما هي القيمة التي تودينها؟", ["الصدق", "التعاون", "الاحترام", "الشجاعة"])

def handle_value_selection(sender_id, value, background_tasks):
    user_state[sender_id]["selected_value"] = value
    send_text_message(sender_id, f"📖 جاري تجهيز الغلاف... لحظات!")
    background_tasks.add_task(process_story_generation, sender_id, value, is_preview=True)

def process_story_generation(sender_id, value, is_preview=False):
    try:
        child_name = user_state[sender_id].get("child_name", "بطلنا")
        char_desc = user_state[sender_id].get("char_desc", "A child")
        age_group = user_state[sender_id].get("age_group", "2-3")
        gender = user_state[sender_id].get("gender", "ولد") # جلب الجنس
        
        # --- تحديد العنوان بناءً على الجنس ---
        prefix = "بطلة" if gender == "بنت" else "بطل"
        display_title = f"{prefix} {value}"

        value_map = {"الشجاعة": "courage.json", "الصدق": "honesty.json", "التعاون": "cooperation.json", "الاحترام": "respect.json"}
        json_filename = value_map.get(value)
        
        manager = StoryManager(child_name)
        manager.character_desc = char_desc
        pages_prompts = manager.generate_story_prompts(json_filename, age_group)

        cover_temp_path = f"/tmp/cover_{sender_id}.png"
        
        # توليد الغلاف
        if is_preview:
            cover_ai_url = generate_storybook_page(char_desc, f"Watercolor cover, {value}", child_name=child_name, is_cover=True)
            if cover_ai_url:
                # استخدام display_title (بطل/بطلة) هنا
                create_cover_page(cover_ai_url, display_title, child_name, cover_temp_path)
                send_image(sender_id, cover_temp_path)
                time.sleep(2)
                
                user_state[sender_id]["step"] = "waiting_for_payment"
                msg = f"💰 لإكمال القصة، يرجى تحويل 25 جنيه على إنستا باي:\n✨ {INSTAPAY_HANDLE} ✨\nثم أرسلي الصورة هنا!"
                send_text_message(sender_id, msg)
                return

        # توليد الصفحات الكاملة
        generated_images = []
        if os.path.exists(cover_temp_path): generated_images.append(cover_temp_path)

        for i, p in enumerate(pages_prompts):
            send_text_message(sender_id, f"🎨 رسم الصفحة {i+1}...")
            img_url = generate_storybook_page("", p["prompt"], child_name=child_name)
            if img_url:
                path = f"/tmp/p_{sender_id}_{i}.png"
                overlay_text_on_image(img_url, p["text"], path)
                generated_images.append(path)

        if generated_images:
            pdf_path = f"/tmp/story_{sender_id}.pdf"
            create_pdf(generated_images, pdf_path)
            send_file(sender_id, pdf_path)
            user_state[sender_id] = {"step": "start"}

    except Exception as e:
        logger.error(f"Gen Error: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
