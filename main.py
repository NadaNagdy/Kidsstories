from fastapi import FastAPI, Request, BackgroundTasks, HTTPException, Response
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import os, uvicorn, logging, requests, base64, time, json, shutil, uuid

# استيراد الدوال من الملفات المساعدة
from dotenv import load_dotenv
load_dotenv() # Load environment variables from .env file early

from messenger_api import send_text_message, send_quick_replies, send_file, send_image
from pdf_utils import create_pdf
from openai_service import verify_payment_screenshot, generate_storybook_page, create_character_reference
from image_utils import overlay_text_on_image, create_cover_page, create_text_page
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
    return HTMLResponse("""
    <html>
        <head>
            <title>Kids Story Bot</title>
            <style>body { font-family: sans-serif; text-align: center; padding: 50px; } a { color: #3498db; }</style>
        </head>
        <body>
            <h1>🤖 Kids Story Bot is Active!</h1>
            <p>We create personalized stories for children.</p>
            <p><a href="/privacy-policy">Privacy Policy</a></p>
        </body>
    </html>
    """)

@app.get("/privacy-policy", response_class=HTMLResponse)
def privacy_policy():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Privacy Policy - Kids Story Bot</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; padding: 40px; line-height: 1.6; max-width: 800px; margin: 0 auto; color: #333; }
            h1 { color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px; }
            h2 { color: #34495e; margin-top: 30px; }
            .ar { direction: rtl; text-align: right; background: #f9f9f9; padding: 20px; border-radius: 8px; margin-top: 40px; }
            .en { margin-bottom: 40px; }
            ul { margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="en">
            <h1>Privacy Policy</h1>
            <p><strong>Effective Date:</strong> February 15, 2026</p>
            <p>This Privacy Policy explains how <strong>Kids Story Bot</strong> ("we", "us") collects, uses, and protects your information when you use our Messenger service.</p>
            
            <h2>1. Information We Collect</h2>
            <ul>
                <li><strong>Photos:</strong> We collect photos of your child ONLY for the purpose of generating a stylized story character. These images are processed temporarily and are not used for training public AI models.</li>
                <li><strong>Names & Ages:</strong> Used solely to personalize the story text.</li>
                <li><strong>Facebook User ID:</strong> To send you the completed story PDF.</li>
            </ul>

            <h2>2. How We Use Your Information</h2>
            <p>Your data is used strictly to:</p>
            <ul>
                <li>Generate the requested story and illustrations via OpenAI APIs.</li>
                <li>Deliver the final PDF file to you.</li>
            </ul>
            <p>WE DO NOT sell your data or photos to third parties.</p>

            <h2>3. Contact Us</h2>
            <p>If you have questions, please contact us via our Facebook Page.</p>

            <h2>4. Data Deletion</h2>
            <p>To request deletion of your data, simply message our page with the word "Delete" or contact the admin directly.</p>
        </div>
        
        <div class="ar">
            <h1>سياسة الخصوصية</h1>
            <p><strong>تاريخ التحديث:</strong> ١٥ فبراير ٢٠٢٦</p>
            <p>توضح سياسة الخصوصية هذه كيفية تعاملنا مع بياناتك عند استخدامك لخدمة "Kids Story Bot".</p>
            
            <h2>١. البيانات التي نجمعها</h2>
            <ul>
                <li><strong>الصور:</strong> نطلب صور الطفل فقط لتحويلها لشخصية كرتونية داخل القصة. نحن نحترم خصوصية أطفالكم ولا نستخدم هذه الصور في أي أغراض أخرى ولا نشاركها مع العامة.</li>
                <li><strong>الاسم والعمر:</strong> لتخصيص محتوى القصة.</li>
            </ul>

            <h2>٢. كيف نستخدم بياناتك</h2>
            <p>تستخدم البيانات حصرياً لغرض واحد: إنشاء القصة وإرسالها لك. لا نقوم ببيع أو مشاركة بياناتك مع أي طرف ثالث.</p>

            <h2>٣. تواصل معنا</h2>
            <p>إذا كان لديك أي استفسار، يرجى مراسلتنا فوراً عبر صفحة الفيسبوك.</p>

            <h2>٤. حذف البيانات</h2>
            <p>لطلب حذف بياناتك، يمكنك ببساطة إرسال كلمة "حذف" أو "Delete" في رسالة للصفحة، أو التواصل مع الأدمن مباشرة.</p>
        </div>
    </body>
    </html>
    """

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
        step = user_state[sender_id].get("step")
        
        if step == "waiting_for_gender":
            user_state[sender_id].update({"gender": payload, "step": "waiting_for_age"})
            send_quick_replies(sender_id, "ممتاز! كم عمر طفلك؟", ["1-2", "2-3", "3-4", "4-5"])
        
        elif step == "waiting_for_age":
            handle_age_selection(sender_id, payload)
            
        elif step == "waiting_for_value":
            handle_value_selection(sender_id, payload, background_tasks)
            
        elif step == "waiting_for_payment":
            if payload in ["PAY_25_EGP", "تم الدفع", "تم التحويل ✅"]:
                send_text_message(sender_id, "بانتظار صورة التحويل (Screenshot) للتأكيد... 📸")
        return

    if "attachments" in message:
        for att in message["attachments"]:
            if att["type"] == "image":
                handle_image_reception(sender_id, att["payload"]["url"], background_tasks)
                return

    text = message.get("text", "")
    if text:
        # --- 1. طلب الباقة (Story Pack) ---
        if "باقة" in text or "baqa" in text.lower():
            user_state[sender_id]["step"] = "waiting_for_pack_payment"
            child_name = user_state[sender_id].get("child_name", "الطفل")
            msg = (
                f"🎉 اختيار ممتاز! باقة الـ 3 مغامرات لـ {child_name} 📚\n"
                f"السعر: ٦٠ جنيه فقط (بدل ١٢٠!)\n\n"
                f"من فضلك حولي المبلغ الآن على:\n"
                f"📍 {PAYMENT_NUMBER}\n"
                f"وابعتي صورة التحويل هنا عشان نبدأ فوراً! 🚀"
            )
            send_text_message(sender_id, msg)
            return

        # --- 2. طلب الفيديو (Hero Movie) ---
        if "فيديو" in text or "video" in text.lower():
            user_state[sender_id]["step"] = "waiting_for_video_payment"
            child_name = user_state[sender_id].get("child_name", "الطفل")
            msg = (
                f"🎬 اختيار رائع! {child_name} هيكون بطل فيلمه الخاص! ✨\n"
                f"فيديو احترافي بصوره واسمه ومؤثرات صوتية.\n"
                f"السعر: ١٠٠ جنيه فقط (بدل ٢٠٠)\n"
                f"⏱️ الاستلام: خلال ٢٤ ساعة\n\n"
                f"من فضلك حولي المبلغ الآن على:\n"
                f"📍 {PAYMENT_NUMBER}\n"
                f"وابعتي صورة التحويل هنا لتأكيد الحجز! 🎟️"
            )
            send_text_message(sender_id, msg)
            return

        if text.lower() == "start":
            user_state[sender_id] = {"step": "waiting_for_name"}
            send_text_message(sender_id, "👋 أهلاً بك في عالم القصص الذكية!")
            send_text_message(sender_id, "ما اسم بطل القصة أو بطلتنا الصغيرة؟")
        elif user_state[sender_id].get("step") == "waiting_for_name":
            user_state[sender_id].update({"child_name": text, "step": "waiting_for_gender"})
            send_quick_replies(sender_id, f"تشرفنا يا {text}! 😊 هل البطل ولد أم بنت؟", ["ولد", "بنت"])

def handle_image_reception(sender_id, url, background_tasks):
    step = user_state[sender_id].get("step")
    if step == "waiting_for_payment":
        send_text_message(sender_id, "🔍 جاري التحقق من التحويل... لحظات!")
        background_tasks.add_task(process_payment_verification, sender_id, url)
    elif step == "waiting_for_photo":
        user_state[sender_id]["photo_url"] = url
        send_text_message(sender_id, "🎨 جاري تحليل الملامح وبناء الشخصية بدقة...")
        background_tasks.add_task(process_image_ai, sender_id, url)

from io import BytesIO
from PIL import Image

def process_image_ai(sender_id, url):
    try:
        gender = user_state[sender_id].get("gender", "ولد")
        child_name = user_state[sender_id].get("child_name", "الطفل")
        age_group = user_state[sender_id].get("age_group", "3-4")
        
        # تحميل الصورة وتحويلها إلى Standard JPEG Base64
        try:
            response = requests.get(url, timeout=20)
            if response.status_code == 200:
                # معالجة الصورة باستخدام PIL لضمان التنسيق
                img = Image.open(BytesIO(response.content))
                img = img.convert("RGB") # إزالة الشفافية وتحويلها إلى ألوان قياسية
                
                # تصغير الصورة إذا كانت ضخمة جداً لتسريع التحليل
                if img.width > 1024 or img.height > 1024:
                    img.thumbnail((1024, 1024))
                
                buffer = BytesIO()
                img.save(buffer, format="JPEG", quality=85)
                b64_image = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                # إرسال الصورة المعالجة مع تمرير الاسم والعمر
                char_desc = create_character_reference(b64_image, gender=gender, is_url=False, use_ai_analysis=True, child_name=child_name, age=age_group)
            else:
                logger.error(f"❌ Failed to download image from URL: {url}")
                char_desc = create_character_reference(url, gender=gender, is_url=True, use_ai_analysis=True, child_name=child_name, age=age_group)
        except Exception as dl_err:
            logger.error(f"❌ Image processing error: {dl_err}")
            char_desc = create_character_reference(url, gender=gender, is_url=True, use_ai_analysis=True, child_name=child_name, age=age_group)

        if char_desc == "ERROR_REFUSAL":
            send_text_message(sender_id, "بعتذر، مقدرناش نحلل ملامح الصورة دي. ياريت تبعتي صورة تانية واضحة لوش الطفل.")
            return

        if char_desc:
            user_state[sender_id].update({"char_desc": char_desc, "step": "waiting_for_value"})
            # بعد الصورة، نذهب مباشرة لاختيار القيمة لأن العمر تم اختياره مسبقاً
            send_quick_replies(sender_id, f"تم تحليل الشخصية بنجاح! ✨ الآن، ما هي القيمة التي تودين تعليمها لـ {child_name}؟", ["الصدق", "التعاون", "الاحترام", "الشجاعة"])
    except Exception as e:
        logger.error(f"AI Error: {e}", exc_info=True)

def handle_age_selection(sender_id, age_group):
    # حفظ العمر ثم الانتقال لطلب الصورة
    user_state[sender_id].update({"age_group": age_group, "step": "waiting_for_photo"})
    
    # رسالة طلب الصورة
    child_name = user_state[sender_id].get("child_name", "الطفل")
    gender = user_state[sender_id].get("gender", "ولد")
    suffix = "بطلتنا الجميلة" if gender == "بنت" else "بطلنا الصغير"
    
    send_text_message(sender_id, f"عظيم! 📸 أرسلي الآن صورة واضحة لوجه {suffix} {child_name} لنحولها لشخصية في القصة.")


def handle_value_selection(sender_id, value, background_tasks):
    user_state[sender_id]["selected_value"] = value
    send_text_message(sender_id, f"📖 جاري رسم غلاف القصة المخصص... انتظروني!")
    background_tasks.add_task(process_story_generation, sender_id, value, is_preview=True)

def process_pack_generation(sender_id):
    """Generates the remaining 3 stories for the user."""
    logger.info(f"📚 Starting Pack Generation for {sender_id}")
    
    # 1. Identify remaining values
    all_values = ["الشجاعة", "الصدق", "التعاون", "الاحترام"] 
    current_value = user_state[sender_id].get("selected_value")
    
    # Filter out current value if it exists in list
    remaining_values = [v for v in all_values if v != current_value]
    
    # If for some reason current_value is not in list (e.g. error), take first 3
    if len(remaining_values) == 4:
        remaining_values = remaining_values[:3]
        
    send_text_message(sender_id, f"جاري تحضير قصص: {', '.join(remaining_values)}... ⏳")
    
    # 2. Iterate and generate
    for val in remaining_values:
        process_story_generation(sender_id, val, is_preview=False, is_pack=True)
        
    # 3. Final Success Message
    send_text_message(sender_id, "🎁 كل القصص وصلت! استمتعوا بـ 'باقة المغامرات' معاً! 🥰")

def process_payment_verification(sender_id, image_url):
    try:
        response = requests.get(image_url)
        base64_img = base64.b64encode(response.content).decode("utf-8")
        
        # Enforce AI Verification
        is_valid, reason = verify_payment_screenshot(base64_img, PAYMENT_NUMBER, use_ai_verification=True)
        
        if is_valid:
            step = user_state[sender_id].get("step")
            
            # CASE A: Pack Payment (60 EGP)
            if step == "waiting_for_pack_payment":
                send_text_message(sender_id, "✅ تم استلام دفع الباقة! جاري تجهيز الـ 3 قصص حالاً... 📚✨")
                process_pack_generation(sender_id)
            
            # CASE B: Video Payment (100 EGP)
            elif step == "waiting_for_video_payment":
                child_name = user_state[sender_id].get("child_name", "الطفل")
                success_msg = (
                    f"✅ تم تأكيد حجز الفيديو لـ {child_name}! 🎬\n"
                    f"جاري العمل على المونتاج والمؤثرات...\n"
                    f"سيصلك الفيديو خلال 24 ساعة على هذا الشات. شكراً لثقتك! ❤️"
                )
                send_text_message(sender_id, success_msg)
                
                # Admin Notification
                admin_msg = f"🔔 NEW ORDER: Video Request 🎥\nUser: {child_name} ({sender_id})\nStatus: PAID 100 EGP\nAction: Create Video manually."
                logger.critical(admin_msg)
                admin_id = os.getenv("ADMIN_ID")
                if admin_id:
                    try:
                        send_text_message(admin_id, admin_msg)
                    except:
                        pass

            # CASE C: Single Story Payment
            else:
                send_text_message(sender_id, "✅ تم تأكيد الدفع بنجاح! نبدأ الآن رسم القصة كاملة... (سيستغرق عدة دقائق)")
                value = user_state[sender_id].get("selected_value")
                process_story_generation(sender_id, value, is_preview=False, is_pack=False)
        else:
            # Send detailed reason for rejection
            send_text_message(sender_id, f"❌ عذراً، لم نتمكن من قبول الدفع.\nالسبب: {reason}\nيرجى التأكد من إرسال إيصال صحيح وحديث.")
            
    except Exception as e:
        logger.error(f"Payment Error: {e}")
        send_text_message(sender_id, "❌ حدث خطأ غير متوقع أثناء التحقق. يرجى المحاولة لاحقاً.")

def process_story_generation(sender_id, value, is_preview=False, is_pack=False):
    try:
        data = user_state[sender_id]
        child_name = data.get("child_name", "")
        gender = data.get("gender", "")
        char_desc = data.get("char_desc", "")
        
        logger.info(f"🚀 Generating story for {child_name} - Value: {value} - Preview: {is_preview}")

        # تحضير النصوص عبر StoryManager
        manager = StoryManager(child_name, gender)
        manager.inject_character_dna(char_desc)
        
        # استخراج وصف الملابس من وصف الشخصية إذا وجد
        extracted_outfit = None
        if "Outfit details:" in char_desc:
            try:
                # محاولة استخراج الجزء الخاص بالملابس ببساطة
                parts = char_desc.split("Outfit details:")
                if len(parts) > 1:
                    extracted_outfit = parts[1].strip().split(".")[0] # أخذ أول جملة فقط
            except:
                pass

        # تعيين الملابس بناءً على العمر أو ما تم استخراجه
        manager.set_outfit_by_age(data.get("age_group"), extracted_outfit=extracted_outfit)
        
        # Inject personality based on the chosen value
        # We add some default positive traits along with the chosen value
        manager.inject_personality(
            traits=[value, "curious", "imaginative", "kind"],
            core_value=value
        ) 

        value_map = {
            "الشجاعة": "courage.json", 
            "الصدق": "honesty.json", 
            "التعاون": "cooperation.json", 
            "الاحترام": "respect.json" 
        }
        
        json_filename = value_map.get(value)
        pages_prompts = manager.generate_story_prompts(json_filename, data.get("age_group"))
        
        if not pages_prompts:
            send_text_message(sender_id, "⚠️ عذراً، محتوى هذه القصة قيد التحديث. يرجى اختيار قيمة أخرى.")
            return

        total_pages = len(pages_prompts)
        cover_path = f"/tmp/cover_{sender_id}.png"

        # --- حالة المعاينة: توليد الغلاف فقط ---
        if is_preview:
            # برومبت الغلاف المحسن لنموذج FLUX
            # برومبت الغلاف المحسن لنموذج FLUX - محايد لترك التفاصيل لـ char_desc
            cover_prompt = f"Professional children's book cover illustration for a story about {child_name} learning about {value}. Soft digital watercolor washes, delicate colored pencil detailing, dreamy cozy bedtime story aesthetic with warm glowing light. Masterpiece quality."
            
            cover_url = generate_storybook_page(char_desc, cover_prompt, gender=gender, age_group=data.get("age_group", "3-4"), is_cover=True)
            
            if cover_url:
                # استدعاء الدالة المعدلة لكتابة "بطل/بطلة القيمة" واسم الطفل
                if create_cover_page(cover_url, value, child_name, gender, cover_path):
                    send_image(sender_id, cover_path)
                    time.sleep(1)
                    msg = (f"💰 لإكمال قصة {child_name}، يرجى تحويل 25 جنيه عبر:\n"
                           f"📍 فودافون كاش أو إنستا باي: {PAYMENT_NUMBER}\n"
                           f"📸 ثم أرسلي صورة التحويل هنا فوراً!")
                    user_state[sender_id]["step"] = "waiting_for_payment"
                    send_text_message(sender_id, msg)
                else:
                    send_text_message(sender_id, "⚠️ حدث خطأ أثناء تجهيز الغلاف، جاري المحاولة مرة أخرى.")
            else:
                send_text_message(sender_id, "⚠️ أداة الرسم مشغولة حالياً، يرجى إعادة اختيار القيمة بعد ثوانٍ.")
            return

        # --- حالة التوليد الكامل: رسم الصفحات وتجميع الـ PDF ---
        generated_images = [cover_path] if os.path.exists(cover_path) else []
        
        for i, p in enumerate(pages_prompts):
            page_num = i + 1
            send_text_message(sender_id, f"⏳ جاري رسم الصفحة {page_num} من {total_pages}...")
            
            # 1. توليد صورة الرسم (الخلفية)
            img_result = generate_storybook_page(char_desc, p["prompt"], gender=gender, age_group=data.get("age_group", "3-4"))
            
            if not img_result:
                send_text_message(sender_id, f"⚠️ تأخرت الصفحة {page_num}.. أحاول مرة أخرى.")
                img_result = generate_storybook_page(char_desc, p["prompt"], gender=gender, age_group=data.get("age_group", "3-4"))

            if img_result:
                # أ. إنشاء وإضافة صفحة النص (مع استخدام الرسمة كخلفية مموهة لضمان التلوين الكامل)
                text_page_path = f"/tmp/text_{sender_id}_{i}.png"
                create_text_page(p["text"], text_page_path, background_source=img_result)
                generated_images.append(text_page_path)

                # ب. إضافة صفحة الرسم (لتكون على اليسار مقابلة للنص)
                generated_images.append(img_result)
            else:
                send_text_message(sender_id, f"❌ فشل توليد الصفحة {page_num}. سنكمل القصة بما توفر.")

        if len(generated_images) > 1:
            send_text_message(sender_id, "✅ اكتملت الرسومات! جاري تجهيز القصة لك... 📚")
            
            # 1. إنشاء ملف الـ PDF الأصلي
            pdf_path = f"/tmp/story_{sender_id}.pdf"
            create_pdf(generated_images, pdf_path)
            
            # 3. إرسال الملفات
            send_file(sender_id, pdf_path)
            
            # 4. رسالة الشكر والتهنئة
            thanks_msg = f"🎉 قصة {child_name} جاهزة!\n\nلقد أرسلت لك ملف القصة الذكية (PDF). استمتعي بقراءتها مع طفلك! 📖✨"
            send_text_message(sender_id, thanks_msg)
            
            # 5. عرض الترقية / باقات إضافية (فقط إذا لم يكن جزءاً من الباقة)
            if not is_pack:
                upsell_msg = (
                    f"🎁 تحبي تكملي المفاجأة لـ {child_name}؟ عندنا ليكي عرضين مميزين جداً! 👇\n\n"
                    f"1️⃣ *فيديو القصة السحري* (The Hero Movie) 🎬\n"
                    f"هنحول القصة دي لفيلم كرتون قصير بالموسيقى والمؤثرات، يتفرج عليه {child_name} ويشوف نفسه بطل الحكاية، وينبهر بصوته وصورته!\n"
                    f"⏱️ *الاستلام:* خلال ٢٤ ساعة\n"
                    f"💰 *السعر:* ١٠٠ جنيه بس (بدل ٢٠٠)\n\n"
                    f"2️⃣ *باقة الـ ٣ مغامرات* (The Story Pack) 📚\n"
                    f"لو {child_name} حب القصة دي، أكيد هيحب يكمل المغامرة! تقدري تحجزي ٣ قصص تانية بمواضيع مختلفة (زي: الشجاعة، حب النفس، الأمانة) كلهم باسمه وصورته، يسلوا وقته ويعلموه حاجات مفيدة طول الشهر.\n"
                    f"⚡ *الاستلام:* فوراً (في نفس الوقت!)\n"
                    f"💰 *السعر:* ٦٠ جنيه بس (عرض خاص للأبطال!)\n\n"
                    f"👇 للاشتراك، ردي بكلمة *فيديو* أو *باقة* وهنبدأ فوراً!"
                )
                send_text_message(sender_id, upsell_msg)
            
            # إعادة تعيين الحالة فقط إذا انتهت الباقة أو كانت قصة مفردة - في حالة الباقة، يتم التحكم بالحالة من الخارج أو لا يهم
            if not is_pack:
                user_state[sender_id] = {"step": "start"}

    except Exception as e:
        logger.error(f"Story Gen Error: {e}")
        send_text_message(sender_id, "😔 حدث خطأ غير متوقع في النظام.")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
