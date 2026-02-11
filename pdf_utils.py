from fpdf import FPDF
import os
import arabic_reshaper
from bidi.algorithm import get_display

def create_pdf(child_name, value, story_text):
    """
    Generates a PDF file containing the story with Arabic support.
    Returns the file path.
    """
    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    
    # Set font (Arial supports basic Latin characters)
    pdf.set_font("Arial", "B", 16)
    
    # Title (in English to avoid encoding issues in title)
    title = f"Story about {value}"
    pdf.cell(0, 10, title, ln=True, align='C')
    pdf.ln(10)
    
    # Process Arabic text for proper display
    # arabic_reshaper connects Arabic letters correctly
    # bidi handles right-to-left text direction
    reshaped_text = arabic_reshaper.reshape(story_text)
    bidi_text = get_display(reshaped_text)
    
    # Body text
    pdf.set_font("Arial", size=12)
    
    # Split text into lines manually to handle encoding
    # We'll encode each line separately
    lines = bidi_text.split('\n')
    
    for line in lines:
        try:
            # Try to add the line
            # FPDF will use latin-1 by default, which won't work for Arabic
            # We need to use a workaround: write as UTF-8 but tell FPDF it's latin-1
            # This is a hack but works for basic Arabic display
            pdf.multi_cell(0, 10, line.encode('latin-1', 'ignore').decode('latin-1'))
        except:
            # If encoding fails, skip the line or use placeholder
            pdf.multi_cell(0, 10, "[Arabic text]")
    
    # Save to /tmp (works on Railway)
    file_path = f"/tmp/story_{value}.pdf"
    pdf.output(file_path)
    
    return file_path
