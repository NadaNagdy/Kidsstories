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
# تم حذف transform_photo_to_character من السطر التالي لأنه لم يعد موجوداً
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
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VODAFONE_CASH_NUMBER = os.getenv("VODAFONE_CASH_NUMBER")
INSTAPAY_HANDLE = os.getenv("INSTAPAY_HANDLE", "01060746538")

logger.info("=" * 60)
logger.info("🚀 KIDS STORY BOT v6.2 - FIX IMPORTERROR 🚀")
logger.info("=" * 60)

user_state = {}

@app.get("/")
def home():
    return {"status": "Kids Story Bot is running!"}

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
    if "quick_reply" in message:
        payload = message["quick_reply"]["payload"]
        current_step = user_state.get(sender_id, {}).get("step")
        if current_step == "waiting_for_age":
            handle_age_selection(sender_id, payload)
        elif current_step == "waiting_for_value":
            handle_value_selection(sender_id, payload, background_tasks)
        elif current_step == "waiting_for_payment":
            if payload in ["PAY_25_EGP", "تم الدفع", "تم التحويل ✅"]:
                handle_payment_success(sender_id, background_tasks)
        return

    if "attachments" in message:
        for attachment in message["attachments"]:
            if attachment["type"] == "image":
                image_url = attachment["payload"]["url"]
                handle_image_reception(sender_id, image_url, background_tasks)
                return

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
    user_state[sender_id]["step"] = "waiting_for_photo"
    send_text_message(sender_id, f"تشرفنا يا {text}! 😊")
    send_text_message(sender_id, "📸 أرسلي الآن صورة واضحة لوجه بطلنا الصغير لنحولها لشخصية في القصة.")

def download_image_as_base64(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode("utf-8")
        return None
    except Exception as e:
        logger.error(f"Download Error: {e}")
        return None

def handle_image_reception(sender_id, image_url, background_tasks):
    current_step = user_state.get(sender_id, {}).get("step")
    if current_step == "waiting_for_payment":
        send_text_message(sender_id, "🔍 جاري التحقق من صورة التحويل...")
        background_tasks.add_task(process_payment_verification, sender_id, image_url)
    else:
        user_state[sender_id]["photo_url"] = image_url
        send_text_message(sender_id, "🎨 جاري تحليل ملامح البطل الصغير... لحظات!")
        background_tasks.add_task(process_image_ai, sender_id, image_url)

def process_image_ai(sender_id, image_url):
    try:
        base64_image = download_image_as_base64(image_url)
        if base64_image:
            # استخدام create_character_reference بدلاً من transform_photo_to_character
            char_desc = create_character_reference(base64_image, is_url=False)
            if char_desc:
                user_state[sender_id]["char_desc"] = char_desc
                user_state[sender_id]["step"] = "waiting_for_age"
                send_quick_replies(sender_id, "تم استلام الصورة بنجاح! ✨ كم عمر طفلك؟", ["1-2", "2-3", "3-4", "4-5"])
            else:
                send_text_message(sender_id, "عذراً، لم نتمكن من معالجة الصورة.")
    except Exception as e:
        logger.error(f"Image AI Error: {e}")
        send_text_message(sender_id, "حدث خطأ فني في تحليل الصورة.")

def handle_age_selection(sender_id, age_group):
    user_state[sender_id]["step"] = "waiting_for_value"
    user_state[sender_id]["age_group"] = age_group
    send_quick_replies(sender_id, f"ما هي القيمة التي تودين أن تكون القصة عنها؟", ["الصدق", "التعاون", "الاحترام", "الشجاعة"])

def handle_value_selection(sender_id, value, background_tasks):
    send_text_message(sender_id, f"📖 جاري تحضير غلاف قصة {value}... لحظات!")
    background_tasks.add_task(process_story_generation, sender_id, value, is_preview=True)

def handle_payment_success(sender_id, background_tasks):
    send_text_message(sender_id, "✅ جاري إكمال باقي صفحات القصة وتحضير الكتاب...")
    value = user_state[sender_id].get("selected_value")
    if value:
        background_tasks.add_task(process_story_generation, sender_id, value, is_preview=False)

def process_story_generation(sender_id, value, is_preview=False):
    try:
        user_state[sender_id]["selected_value"] = value
        child_name = user_state[sender_id].get("child_name", "بطلنا")
        char_desc = user_state[sender_id].get("char_desc", "A cute child character")
        age_group = user_state[sender_id].get("age_group", "2-3")
        
        value_map = {"الشجاعة": "courage.json", "الصدق": "honesty.json", "التعاون": "cooperation.json", "الاحترام": "respect.json"}
        json_filename = value_map.get(value)
        
        manager = StoryManager(child_name)
        manager.character_desc = char_desc
        pages_prompts = manager.generate_story_prompts(json_filename, age_group)
        
        if not pages_prompts:
            send_text_message(sender_id, "عذراً، القصة غير متوفرة لهذا العمر حالياً.")
            return

        cover_temp_path = f"/tmp/cover_{sender_id}.png"
        
        if not os.path.exists(cover_temp_path) or is_preview:
            cover_prompt = f"Classic children's storybook watercolor cover illustration, hero: {char_desc}. Space for title at top."
            cover_ai_url = generate_storybook_page(char_desc, cover_prompt, child_name=child_name, is_cover=True)
            if cover_ai_url:
                cover_path = create_cover_page(cover_ai_url, f"بطل {value}", child_name, cover_temp_path)
                if cover_path:
                    send_image(sender_id, cover_path)
                    time.sleep(3)

        if is_preview:
            user_state[sender_id]["step"] = "waiting_for_payment"
            target_payment = f"حساب إنستا باي: {INSTAPAY_HANDLE}"
            msg = f"💰 لإكمال قصة {child_name} الرائعة، يرجى تحويل 25 جنيه على:\n✨ {target_payment} ✨\n\nأرسلي Screenshot للتحويل هنا!"
            send_text_message(sender_id, msg)
            return

        # توليد الصفحات بعد الدفع
        generated_images = []
        for i, page_data in enumerate(pages_prompts):
            send_text_message(sender_id, f"🎨 جاري رسم الصفحة {i+1}...")
            ai_image_url = generate_storybook_page("", page_data["prompt"], child_name=child_name, is_final=(i == len(pages_prompts)-1))
            if ai_image_url:
                temp_img_path = f"/tmp/page_{sender_id}_{i}.png"
                result_path = overlay_text_on_image(ai_image_url, page_data["text"], temp_img_path)
                if result_path:
                    generated_images.append(temp_img_path)
        
        if os.path.exists(cover_temp_path):
            generated_images.insert(0, cover_temp_path)
        
        if generated_images:
            pdf_path = f"/tmp/story_{sender_id}.pdf"
            create_pdf(generated_images, pdf_path)
            send_file(sender_id, pdf_path)
            send_text_message(sender_id, "📚 تم تجميع كتابك بنجاح! أرسل 'Start' لعمل قصة جديدة.")

    except Exception as e:
        logger.error(f"Generation Error: {e}")
        send_text_message(sender_id, "عذراً، حدث خطأ أثناء إنشاء القصة.")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
