from fpdf import FPDF
import os

def create_pdf(image_paths, output_path):
    """
    Combines a list of image paths into a single PDF.
    """
    try:
        pdf = FPDF()
        for img_path in image_paths:
            # Add a new page for each image
            pdf.add_page()
            # FPDF uses points as default unit (1pt = 1/72 inch). 
            # Standard A4 size is roughly 210 x 297 mm.
            # We'll stretch the image to fit the page
            pdf.image(img_path, x=0, y=0, w=210, h=297)
            
        pdf.output(output_path)
        return output_path
    except Exception as e:
        print(f"Error creating PDF: {e}")
        return None
