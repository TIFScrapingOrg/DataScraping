from PIL import Image
import pytesseract
import fitz
import time
import io
import re
import sys

start_time = time.time()

# Our test pdf
pdf_path = "PDF_transcribing_examples/T_003_43rdDamenAR98.pdf"


with fitz.open(pdf_path) as pdf:

	for page_number in range(len(pdf)):

		# We want to use an in-memory version of an image instead of
		# going through the process of converting then saving it to the
		# filesystem

		# This section of the code uses PyMuPDF to turn each page into
		# it's full resolution image form
		page = pdf.load_page(page_number)
		pixmap = page.get_pixmap(dpi=300)
		image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
		image_bytes = io.BytesIO()

		image.save(image_bytes, jpg_quality=100, format="PNG")
		image_bytes.seek(0)

		# Now use that image in tesseract
		pdf_page_string = pytesseract.image_to_string(Image.open(image_bytes))
		
		financialsRegExTrigger = re.compile('statements of[ ]?(?:revenue|expenditure|change in fund balance)',re.IGNORECASE)

		if financialsRegExTrigger.search(pdf_page_string):
			print("-----" + str(page_number) + "-----")
			print(pdf_page_string)
			sys.exit()


print(f'Time taken: {time.time - start_time} seconds')