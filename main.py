from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import PlainTextResponse
import os, uvicorn, logging, requests, base64, time
from messenger_api import send_text_message, send_quick_replies, send_file, send_image
from pdf_utils import create_pdf
from openai_service import verify_payment_screenshot, generate_storybook_page, create_character_reference
from image_utils import overlay_text_on_image, create_cover_page
from story_manager import StoryManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "my_verify_token")
PAYMENT_NUMBER = os.getenv("INSTAPAY_HANDLE", "01060746538")
user_state = {}

@app.post("/webhook")
async def webhook_handler(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for messaging_event in entry.get("messaging", []):
                sender_id = messaging_event["sender"]["id"]
                if sender_id not in user_state: user_state[sender_id] = {"step": "start"}
                if "message" in messaging_event:
                    start_processing(sender_id, messaging_event, background_tasks)
    return {"status": "ok"}

def start_processing(sender_id, messaging_event, background_tasks):
    message = messaging_event["message"]
    if "quick_reply" in message:
        payload = message["quick_reply"]["payload"]
        step = user_state[sender_id].get("step")
        if step == "waiting_for_gender":
            user_state[sender_id].update({"gender": payload, "step": "waiting_for_photo"})
            suffix = "بطلتنا الجميلة" if payload == "بنت" else "بطلنا الصغير"
            send_text_message(sender_id, f"عظيم! 📸 أرسلي الآن صورة واضحة لوجه {suffix} لنحولها لشخصية في القصة.")
        elif step == "waiting_for_age": handle_age_selection(sender_id, payload)
        elif step == "waiting_for_value": handle_value_selection(sender_id, payload, background_tasks)
        elif step == "waiting_for_payment": send_text_message(sender_id, "بانتظار صورة التحويل (Screenshot) للتأكيد... 📸")
        return

    if "attachments" in message:
        for att in message["attachments"]:
            if att["type"] == "image":
                handle_image_reception(sender_id, att["payload"]["url"], background_tasks)
                return

    text = message.get("text", "")
    if text.lower() == "start":
        user_state[sender_id] = {"step": "waiting_for_name"}
        send_text_message(sender_id, "👋 أهلاً بك! ما اسم بطل القصة أو بطلتنا الصغيرة؟")
    elif user_state[sender_id].get("step") == "waiting_for_name":
        user_state[sender_id].update({"child_name": text, "step": "waiting_for_gender"})
        send_quick_replies(sender_id, f"تشرفنا يا {text}! 😊 هل البطل ولد أم بنت؟", ["ولد", "بنت"])

def handle_image_reception(sender_id, url, background_tasks):
    step = user_state[sender_id].get("step")
    if step == "waiting_for_payment":
        send_text_message(sender_id, "🔍 جاري التحقق من التحويل...")
        background_tasks.add_task(process_payment_verification, sender_id, url)
    else:
        user_state[sender_id]["photo_url"] = url
        send_text_message(sender_id, "🎨 جاري تحليل الملامح...")
        background_tasks.add_task(process_image_ai, sender_id, url)

def process_image_ai(sender_id, url):
    gender = user_state[sender_id].get("gender", "ولد")
    char_desc = create_character_reference(url, gender=gender, is_url=True)
    if char_desc:
        user_state[sender_id].update({"char_desc": char_desc, "step": "waiting_for_age"})
        send_quick_replies(sender_id, "تم استلام الصورة! ✨ كم عمر طفلك؟", ["1-2", "2-3", "3-4", "4-5"])

def process_story_generation(sender_id, value, is_preview=False):
    try:
        data = user_state[sender_id]
        prefix = "بطلة" if data.get("gender") == "بنت" else "بطل"
        display_title = f"{prefix} {value}"
        
        if is_preview:
            cover_url = generate_storybook_page(data["char_desc"], f"Cover for {value}", is_cover=True)
            path = f"/tmp/c_{sender_id}.png"
            if create_cover_page(cover_url, display_title, data["child_name"], path):
                send_image(sender_id, path)
                msg = (f"💰 لإكمال القصة، يرجى تحويل 25 جنيه عبر:\n"
                       f"1️⃣ انستا باي: {PAYMENT_NUMBER}\n2️⃣ فودافون كاش: {PAYMENT_NUMBER}\n"
                       f"📸 أرسلي صورة التحويل هنا!")
                user_state[sender_id]["step"] = "waiting_for_payment"
                send_text_message(sender_id, msg)
            return
        # كود توليد الصفحات الكاملة (PDF) يتبع هنا...
    except Exception as e: logger.error(f"Gen Error: {e}")
