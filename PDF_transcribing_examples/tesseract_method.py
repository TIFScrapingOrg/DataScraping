# Import necessary modules
import io
from PIL import Image

# Installing pytesseract involves installing the actual tesseract module from
# google and also requires pillow
from pytesseract import pytesseract

# Use PyMuPDF to turn PDF's into images
import fitz


# Path to pdf
pdf_path = "T_003_43rdDamenAR98.pdf"

with open("tesseract_text.txt", 'a', encoding="utf-8") as output, fitz.open(pdf_path) as pdf:

	# Loop through all pages
	for page_number in range(len(pdf)):
		page = pdf.load_page(page_number)
		pixmap = page.get_pixmap()

		image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
		image_bytes = io.BytesIO()

		# We would like to just use an in memory version of the page images.
		# This fixes file ordering shenanigans and also makes the process
		# significantly faster
		image.save(image_bytes, jpg_quality=100, format="PNG")
		image_bytes.seek(0)
		text = pytesseract.image_to_string(Image.open(image_bytes))
		
		output.write(text)