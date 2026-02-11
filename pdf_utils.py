from fpdf import FPDF
import os

def create_pdf(child_name, value, story_text):
    """
    Generates a text file containing the story (fallback for Arabic encoding issues).
    Returns the file path.
    """
    # For now, create a simple text file instead of PDF
    # This avoids all encoding issues with FPDF and Arabic
    file_path = f"/tmp/story_{value}.txt"
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"قصة عن {value}\n")
        f.write("=" * 50 + "\n\n")
        f.write(story_text)
        f.write("\n\n" + "=" * 50)
        f.write(f"\n\nتم إنشاء القصة بواسطة بوت قصص الأطفال الذكية")
    
    return file_path
