#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os


def _contains_arabic(text: str) -> bool:
    """تحقق بسيط إذا كان النص يحتوي على أي حرف عربي."""
    if not isinstance(text, str):
        return False
    return any("\u0600" <= ch <= "\u06FF" for ch in text)


def verify_complete_setup():
    """التحقق الشامل من جميع ملفات القصص في stories_content/"""

    print("\n" + "=" * 70)
    print("🔍 التحقق الشامل من ملفات القصص العربية (stories_content/)")
    print("=" * 70 + "\n")

    values = ["الشجاعة", "الصدق", "التعاون", "الاحترام"]
    age_groups = ["1-2", "2-3", "3-4", "4-5"]
    total_issues = 0

    for value in values:
        target_file = os.path.join("stories_content", f"{value}.json")

        print(f"📖 القيمة: {value}")
        print(f"   الملف: {target_file}")

        if not os.path.exists(target_file):
            print(f"   ❌ الملف غير موجود!")
            total_issues += 1
            print()
            continue

        try:
            with open(target_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            print(f"   ✅ تم قراءة الملف بنجاح")

            # التحقق من كل فئة عمرية
            for age in age_groups:
                if age in data:
                    pages = data[age].get("pages", [])
                    if pages:
                        has_arabic = any(
                            _contains_arabic(page.get("text", "")) for page in pages
                        )

                        if has_arabic:
                            print(f"   ✅ عمر {age}: {len(pages)} صفحات - يحتوي على نص عربي")
                        else:
                            print(
                                f"   ⚠️  عمر {age}: {len(pages)} صفحات - لا يحتوي على نص عربي واضح في حقل 'text'!"
                            )
                            total_issues += 1
                    else:
                        print(f"   ⚠️  عمر {age}: لا توجد صفحات!")
                        total_issues += 1
                else:
                    print(f"   ❌ عمر {age}: غير موجود!")
                    total_issues += 1

        except Exception as e:
            print(f"   ❌ خطأ: {e}")
            total_issues += 1

        print()

    # النتيجة النهائية
    print("=" * 70)
    if total_issues == 0:
        print("✅ كل شيء جاهز! جميع ملفات القصص صحيحة ومكتملة!")
    else:
        print(f"⚠️  تم العثور على {total_issues} مشكلة - يرجى المراجعة")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    verify_complete_setup()

