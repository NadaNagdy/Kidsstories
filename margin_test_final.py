from image_utils import create_text_page
import os

test_text = "ذاتَ يَوْمٍ، ذَهَبَ الْبَطَلُ عُمَرُ إِلَى الْحَدِيقَةِ لِيَلْعَبَ مَعَ أَصْدِقَائِهِ. الصدقُ مَنْجاةٌ."
output_path = "/Users/nadanagdy/Kidsstories/story_assets/margin_test_final.png"

result = create_text_page(test_text, output_path)
print(f"✅ Final margin test page generated at: {result}")
