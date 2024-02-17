# Import necessary modules
import fitz
# Idk why it's called fitz


# Path to file
pdf_path = "T_003_43rdDamenAR98.pdf"

with fitz.open(pdf_path) as doc, open("PyMuPDF_text.txt", 'a', encoding="utf-8") as output:

	# Loop through all pages
	for page in doc:
		output.write(page.get_text())