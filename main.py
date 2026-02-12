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
        elif current_step == "waiting_for_payment":
            if payload == "PAY_25_EGP" or payload == "تم التحويل ✅" or payload == "تم الدفع" or "InstaPay" in payload:
                handle_payment_success(sender_id, background_tasks)
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
            is_valid = verify_payment_screenshot(base64_image, INSTAPAY_HANDLE)
            if is_valid:
                # Proceed to full story generation
                from main import handle_payment_success # Local import to avoid circular dependency if any
                import asyncio
                # Since we are in a thread/process from background_tasks, we can just call it
                # But handle_payment_success expects background_tasks? 
                # Let's refactor handle_payment_success or call it directly.
                # Actually, I'll just trigger the story generation here.
                send_text_message(sender_id, "✅ تم التحقق من التحويل بنجاح! شكراً لك.")
                send_text_message(sender_id, "🚀 جاري إكمال باقي صفحات القصة وتحضير الكتاب...")
                
                value = user_state[sender_id].get("selected_value")
                if value:
                    # We need a new background task or just run it?
                    # Since we are already in a background task, we can call it.
                    process_story_generation(sender_id, value, is_preview=False)
                else:
                    send_text_message(sender_id, "عذراً، حدث خطأ. الرجاء البدء من جديد.")
            else:
                send_text_message(sender_id, "❌ لم نتمكن من العثور على رقم التحويل الصحيح في الصورة. يرجى التأكد من إرسال صورة واضحة للتحويل (Screenshot) لـلـرقم/الحساب الصحيح.")
                send_text_message(sender_id, "لو سمحت أرسلي صوره من التحويل مره اخري.. القصه بانتظارك! 😊")
        else:
            send_text_message(sender_id, "عذراً، فشل تحميل الصورة. يرجى المحاولة مرة أخرى.")
    except Exception as e:
        logger.error(f"Error in process_payment_verification: {e}")
        send_text_message(sender_id, "عذراً، حدث خطأ أثناء التحقق من الصورة.")

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
    # Start with preview mode (first page only)
    background_tasks.add_task(process_story_generation, sender_id, value, is_preview=True)

def handle_payment_success(sender_id, background_tasks):
    send_text_message(sender_id, "✅ تم استلام الدفع بنجاح! شكراً لك.")
    send_text_message(sender_id, "🚀 جاري إكمال باقي صفحات القصة وتحضير الكتاب...")
    
    # Retrieve saved state to continue
    value = user_state[sender_id].get("selected_value")
    if value:
        background_tasks.add_task(process_story_generation, sender_id, value, is_preview=False)
    else:
        send_text_message(sender_id, "عذراً، حدث خطأ. الرجاء البدء من جديد.")

