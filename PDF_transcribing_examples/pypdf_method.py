# Import necessary modules
import pypdf


# Path to file
pdf_path = "T_003_43rdDamenAR98.pdf"

# Create pypdf reader
reader = pypdf.PdfReader(pdf_path)

with open("pypdf_text.txt", 'a', encoding="utf-8") as output:
	number_of_pages = len(reader.pages)

	# Loop through all pages
	for i in range(number_of_pages):
		page = reader.pages[i]
		output.write(page.extract_text())