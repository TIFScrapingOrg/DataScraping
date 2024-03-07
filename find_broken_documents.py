import fitz
import io
import os
import sys

report_folder = 'TIFpdfs'

pages_total = 0

for subdir, dirs, files in os.walk(report_folder):

	for file in files:

		try:

			with fitz.open(os.path.join(subdir, file)) as pdf:

				if len(pdf) <= 1:

					print(f'{os.path.join(subdir, file)} has 0 pages')

				pages_total += len(pdf)

		except fitz.FileDataError as file_error:

			# As far as I'm aware, the only time this error occurs is when the
			# file is broken
			print(f'{os.path.join(subdir, file)} is broken')

print(pages_total)

print('Complete')