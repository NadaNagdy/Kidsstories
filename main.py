from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import PlainTextResponse
import os
import uvicorn
import logging
import requests
import base64
from messenger_api import send_text_message, send_quick_replies, send_file, send_image
from story import generate_story
from pdf_utils import create_pdf
from openai_service import transform_photo_to_character, verify_payment_screenshot
from payment_service import generate_payment_link, PAYMOB_API_KEY

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Environment variables
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "my_verify_token")
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VODAFONE_CASH_NUMBER = os.getenv("VODAFONE_CASH_NUMBER")
INSTAPAY_HANDLE = os.getenv("INSTAPAY_HANDLE", "01060746538")

# Startup Banner
logger.info("=" * 60)
logger.info("🚀 KIDS STORY BOT v5.2 - COVER PNG FIX 🚀")
logger.info("=" * 60)

# Simple in-memory state management
user_state = {}

@app.get("/")
def home():
    return {"status": "Kids Story Bot is running on Railway!"}

@app.get("/webhook")
def verify_webhook(request: Request):
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
        logger.error(f"Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}

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
        send_text_message(sender_id, "📸 أرسلي الآن صورة واضحة ومباشرة لوجه بطلنا الصغير لنحولها لشخصية في القصة.")
    elif text.lower() == "start":
        send_welcome_message(sender_id)
    else:
        send_text_message(sender_id, "مرحباً! أرسل 'Start' للبدء من جديد.")

def download_image_as_base64(url):
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return base64.b64encode(response.content).decode("utf-8")
        return None
    except Exception as e:
        logger.error(f"Error downloading image: {e}")
        return None

def handle_image_reception(sender_id, image_url, background_tasks):
    current_step = user_state.get(sender_id, {}).get("step")
    if current_step == "waiting_for_payment":
        send_text_message(sender_id, "🔍 جاري التحقق من صورة التحويل... لحظات!")
        background_tasks.add_task(process_payment_verification, sender_id, image_url)
    else:
        user_state[sender_id]["step"] = "processing_ai"
        user_state[sender_id]["photo_url"] = image_url
        send_text_message(sender_id, "🎨 جاري تحويل صورتك لشخصية كرتونية رائعة... لحظات!")
        background_tasks.add_task(process_image_ai, sender_id, image_url)

def process_payment_verification(sender_id, image_url):
    try:
        base64_image = download_image_as_base64(image_url)
        if base64_image:
            if verify_payment_screenshot(base64_image, INSTAPAY_HANDLE):
                send_text_message(sender_id, "✅ تم التحقق من التحويل بنجاح! شكراً لك.")
                send_text_message(sender_id, "🚀 جاري إكمال باقي صفحات القصة وتحضير الكتاب...")
                value = user_state[sender_id].get("selected_value")
                if value:
                    process_story_generation(sender_id, value, is_preview=False)
                else:
                    send_text_message(sender_id, "عذراً، حدث خطأ. الرجاء البدء من جديد.")
            else:
                send_text_message(sender_id, "❌ لم نتمكن من العثور على رقم التحويل الصحيح. يرجى إرسال صورة واضحة للتحويل.")
        else:
            send_text_message(sender_id, "عذراً، فشل تحميل الصورة.")
    except Exception as e:
        logger.error(f"Error in process_payment_verification: {e}")
        send_text_message(sender_id, "عذراً، حدث خطأ أثناء التحقق.")

def process_image_ai(sender_id, image_url):
    try:
        base64_image = download_image_as_base64(image_url)
        if base64_image:
            ai_photo_url = transform_photo_to_character(base64_image)
            if ai_photo_url:
                user_state[sender_id]["ai_photo_url"] = ai_photo_url
                user_state[sender_id]["step"] = "waiting_for_age"
                send_quick_replies(sender_id, "تم التحويل! ✨ كم عمر طفلك؟", ["1-2", "2-3", "3-4", "4-5"])
            else:
                user_state[sender_id]["step"] = "waiting_for_photo"
                send_text_message(sender_id, "عذراً، لم نتمكن من معالجة الصورة.")
    except Exception as e:
        logger.error(f"Error in process_image_ai: {e}")
        user_state[sender_id]["step"] = "waiting_for_photo"
        send_text_message(sender_id, "عذراً، حدث خطأ فني.")

def handle_age_selection(sender_id, age_group):
    user_state[sender_id]["step"] = "waiting_for_value"
    user_state[sender_id]["age_group"] = age_group
    send_quick_replies(sender_id, f"عظيم! لعمر {age_group}، ما هي القيمة التي تودين أن تكون القصة عنها؟", ["الصدق", "التعاون", "الاحترام", "الشجاعة"])

def handle_value_selection(sender_id, value, background_tasks):
    send_text_message(sender_id, f"📖 جاري كتابة قصة عن {value}... لحظات فقط!")
    background_tasks.add_task(process_story_generation, sender_id, value, is_preview=True)

def handle_payment_success(sender_id, background_tasks):
    send_text_message(sender_id, "✅ تم استلام الدفع بنجاح! شكراً لك.")
    send_text_message(sender_id, "🚀 جاري إكمال باقي صفحات القصة وتحضير الكتاب...")
    value = user_state[sender_id].get("selected_value")
    if value:
        background_tasks.add_task(process_story_generation, sender_id, value, is_preview=False)
    else:
        send_text_message(sender_id, "عذراً، حدث خطأ. الرجاء البدء من جديد.")

import json
from image_utils import overlay_text_on_image
from openai_service import create_character_reference, generate_storybook_page

def process_story_generation(sender_id, value, is_preview=False):
    try:
        user_state[sender_id]["selected_value"] = value
        child_name = user_state[sender_id].get("child_name", "بطلنا")
        photo_url = user_state[sender_id].get("photo_url")
        age_group = user_state[sender_id].get("age_group", "2-3")
        
        base64_image = download_image_as_base64(photo_url)
        if base64_image:
            char_desc = create_character_reference(base64_image, is_url=False)
        else:
            char_desc = "A cute child character, classic children's book illustration style"
        
        try:
            config_path = f"stories_content/{value}.json"
            with open(config_path, "r", encoding="utf-8") as f:
                story_config = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load story config for {value}: {e}")
            send_text_message(sender_id, f"عذراً، قصة {value} غير متوفرة حالياً.")
            return

        story_data = story_config.get(age_group) or story_config.get("2-3")
        if not story_data:
            send_text_message(sender_id, "عذراً، القصة غير متوفرة.")
            return

        pages = story_data["pages"]
        generated_images = []
        
        # 3. Handle Cover Page (Ensure it exists and send as PNG)
        cover_temp_path = f"/tmp/cover_{sender_id}.png"
        
        if not os.path.exists(cover_temp_path) or is_preview:
            send_text_message(sender_id, "🖼️ جاري تجهيز الغلاف..." if is_preview else "🖼️ جاري تحضير الغلاف النهائي...")
            
            cover_prompt = (
                "Classic children's storybook watercolor cover illustration.\n"
                "- Show the hero child from the character description standing proudly inside a large soft circular frame in the center.\n"
                "- Keep a clean light background (white or very light pastel) with subtle watercolor texture.\n"
                "- LEAVE clear empty space at the TOP for the Arabic title 'بطل الشجاعة' (or similar) – do NOT draw complex details there.\n"
                "- LEAVE clear empty space at the BOTTOM for the child's name in Arabic – do NOT overcrowd this area.\n"
                "- Add a subtle hand-drawn border/frame around the whole cover for a classic storybook look.\n"
                "- Mood: warm, premium, heartwarming, suitable for ages 1–5."
            )
            try:
                cover_ai_url = generate_storybook_page(
                    char_desc,
                    cover_prompt,
                    child_name=child_name,
                    is_cover=True,
                )
                if cover_ai_url:
                    from image_utils import create_cover_page
                    cover_path = create_cover_page(cover_ai_url, f"بطل الـ{value}", child_name, cover_temp_path)
                    if cover_path:
                        send_image(sender_id, cover_path)
                    elif is_preview: 
                        send_text_message(sender_id, cover_ai_url)
            except Exception as e:
                logger.error(f"Cover Error: {e}")
        else:
            if not is_preview:
                send_image(sender_id, cover_temp_path)

        if is_preview:
            user_state[sender_id]["step"] = "waiting_for_payment"
            if PAYMOB_API_KEY:
                user_info = {"first_name": "User", "last_name": sender_id, "phone_number": "+201000000000", "email": "user@test.com"}
                payment_url = generate_payment_link(25, user_info)
                if payment_url:
                    send_text_message(sender_id, f"🔒 لإكمال القصة، يرجى الدفع عبر الرابط التالي:\n{payment_url}")
                    send_quick_replies(sender_id, "بعد الدفع، اضغط هنا:", ["تم الدفع"])
                else:
                    send_quick_replies(sender_id, "خطأ في الدفع.", ["PAY_25_EGP"])
            else:
                target_payment = f"حساب إنستا باي: {INSTAPAY_HANDLE}" if INSTAPAY_HANDLE else "رقم محفظة: 010XXXXXXXX"
                msg = (f"💰 الدفع عبر إنستا باي (InstaPay):\n\nلإكمال القصة، يرجى تحويل مبلغ 25 جنيه على:\n✨ {target_payment} ✨\n\nبعد التحويل، أرسلي Screenshot هنا! 👇")
                send_text_message(sender_id, msg)
            return

        else:
            send_text_message(sender_id, "📚 جاري إكمال باقي صفحات القصة...")
            for i, page in enumerate(pages):
                send_text_message(sender_id, f"🎨 جاري رسم الصفحة {i+1} من {len(pages)}...")
                # Treat the very last page in the JSON as the FINAL reward / tips page
                is_final_page = i == len(pages) - 1
                ai_image_url = generate_storybook_page(
                    char_desc,
                    page["prompt"],
                    child_name=child_name,
                    is_final=is_final_page,
                )
                if ai_image_url:
                    page_text = page["text"].replace("{child_name}", child_name)
                    temp_img_path = f"/tmp/page_{sender_id}_{i}.png"
                    result_path = overlay_text_on_image(ai_image_url, page_text, temp_img_path)
                    if result_path:
                        generated_images.append(temp_img_path)
            
            # Add cover to final PDF
            if os.path.exists(cover_temp_path):
                generated_images.insert(0, cover_temp_path)
            
            # Deduplicate
            seen = set()
            generated_images = [x for x in generated_images if not (x in seen or seen.add(x))]
            
            if generated_images:
                send_text_message(sender_id, "📚 جاري تجميع الصفحات...")
                pdf_path = f"/tmp/story_{sender_id}.pdf"
                create_pdf(generated_images, pdf_path)
                send_file(sender_id, pdf_path)
                send_text_message(sender_id, f"أتمنى أن تعجبكم قصة {value}! 📚✨\nأرسل 'Start' لعمل قصة جديدة.")
                user_state[sender_id] = {"step": "start"}
            else:
                send_text_message(sender_id, "عذراً، حدث خطأ في إنشاء الصفحات.")

    except Exception as e:
        logger.error(f"Error in process_story_generation: {e}")
        send_text_message(sender_id, "عذراً، حدث خطأ غير متوقع.")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
