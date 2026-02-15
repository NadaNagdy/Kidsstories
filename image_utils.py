from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import requests
import base64
from io import BytesIO
import arabic_reshaper
from bidi.algorithm import get_display
def get_image_source(source):
    """
    دالة ذكية لفتح الصورة سواء كانت رابط URL أو مسار ملف محلي (مثل مخرجات Flux)
    """
    try:
        # إذا كان المدخل رابط يبدأ بـ http
        if isinstance(source, str) and source.startswith("http"):
            response = requests.get(source, timeout=15)
            return Image.open(BytesIO(response.content))
        
        # إذا كان مسار ملف موجود على السيرفر (/tmp/...)
        elif isinstance(source, str) and os.path.exists(source):
            return Image.open(source)
            
        # إذا كانت الصورة مفتوحة بالفعل (Image object)
        elif isinstance(source, Image.Image):
            return source
            
        return None
    except Exception as e:
        print(f"❌ Error in get_image_source: {e}")
        return None
# ---------------------------------------------------------------------------
# 1. محرك النصوص العربية (إصلاح الحروف الناقصة والروابط)
# ---------------------------------------------------------------------------

def _prepare_arabic_text(text: str) -> str:
    """تحضير النص ليكون مقروءاً وصحيحاً برمجياً مع دعم كامل للحروف والروابط"""
    if not text: return ""
    
    # استخدام الدالة المباشرة للحصول على أفضل النتائج الافتراضية
    reshaped_text = arabic_reshaper.reshape(text)
    return get_display(reshaped_text)

