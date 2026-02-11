from fpdf import FPDF
import os

def create_pdf(image_paths, output_path):
    """
    Combines a list of image paths into a single PDF.
    """
    try:
        # Use custom square size 210x210 mm
        pdf = FPDF(unit='mm', format=(210, 210))
        for img_path in image_paths:
            # Add a new page for each image
            pdf.add_page()
            # Standard square size 210 x 210 mm.
            # We'll fill the square page with the image
            pdf.image(img_path, x=0, y=0, w=210, h=210)
            
        pdf.output(output_path)
        return output_path
    except Exception as e:
        print(f"Error creating PDF: {e}")
        return None
