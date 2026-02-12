from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.responses import PlainTextResponse
import os, uvicorn, logging, requests, base64, time

# استيراد الدوال من الملفات الأخرى
from messenger_api import send_text_message, send_quick_replies, send_file, send_image
from pdf_utils import create_pdf
from openai_service import verify_payment_screenshot, generate_storybook_page, create_character_reference
from image_utils import overlay_text_on_image, create_cover_page
from story_manager import StoryManager

# إعداد السجلات
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# متغيرات البيئة
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "my_verify_token")
PAYMENT_NUMBER = os.getenv("INSTAPAY_HANDLE", "01060746538")
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

    # 2. معالجة المرفقات (الصورة)
    if "attachments" in message:
        for att in message["attachments"]:
            if att["type"] == "image":
                handle_image_reception(sender_id, att["payload"]["url"], background_tasks)
                return

    # 3. معالجة النصوص العادية
    text = message.get("text", "")
    if text:
        if text.lower() == "start":
            user_state[sender_id] = {"step": "waiting_for_name"}
            send_text_message(sender_id, "👋 أهلاً بك! ما اسم بطل القصة أو بطلتنا الصغيرة؟")
        elif user_state[sender_id].get("step") == "waiting_for_name":
            user_state[sender_id].update({"child_name": text, "step": "waiting_for_gender"})
            send_quick_replies(sender_id, f"تشرفنا يا {text}! 😊 هل البطل ولد أم بنت؟", ["ولد", "بنت"])

# --- دوال المعالجة المساعدة ---

def handle_image_reception(sender_id, url, background_tasks):
    step = user_state[sender_id].get("step")
    if step == "waiting_for_payment":
        send_text_message(sender_id, "🔍 جاري التحقق من صورة التحويل... لحظات!")
        background_tasks.add_task(process_payment_verification, sender_id, url)
    else:
        user_state[sender_id]["photo_url"] = url
        send_text_message(sender_id, "🎨 جاري تحليل الملامح وبناء الشخصية...")
        background_tasks.add_task(process_image_ai, sender_id, url)

def process_image_ai(sender_id, url):
    try:
        gender = user_state[sender_id].get("gender", "ولد")
        # استخراج وصف دقيق (100 كلمة) من الصورة
        char_desc = create_character_reference(url, gender=gender, is_url=True)
        if char_desc:
            user_state[sender_id].update({"char_desc": char_desc, "step": "waiting_for_age"})
            send_quick_replies(sender_id, "تم استلام الصورة! ✨ كم عمر طفلك؟", ["1-2", "2-3", "3-4", "4-5"])
    except Exception as e:
        logger.error(f"AI Analysis Error: {e}")

def handle_age_selection(sender_id, age_group):
    user_state[sender_id].update({"age_group": age_group, "step": "waiting_for_value"})
    send_quick_replies(sender_id, f"لعمر {age_group}، ما هي القيمة التي تودين تعليمها لطفلك؟", ["الصدق", "التعاون", "الاحترام", "الشجاعة"])

def handle_value_selection(sender_id, value, background_tasks):
    user_state[sender_id]["selected_value"] = value
    send_text_message(sender_id, f"📖 جاري تجهيز الغلاف باسم بطلنا... لحظات!")
    background_tasks.add_task(process_story_generation, sender_id, value, is_preview=True)

def process_payment_verification(sender_id, image_url):
    try:
        # تحميل الصورة وتحويلها لـ Base64 للتحقق
        response = requests.get(image_url)
        base64_image = base64.b64encode(response.content).decode("utf-8")
        is_valid = verify_payment_screenshot(base64_image, PAYMENT_NUMBER)
        
        if is_valid:
            send_text_message(sender_id, "✅ تم التأكد من الدفع! جاري رسم صفحات القصة كاملة... انتظروني!")
            value = user_state[sender_id].get("selected_value")
            process_story_generation(sender_id, value, is_preview=False)
        else:
            send_text_message(sender_id, "❌ لم نتمكن من التأكد من بيانات التحويل. يرجى إرسال صورة واضحة تظهر رقم المستلم والمبلغ.")
    except Exception as e:
        logger.error(f"Payment Verification Error: {e}")

def process_story_generation(sender_id, value, is_preview=False):
    try:
        data = user_state[sender_id]
        child_name = data.get("child_name", "بطلنا")
        gender = data.get("gender", "ولد")
        char_desc = data.get("char_desc", "A cute child")
        
        prefix = "بطلة" if gender == "بنت" else "بطل"
        display_title = f"{prefix} {value}"
        
        if is_preview:
            # توليد الغلاف فقط للمعاينة
            cover_url = generate_storybook_page(char_desc, f"Magical watercolor cover for {value} story", gender=gender, is_cover=True)
            path = f"/tmp/cover_{sender_id}.png"
            if create_cover_page(cover_url, display_title, child_name, path):
                send_image(sender_id, path)
                time.sleep(2)
                msg = (
                    f"💰 لإكمال قصة {child_name}، يرجى تحويل 25 جنيه:\n\n"
                    f"1️⃣ انستا باي: {PAYMENT_NUMBER}\n"
                    f"2️⃣ فودافون كاش: {PAYMENT_NUMBER}\n\n"
                    f"📸 أرسلي صورة التحويل هنا!"
                )
                user_state[sender_id]["step"] = "waiting_for_payment"
                send_text_message(sender_id, msg)
            return

        # توليد القصة الكاملة (هنا يتم استدعاء StoryManager لإنشاء الصفحات)
        # سيتم رسم كل صفحة ودمج النص عليها ثم إنشاء PDF
        # (الكود يكمل عملية التوليد المعتادة)
        
    except Exception as e:
        logger.error(f"Story Gen Error: {e}")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
