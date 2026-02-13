from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import PlainTextResponse
import os, uvicorn, logging, requests, base64, time

# استيراد الدوال من الملفات المساعدة التي قمنا بتطويرها
from messenger_api import send_text_message, send_quick_replies, send_file, send_image
from pdf_utils import create_pdf
from openai_service import verify_payment_screenshot, generate_storybook_page, create_character_reference
from image_utils import overlay_text_on_image, create_cover_page
from story_manager import StoryManager

# إعداد السجلات لمراقبة أداء البوت
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# متغيرات البيئة (تأكد من ضبطها في Railway)
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "my_verify_token")
PAYMENT_NUMBER = os.getenv("INSTAPAY_HANDLE", "01060746538")
user_state = {}

@app.get("/")
def home():
    return {"status": "Story Bot is Active"}

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
    
    # 1. معالجة الردود السريعة (Quick Replies)
    if "quick_reply" in message:
        payload = message["quick_reply"]["payload"]
        step = user_state[sender_id].get("step")
        
        if step == "waiting_for_gender":
            user_state[sender_id].update({"gender": payload, "step": "waiting_for_photo"})
            suffix = "بطلتنا الجميلة" if payload == "بنت" else "بطلنا الصغير"
            send_text_message(sender_id, f"عظيم! 📸 أرسلي الآن صورة واضحة لوجه {suffix} لنحولها لشخصية في القصة.")
        
        elif step == "waiting_for_age":
            handle_age_selection(sender_id, payload)
            
        elif step == "waiting_for_value":
            handle_value_selection(sender_id, payload, background_tasks)
            
        elif step == "waiting_for_payment":
            if payload in ["PAY_25_EGP", "تم الدفع", "تم التحويل ✅"]:
                send_text_message(sender_id, "بانتظار صورة التحويل (Screenshot) للتأكيد... 📸")
        return

    # 2. معالجة المرفقات (الصورة الشخصية أو صورة الدفع)
    if "attachments" in message:
        for att in message["attachments"]:
            if att["type"] == "image":
                handle_image_reception(sender_id, att["payload"]["url"], background_tasks)
                return

    # 3. معالجة النصوص (البداية والاسم)
    text = message.get("text", "")
    if text:
        if text.lower() == "start":
            user_state[sender_id] = {"step": "waiting_for_name"}
            send_text_message(sender_id, "👋 أهلاً بك في عالم القصص الذكية!")
            send_text_message(sender_id, "ما اسم بطل القصة أو بطلتنا الصغيرة؟")
        elif user_state[sender_id].get("step") == "waiting_for_name":
            user_state[sender_id].update({"child_name": text, "step": "waiting_for_gender"})
            send_quick_replies(sender_id, f"تشرفنا يا {text}! 😊 هل البطل ولد أم بنت؟", ["ولد", "بنت"])

# --- الدوال المساعدة لإدارة تدفق البيانات ---

def handle_image_reception(sender_id, url, background_tasks):
    step = user_state[sender_id].get("step")
    if step == "waiting_for_payment":
        send_text_message(sender_id, "🔍 جاري التحقق من التحويل... لحظات!")
        background_tasks.add_task(process_payment_verification, sender_id, url)
    else:
        user_state[sender_id]["photo_url"] = url
        send_text_message(sender_id, "🎨 جاري تحليل الملامح وبناء الشخصية بدقة...")
        background_tasks.add_task(process_image_ai, sender_id, url)

def process_image_ai(sender_id, url):
    try:
        gender = user_state[sender_id].get("gender", "ولد")
        char_desc = create_character_reference(url, gender=gender, is_url=True)
        if char_desc:
            user_state[sender_id].update({"char_desc": char_desc, "step": "waiting_for_age"})
            send_quick_replies(sender_id, "تم استلام الصورة بنجاح! ✨ كم عمر طفلك؟", ["1-2", "2-3", "3-4", "4-5"])
    except Exception as e:
        logger.error(f"AI Error: {e}")

def handle_age_selection(sender_id, age_group):
    user_state[sender_id].update({"age_group": age_group, "step": "waiting_for_value"})
    send_quick_replies(sender_id, f"لعمر {age_group}، ما هي القيمة التي تودين تعليمها لطفلك؟", ["الصدق", "التعاون", "الاحترام", "الشجاعة"])

def handle_value_selection(sender_id, value, background_tasks):
    user_state[sender_id]["selected_value"] = value
    send_text_message(sender_id, f"📖 جاري رسم غلاف القصة المخصص... انتظروني!")
    background_tasks.add_task(process_story_generation, sender_id, value, is_preview=True)

