def generate_storybook_page(character_description, page_prompt, child_name=None, is_cover=False, is_final=False):
    """توليد صورة الصفحة مع معالجة روابط https أو بيانات Base64"""
    try:
        page_type = "COVER PAGE" if is_cover else ("FINAL REWARD PAGE" if is_final else "STORY PAGE")
        
        user_content = f"""
        TASK: {page_type}
        CHARACTER DESCRIPTION: {character_description}
        SCENE DESCRIPTION: {page_prompt}
        {f'CHILD NAME: {child_name}' if child_name else ''}
        
        REMINDERS:
        - Use the global watercolor style.
        - Child MUST wear the striped sweatshirt.
        - Leave the bottom 25% of the image empty for text.
        """.strip()

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://kidsstories.railway.app",
            "X-Title": "Kids Story Bot"
        }

        payload = {
            "model": "google/gemini-2.5-flash-image",
            "messages": [
                {"role": "system", "content": GLOBAL_STORYBOOK_STYLE},
                {"role": "user", "content": user_content}
            ],
            "modalities": ["image"]
        }
        
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        data = response.json()
        
        # 1. البحث في حقل images المخصص (الأكثر دقة)
        try:
            choices = data.get('choices', [])
            if choices:
                message = choices[0].get('message', {})
                images = message.get('images', [])
                if images:
                    img_url = images[0].get('image_url', {}).get('url', '')
                    if img_url:
                        print(f"✅ Image Found in structured field (Base64 or URL)")
                        return img_url
        except Exception as e:
            print(f"Checking images field failed: {e}")

        # 2. إذا لم نجدها في الحقل المنظم، نبحث بالـ Regex في كل الرد
        full_response_text = str(data)
        
        # البحث عن Base64
        if "data:image" in full_response_text:
            base64_match = re.search(r'data:image/[^;]+;base64,[^"\'\s]+', full_response_text)
            if base64_match:
                print("✅ Base64 Image Found via Regex")
                return base64_match.group(0)

        # البحث عن رابط https
        url_match = re.search(r'https://[^\s"\'<>]+(?:\.png|\.jpg|\.jpeg|\b)', full_response_text)
        if url_match:
            print("✅ HTTPS Image URL Found via Regex")
            return url_match.group(0).rstrip(').')
        
        print(f"⚠️ No image data found in response: {full_response_text[:200]}...")
        return None

    except Exception as e:
        print(f"❌ Error generating page: {e}")
        return None