def _get_arabic_font(size: int, weight: str = "bold") -> ImageFont.FreeTypeFont:
    """تحميل الخطوط مع ضمان دعم كامل للحروف العربية - NotoSansArabic أولاً (أفضل توافق)"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    fonts_dir = os.path.join(base_dir, "fonts")
    suffix = "-Bold.ttf" if weight.lower() == "bold" else "-Regular.ttf"

    # قائمة الخطوط بترتيب الأفضلية (NotoSansArabic يدعم كل الحروف العربية بدون نقص)
    font_candidates = [
        # المحاولة 1: NotoSansArabic (يدعم جميع Arabic Presentation Forms بدون استثناء)
        os.path.join(fonts_dir, f"NotoSansArabic{suffix}"),
        # المحاولة 2: خط Geeza Pro (ممتاز على Mac فقط)
        "/System/Library/Fonts/GeezaPro.ttc",
        # المحاولة 3: Almarai و Cairo (قد تكون فيهما حروف ناقصة)
        os.path.join(fonts_dir, f"Almarai{suffix}"),
        os.path.join(fonts_dir, f"Cairo{suffix}"),
        # المحاولة 4: خط Arial (احتياطي)
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]

    for font_path in font_candidates:
        try:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, size)
                print(f"✅ Loaded Arabic font: {os.path.basename(font_path)}")
                return font
        except Exception as e:
            print(f"⚠️ Failed to load {font_path}: {e}")
            continue

    print("⚠️ Using default PIL font (NO ARABIC SUPPORT)")
    return ImageFont.load_default()

def _detect_best_position(img):
    """تحليل الصورة للعثور على أفضل مساحة (أغمق مساحة) للنص الأصفر"""
    try:
        w, h = img.size
        # فحص الجزء العلوي (أول 30%) والجزء السفلي (آخر 30%)
        top_slice = img.crop((0, 0, w, int(h * 0.3))).convert("L")
        bottom_slice = img.crop((0, int(h * 0.7), w, h)).convert("L")
        
        top_bright = sum(top_slice.getdata()) / (w * int(h * 0.3))
        bottom_bright = sum(bottom_slice.getdata()) / (w * (h - int(h * 0.7)))
        
        # نختار المنطقة الأغمق ليكون النص الأصفر بارزاً جداً
        return "TOP" if top_bright < bottom_bright else "BOTTOM"
    except:
        return "BOTTOM"

# ---------------------------------------------------------------------------
# 2. وظائف إنشاء الصور (تحسين البروز والوضوح)
# ---------------------------------------------------------------------------

def create_cover_page(image_url, value, child_name, gender, output_path):
    """إنشاء الغلاف بملء الصفحة مع نصوص صفراء فائقة الوضوح"""
    try:
        width, height = 1024, 1024
        art_source = get_image_source(image_url)
        if not art_source: return None
        
        img = art_source.convert("RGB").resize((width, height), Image.LANCZOS)
        draw = ImageDraw.Draw(img)
        
        title_font = _get_arabic_font(115, weight="bold")
        name_font = _get_arabic_font(105, weight="bold")

        main_fill = (255, 235, 0)
        stroke_color = (0, 0, 0) # أسود للحدود لضمان البروز

        # 1. العنوان المسطح في الأعلى
        prefix = "بطلة" if gender == "بنت" else "بطل"
        top_text = f"{prefix} {value}"
        reshaped_top = _prepare_arabic_text(top_text)
        
        # تصغير الخط تلقائياً وتوسيع الهوامش لضمان عدم اختفاء أي حرف (مثل القاف في الصدق)
        current_title_size = 90 # تقليل الحجم الابتدائي قليلاً
        max_title_width = 700   # ترك مساحة كافية على الجوانب (162px من كل جهة)
        
        while current_title_size > 40:
            title_font = _get_arabic_font(current_title_size, weight="bold")
            bbox = draw.textbbox((0, 0), reshaped_top, font=title_font, stroke_width=10)
            tw = bbox[2] - bbox[0]
            if tw < max_title_width:
                break
            current_title_size -= 5
            
        tx, ty = (width - tw) // 2 - bbox[0], 80
        draw.text((tx, ty), reshaped_top, font=title_font, fill=main_fill, 
                  stroke_width=10, stroke_fill=stroke_color)

        # 2. اسم الطفل في الأسفل
        reshaped_name = _prepare_arabic_text(child_name)
        
        current_name_size = 90
        while current_name_size > 40:
            name_font = _get_arabic_font(current_name_size, weight="bold")
            n_bbox = draw.textbbox((0, 0), reshaped_name, font=name_font, stroke_width=10)
            nw = n_bbox[2] - n_bbox[0]
            if nw < max_title_width:
                break
            current_name_size -= 5
            
        nx, ny = (width - nw) // 2 - n_bbox[0], 860
        draw.text((nx, ny), reshaped_name, font=name_font, fill=main_fill,
                  stroke_width=10, stroke_fill=stroke_color)

        img.save(output_path, quality=100, subsampling=0) 
        return output_path
    except Exception as e:
        print(f"❌ Error in create_cover_page: {e}")
        return None

def overlay_text_on_image(image_url, text, output_path):
    """توزيع النص بذكاء في المساحات الفارغة بلون أصفر وبروز عالٍ"""
    try:
        width, height = 1024, 1024
        art_source = get_image_source(image_url)
        if not art_source: return None
        
        img = art_source.convert("RGB").resize((width, height), Image.LANCZOS)
        
        # تحديد أفضل مكان للنص
        position = _detect_best_position(img)
        draw = ImageDraw.Draw(img)
        
        font = _get_arabic_font(45, weight="bold")
        main_fill = (255, 235, 0)
        stroke_color = (0, 0, 0)
        
        # تقسيم النص لسطور
        lines = []
        words = text.split()
        current_line = []
        for word in words:
            current_line.append(word)
            test_line = " ".join(current_line)
            if draw.textlength(_prepare_arabic_text(test_line), font=font) > 820:
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        lines.append(" ".join(current_line))
        
        line_height = 60
        total_height = len(lines) * line_height
        
        # اختيار الإحداثيات بناءً على ذكاء المساحة
        if position == "TOP":
            start_y = 60
        else:
            start_y = height - total_height - 100
        
        for i, line in enumerate(lines):
            line_reshaped = _prepare_arabic_text(line)
            lw = draw.textlength(line_reshaped, font=font)
            lx = (width - lw) // 2
            ly = start_y + (i * line_height)
            
            # رسم النص بحدود سميكة جداً لضمان القراءة
            draw.text((lx, ly), line_reshaped, font=font, fill=main_fill,
                      stroke_width=10, stroke_fill=stroke_color)

        img.save(output_path, quality=100, subsampling=0)
        return output_path
    except Exception as e:
        print(f"❌ Error in overlay_text_on_image: {e}")
        return None

def create_text_page(text, output_path):
    """
    إنشاء صفحة بيضاء تحتوي على نص القصة بشكل أنيق وواضح جداً
    تزيل مشكلة الحروف الناقصة وتوفر راحة في القراءة
    """
    try:
        width, height = 1024, 1024
        # إنشاء صفحة بيضاء نقية
        img = Image.new("RGB", (width, height), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # اختيار خط كبير وواضح (Regular لراحة العين)
        # اختيار خط كبير وواضح (Regular لراحة العين)
        font = _get_arabic_font(50, weight="regular")
        text_color = (0, 0, 0) # أسود نقي (Black) للتباين العالي والوضوح التام
        
        # نظام ذكي لتقسيم السطور مع هوامش كبيرة جداً لضمان عدم قص أي حرف
        # الهوامش الآمنة (Margin) على الجوانب لمنع القص
        SAFE_MARGIN = 100 
        max_width = width - (SAFE_MARGIN * 2) 

        lines = []
        words = text.split()
        current_line = []
        
        for word in words:
            current_line.append(word)
            test_line = " ".join(current_line)
            reshaped_test = _prepare_arabic_text(test_line)
            
            # قياس دقيق جداً
            bbox = draw.textbbox((0, 0), reshaped_test, font=font)
            test_width = bbox[2] - bbox[0]
            
            if test_width > max_width:
                # إذا تجاوزنا العرض: احذف الكلمة الأخيرة، احفظ السطر، وابدأ سطراً جديداً
                current_line.pop()
                lines.append(" ".join(current_line))
                current_line = [word]
        
        # إضافة السطر الأخير
        if current_line:
            lines.append(" ".join(current_line))
            
        # حساب التمركز العمودي
        line_height = 100 # مسافة مريحة
        total_text_height = len(lines) * line_height
        start_y = (height - total_text_height) // 2
        
        for i, line in enumerate(lines):
            reshaped_line = _prepare_arabic_text(line)
            bbox = draw.textbbox((0, 0), reshaped_line, font=font)
            w_line = bbox[2] - bbox[0]
            
            # حساب الإحداثي الأفقي للمنتصف
            lx = (width - w_line) // 2
            
            # تصحيح offset الخط (لأن bbox لا يبدأ من 0 دائماً في الخطوط العربية)
            lx = lx - bbox[0]

            ly = start_y + (i * line_height)
            
            draw.text((lx, ly), reshaped_line, font=font, fill=text_color)
            
        img.save(output_path, quality=100)
        return output_path
        
    except Exception as e:
        print(f"❌ Error in create_text_page: {e}")
        return None
def create_html_flipbook(image_paths, child_name, output_path):
    """
    إنشاء ملف HTML تفاعلي يحتوي على القصة كاملة مع تأثير تقليب الصفحات
    يتم دمج الصور داخل الملف (Base64) ليعمل بدون إنترنت أو روابط خارجية
    """
    try:
        pages_html = ""
        for i, img_path in enumerate(image_paths):
            with open(img_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
            # الغلاف أول صفحة، ثم النص، ثم الرسم (الترتيب العربي الصحيح)
            page_type = "cover" if i == 0 else ("text" if i % 2 != 0 else "art")
            
            pages_html += f"""
            <div class="page" data-density="{"hard" if page_type == "cover" else "soft"}">
                <div class="page-content">
                    <img src="data:image/png;base64,{encoded_string}" alt="Page {i}">
                </div>
            </div>
            """

        html_template = f"""
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>قصة {child_name}</title>
    <style>
        body {{ margin: 0; background: #e0e0e0; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; font-family: sans-serif; }}
        .header {{ margin-bottom: 20px; }}
        #book-container {{ width: 90vw; max-width: 800px; height: 80vh; display: flex; justify-content: center; align-items: center; }}
        #book {{ width: 100%; height: 100%; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }}
        .page {{ background: white; width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; overflow: hidden; border: 1px solid #ddd; }}
        .page-content {{ width: 100%; height: 100%; display: flex; align-items: center; justify-content: center; }}
        .page img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
        .controls {{ margin-top: 20px; display: flex; gap: 15px; }}
        button {{ padding: 10px 20px; border-radius: 20px; border: none; background: #00bcd4; color: white; cursor: pointer; }}
    </style>
</head>
<body>
    <div class="header"><h1>📖 قصة {child_name}</h1></div>
    <div id="book-container"><div id="book">{pages_html}</div></div>
    <div class="controls">
        <button onclick="book.flipPrev()">السابق</button>
        <button onclick="book.flipNext()">التالي</button>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/page-flip@2.0.7/dist/js/page-flip.browser.js"></script>
    <script>
        const bookElement = document.getElementById('book');
        const book = new St.PageFlip(bookElement, {{
            width: 800, height: 800, size: "stretch", showCover: true, useMouseOver: false
        }});
        book.loadFromHTML(document.querySelectorAll('.page'));
    </script>
</body>
</html>
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_template)
        return output_path
    
    except Exception as e:
        print(f"❌ Error in create_html_flipbook: {e}")
        return None