def process_payment_verification(sender_id, image_url):
    try:
        response = requests.get(image_url)
        base64_img = base64.b64encode(response.content).decode("utf-8")
        if verify_payment_screenshot(base64_img, PAYMENT_NUMBER):
            send_text_message(sender_id, "✅ تم تأكيد الدفع بنجاح! نبدأ الآن رسم القصة كاملة...")
            value = user_state[sender_id].get("selected_value")
            process_story_generation(sender_id, value, is_preview=False)
        else:
            send_text_message(sender_id, "❌ لم نتمكن من التحقق من الصورة. يرجى إرسال لقطة شاشة واضحة للتحويل.")
    except Exception as e:
        logger.error(f"Payment Error: {e}")

def process_story_generation(sender_id, value, is_preview=False):
    try:
        data = user_state[sender_id]
        child_name, gender, char_desc = data["child_name"], data["gender"], data["char_desc"]
        prefix = "بطلة" if gender == "بنت" else "بطل"
        display_title = f"{prefix} {value}"
        
        # تحضير النصوص عبر StoryManager
        manager = StoryManager(child_name)
        manager.character_desc = char_desc  # 🌟 [تم الإصلاح] تمرير وصف ملامح الطفل ليتم دمجها في الصور
        
        # 🌟 [تم الإصلاح] توحيد أسماء الملفات لتطابق ما حفظناه
        value_map = {
            "الشجاعة": "courage.json", 
            "الصدق": "honesty.json", 
            "التعاون": "cooperation.json", 
            "الاحترام": "politeness.json"
        }
        
        json_filename = value_map.get(value)
        pages_prompts = manager.generate_story_prompts(json_filename, data.get("age_group"))
        
        # 🌟 [تم الإصلاح] حماية السيرفر من الانهيار إذا لم يجد القصة
        if not pages_prompts:
            send_text_message(sender_id, "⚠️ عذراً، محتوى هذه القصة قيد التحديث حالياً. يرجى المحاولة لاحقاً أو اختيار قيمة أخرى.")
            return

        total_pages = len(pages_prompts)
        cover_path = f"/tmp/cover_{sender_id}.png"

        # --- حالة المعاينة: توليد الغلاف فقط ---
        if is_preview:
            cover_url = generate_storybook_page(char_desc, f"Magical watercolor cover for {value}", gender=gender, is_cover=True)
            if cover_url and create_cover_page(cover_url, display_title, child_name, cover_path):
                send_image(sender_id, cover_path)
                time.sleep(1)
                msg = (f"💰 لإكمال قصة {child_name}، يرجى تحويل 25 جنيه عبر:\n"
                       f"📍 فودافون كاش أو إنستا باي: {PAYMENT_NUMBER}\n"
                       f"📸 ثم أرسلي صورة التحويل هنا فوراً!")
                user_state[sender_id]["step"] = "waiting_for_payment"
                send_text_message(sender_id, msg)
            return

        # --- حالة التوليد الكامل: رسم الصفحات وتجميع الـ PDF ---
        generated_images = [cover_path] if os.path.exists(cover_path) else []
        
        for i, p in enumerate(pages_prompts):
            page_num = i + 1
            send_text_message(sender_id, f"⏳ جاري تحميل الصفحة {page_num} من {total_pages}...")
            
            img_url = generate_storybook_page(char_desc, p["prompt"], gender=gender)
            if img_url:
                path = f"/tmp/p_{sender_id}_{i}.png"
                overlay_text_on_image(img_url, p["text"], path)
                generated_images.append(path)
            else:
                send_text_message(sender_id, f"⚠️ عذراً، تأخرت الصفحة {page_num}.. أحاول مرة أخرى.")
                # محاولة إعادة توليد بسيطة لضمان الاستمرارية
                img_url = generate_storybook_page(char_desc, p["prompt"], gender=gender)
                if img_url:
                    path = f"/tmp/p_{sender_id}_{i}.png"
                    overlay_text_on_image(img_url, p["text"], path)
                    generated_images.append(path)

        if len(generated_images) > 1:
            send_text_message(sender_id, "✅ اكتملت الرسومات! جاري تجميع ملف الـ PDF... 📚")
            pdf_path = f"/tmp/story_{sender_id}.pdf"
            create_pdf(generated_images, pdf_path)
            send_file(sender_id, pdf_path)
            send_text_message(sender_id, f"🎉 قصة {child_name} جاهزة! نتمنى لكم قراءة ممتعة. هل نجهز قصة أخرى؟")
            user_state[sender_id] = {"step": "start"}

    except Exception as e:
        logger.error(f"Story Gen Error: {e}")
        send_text_message(sender_id, "😔 حدث خطأ غير متوقع، جاري مراجعة النظام.")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