def handle_payment_success(sender_id, background_tasks):
    send_text_message(sender_id, "✅ تم استلام الدفع بنجاح! شكراً لك.")
    send_text_message(sender_id, "🚀 جاري إكمال باقي صفحات القصة وتحضير الكتاب...")
    
    # Retrieve saved state to continue
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
        
        # 1. Create a consistent character description from the photo
        send_text_message(sender_id, "🔍 جاري تحليل ملامح بطلنا الصغير لضمان ظهور الشخصية بشكل متناسق في كل الصفحات...")
        
        # Download image and convert to base64 for vision processing
        base64_image = download_image_as_base64(photo_url)
        if base64_image:
            char_desc = create_character_reference(base64_image, is_url=False)
        else:
            char_desc = "A cute child character, classic children's book illustration style"
        
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
        
        generated_images = []
        
        # Determine range of pages to generate
        # Determine range of pages to generate
        if is_preview:
            # Generate Cover Only
            send_text_message(sender_id, "🖼️ جاري تجهيز معاينة الغلاف...")
            
            # Generate Cover Page
            cover_prompt = (
                f"A beautiful artistic cover illustration featuring the hero: {char_desc}. "
                f"Style: Classic children's book illustration, soft watercolor and colored pencil textures, hand-drawn look, gentle pastel color palette, clean white background. "
                f"COMPOSITION: The character is centered inside a soft, artistic circular frame. "
                f"Leave clear white space at the very top for a title and at the very bottom for a name. "
                f"The overall feel is heartwarming and nostalgic, reminiscent of professional nursery storybooks."
            )
            try:
                cover_ai_url = generate_storybook_page(char_desc, cover_prompt, child_name=child_name)
                
                if cover_ai_url:
                    from image_utils import create_cover_page
                    cover_temp_path = f"/tmp/cover_{sender_id}.png"
                    title_text = f"بطل الـ{value}"
                    cover_path = create_cover_page(cover_ai_url, title_text, child_name, cover_temp_path)
                    if cover_path:
                        generated_images.append(cover_path)
                        send_image(sender_id, cover_path)
                    else:
                        logger.error("Failed to create cover page image (create_cover_page returned None)")
                        # Fallback: Send the raw AI image
                        send_text_message(sender_id, "⚠️ لم نتمكن من إضافة النصوص، لكن إليك الغلاف:")
                        send_text_message(sender_id, cover_ai_url) # Send URL directly, Messenger renders it
                else:
                    logger.error("Failed to generate AI image for cover")
                    send_text_message(sender_id, "⚠️ حدثت مشكلة في تصميم الغلاف، سننتقل للخطوة التالية.")
            except Exception as e:
                logger.error(f"Exception during cover generation: {e}")
            
            user_state[sender_id]["step"] = "waiting_for_payment"
            
            # Check for Paymob Configuration
            if PAYMOB_API_KEY:
                # Generate Real Payment Link
                # Using dummy user info for now, in real app we'd ask for email/phone or get from FB profile
                user_info = {"first_name": "User", "last_name": sender_id, "phone_number": "+201000000000", "email": "user@test.com"}
                payment_url = generate_payment_link(25, user_info)
                
                if payment_url:
                    # Send a button with the link
                    # Messenger Button Template (Generic Template with 1 button)
                    # For now, simplistic URL message + text
                    send_text_message(sender_id, f"🔒 لإكمال القصة، يرجى الدفع عبر الرابط التالي:\n{payment_url}")
                    # Also keep the simulated button for testing convenience? Or remove it?
                    # Let's keep the simulated button as a 'Confirm Payment' step for this demo
                    send_quick_replies(sender_id, "بعد الدفع، اضغط هنا:", ["تم الدفع"])
                else:
                     send_quick_replies(sender_id, "خطأ في الاتصال بنظام الدفع. (محاكاة):", ["PAY_25_EGP"])
            else:
                 # Fallback to Manual Payment (Instapay / Vodafone Cash)
                 if INSTAPAY_HANDLE and INSTAPAY_HANDLE != "username@instapay":
                     target_payment = f"حساب إنستا باي: {INSTAPAY_HANDLE}"
                 elif VODAFONE_CASH_NUMBER:
                     target_payment = f"رقم محفظة: {VODAFONE_CASH_NUMBER}"
                 else:
                     target_payment = "رقم: 010XXXXXXXX (مثال)"

                 msg = (
                     f"💰 الدفع عبر إنستا باي (InstaPay):\n\n"
                     f"لإكمال القصة، يرجى تحويل مبلغ 25 جنيه على:\n"
                     f"✨ {target_payment} ✨\n\n"
                     f"بعد التحويل، لو سمحت أرسلي صوره من التحويل (Screenshot) هنا.. القصه بانتظارك! 👇"
                 )
                 send_text_message(sender_id, msg)
            
            return

        else:
            # Resume from page 1 (since cover is 0)
            send_text_message(sender_id, "📚 جاري إكمال القصة...")
            start_page = 0 
            end_page = len(pages)

        # 4. Generate story pages in a loop
        for i in range(start_page, end_page):
            if i >= len(pages): break
            page = pages[i]
            send_text_message(sender_id, f"🎨 جاري رسم الصفحة {i+1} من {len(pages)}...")
            
            # Generate Background + Character
            ai_image_url = generate_storybook_page(char_desc, page["prompt"], child_name=child_name)
            
            if ai_image_url:
                # Overlay Text
                page_text = page["text"].replace("{child_name}", child_name)
                temp_img_path = f"/tmp/page_{sender_id}_{i}.png"
                result_path = overlay_text_on_image(ai_image_url, page_text, temp_img_path)
                
                if result_path:
                    generated_images.append(temp_img_path)
                    
                    # If preview mode, send the image immediately
                    if is_preview:
                        send_image(sender_id, temp_img_path)
                else:
                    logger.error(f"Failed to overlay text for page {i+1}")
            else:
                logger.error(f"Failed to generate image for page {i+1}")
        
        if is_preview:
            user_state[sender_id]["step"] = "waiting_for_payment"
            # In a real app, this would be a webview button or link
            send_quick_replies(sender_id, "🔒 لإكمال القصة والحصول على الكتاب PDF، يرجى دفع رسوم رمزية (25 جنيه).", ["Pay 25 EGP"])
            return

        # If not preview, retrieve existing images (mock logic for now since tmp clears)
        # In a real app, you'd store these in S3/Cloudinary.
        # Check if page 0 exists from preview step
        page_0_path = f"/tmp/page_{sender_id}_0.png"
        if os.path.exists(page_0_path):
            generated_images.insert(0, page_0_path)
            
        # Also need to add cover if it exists (assuming it was made during preview or persistent)
        cover_path = f"/tmp/cover_{sender_id}.png"
        if os.path.exists(cover_path):
            # Check if cover is already in list (it might be added by previous cover logic if I didn't change it)
            # The previous cover logic (lines 249-262) runs every time process_story_generation is called?
            # Wait, line 249-262 is BEFORE this loop.
            # I should wrap 249-262 in `if is_preview:` or handle it carefully.
            # Actually, let's just make sure we don't duplicate.
            if cover_path not in generated_images:
                generated_images.insert(0, cover_path)
        
        if not generated_images:
            send_text_message(sender_id, "عذراً، حدث خطأ أثناء إنشاء صفحات القصة.")
            return

        # 5. Create PDF from images
        send_text_message(sender_id, "📚 جاري تجميع الصفحات في الكتاب النهائي...")
        pdf_name = f"story_{sender_id}.pdf"
        pdf_path = f"/tmp/{pdf_name}"
        create_pdf(generated_images, pdf_path)
        
        # 6. Send PDF
        send_file(sender_id, pdf_path)
        
        # 7. Cleanup
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
