#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os


def test_story_loading():
    """اختبار تحميل القصص العربية من ملفات JSON في stories_content/"""

    values = ["الشجاعة", "الصدق", "التعاون", "الاحترام"]
    age_groups = ["1-2", "2-3", "3-4", "4-5"]

    print("=" * 60)
    print("🧪 اختبار تحميل القصص العربية من stories_content/")
    print("=" * 60)

    for value in values:
        filename = os.path.join("stories_content", f"{value}.json")

        print(f"\n📖 جاري اختبار: {value}")
        print(f"   الملف: {filename}")

        # التحقق من وجود الملف
        if not os.path.exists(filename):
            print(f"   ❌ الملف غير موجود!")
            continue

        try:
            # قراءة الملف
            with open(filename, "r", encoding="utf-8") as f:
                story_data = json.load(f)

            print(f"   ✅ تم فتح الملف بنجاح")

            # التحقق من كل فئة عمرية
            for age in age_groups:
                if age in story_data:
                    pages = story_data[age].get("pages", [])
                    print(f"   ✅ عمر {age}: {len(pages)} صفحات")

                    # عرض أول نص عربي
                    if pages:
                        first_text = pages[0].get("text", "")
                        snippet = first_text[:50].replace("\n", " ")
                        print(f"      النص الأول: {snippet}...")
                else:
                    print(f"   ❌ عمر {age}: غير موجود في الملف")

        except json.JSONDecodeError as e:
            print(f"   ❌ خطأ في قراءة JSON: {e}")
        except Exception as e:
            print(f"   ❌ خطأ: {e}")

    print("\n" + "=" * 60)
    print("✅ انتهى الاختبار")
    print("=" * 60)


if __name__ == "__main__":
    test_story_loading()

