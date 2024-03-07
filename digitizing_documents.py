from PIL import Image
import pytesseract
import fitz
import io
import json
import os
import pandas as pd
import math
import sys

REPORT_FOLDER = 'TIFpdfs'
TOTAL_PAGES_TO_PARSE = 158021
total_pages_parsed = 0
total_files_parsed = 0

# Check if there is a TIF folder
if not os.path.isdir(REPORT_FOLDER) or not os.path.isdir(os.path.join(REPORT_FOLDER, '2001')):
	print(f'There is no reports folder. Reports should be in "{REPORT_FOLDER}"')
	sys.exit()

DATABASE_FILE = 'database.csv'
COMPLETION_FILE = 'completed.json'

# Check for pre-existing data
if os.path.isfile(COMPLETION_FILE) and os.path.isfile(DATABASE_FILE):
	# Try to read it in
	try:
		with open(COMPLETION_FILE, encoding='utf8') as data:
			loaded_status = json.load(data)
			print('Found data describing completion status, loading database...', end='', flush=True)

			loaded_data = pd.read_csv(DATABASE_FILE)

			print('Database loaded')


			could_read = True

	except json.decoder.JSONDecodeError:
		print("Could not load data file")
		could_read = False

else:
	print("No completion status")
	could_read = False

# If we couldn't read in the database but it does exist, we don't want to accidentally overwrite it
if not could_read and (os.path.isfile(DATABASE_FILE) or os.path.isfile(COMPLETION_FILE)):
	print('There is an existing database/completion file that could not be read')
	print('Fix this or load a backup')
	print('To prevent overwriting, this process will not continue')
	sys.exit()

completion_status = { }
DATABASE_FIELDS = ['year', 'tif_number', 'page_num', 'block_num', 'par_num', 'line_num', 'word_num', 'left', 'top', 'width', 'height', 'conf', 'text']
pandas_database = pd.DataFrame(columns=DATABASE_FIELDS)

caught_up_to_last_savepoint = True

if could_read:
	pandas_database = loaded_data
	completion_status = loaded_status
	caught_up_to_last_savepoint = False
	print('Catching up to last savepoint...', end='', flush=True)

# Walk through all reports
for subdir, dirs, files in os.walk(REPORT_FOLDER):

	year = subdir[8:]

	if year not in completion_status:
		completion_status[year] = {}


	for file in files:

		if file not in completion_status[year]:
			completion_status[year][file] = { 'successful': [], 'failed': [] }
			

		with fitz.open(os.path.join(subdir, file)) as pdf:

			# Keep a buffer so we can add to the main dataframe in batches.
			# Doing a bunch of small additions started taking a lot of time as
			# the database got bigger.
			buffer_database = pd.DataFrame(columns=DATABASE_FIELDS)

			if not caught_up_to_last_savepoint and total_files_parsed % 40 == 0:
				print('.', end='', flush=True)

			for page_number in range(len(pdf)):

				page_key = str(page_number)

				# * Un-comment later so we can fix errors that we ignored before
				# if page_key in completion_status[year][file]['successful']:
				if page_key in completion_status[year][file]['successful'] or page_key in completion_status[year][file]['failed']:
					# Maybe redundant but I might have fucked up somewhere
					if caught_up_to_last_savepoint:
						print(f'Already processed {page_key}')
					
					continue
				elif not caught_up_to_last_savepoint:
					print('Caught up!')
					print(f'Scanning {os.path.join(subdir, file)}')
					caught_up_to_last_savepoint = True
				

				page = pdf.load_page(page_number)
				pixmap = page.get_pixmap(dpi=300)
				image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
				image_bytes = io.BytesIO()

				image.save(image_bytes, jpg_quality=100, format="PNG")
				image_bytes.seek(0)

				try:
					orientation = pytesseract.image_to_osd(Image.open(image_bytes), output_type=pytesseract.Output.DICT)
					orientation['page_num'] = page_number + 1

					# I don't want to bother with rotation right now
					if orientation['rotate'] != 0:
						print(f'{page_number + 1} has non-0 orientation')
						if page_key not in completion_status[year][file]['failed']:
							completion_status[year][file]['failed'].append(page_key)

					else:
						page_df = pytesseract.image_to_data(Image.open(image_bytes), output_type=pytesseract.Output.DATAFRAME, lang='eng')

						# Columns we don't need
						page_df = page_df.drop(['page_num', 'level'], axis=1)
						
						# Get rid of empty values
						page_df = page_df.dropna(subset=['text'])

						# Low confidence and empty values
						page_df.drop(page_df[(page_df['conf'] < 3.0) | (page_df['text'] == ' ')].index, inplace=True)

						# Round the confidence
						page_df['conf'] = page_df['conf'].apply(lambda confidence: round(confidence, 2))


						# Add our own 'year', 'tif_number', 'page_num'
						page_df = page_df.assign(year=year, tif_number=file[2:5], page_num=page_number)

						# print(page_df.to_string())
						# print(page_df)
	
						# Append the items to our buffer database
						if buffer_database.empty:
							buffer_database = page_df
						else:
							buffer_database = pd.concat([buffer_database, page_df], copy=True, ignore_index=True)

						if page_key in completion_status[year][file]['failed']:
							completion_status[year][file]['failed'].remove(page_key)

						completion_status[year][file]['successful'].append(page_key)

				except pytesseract.pytesseract.TesseractError as tess_error:

					if tess_error.status == 1:
						print(f'{page_number + 1} has "too few characters"')
					else:
						print(f'{page_number + 1} has an unknown error')

					if page_key not in completion_status[year][file]['failed']:
						completion_status[year][file]['failed'].append(page_key)

				if page_number % 30 == 0 and len(pdf) - page_number >= 30 and page_number > 1:
					with open(COMPLETION_FILE, 'w', encoding='utf-8') as f:
						json.dump(completion_status, f, ensure_ascii=False)

						# Merge the buffer to the main database
						pandas_database = pd.concat([pandas_database, buffer_database], copy=False, ignore_index=True)
						buffer_database = pd.DataFrame(columns=DATABASE_FIELDS)
						
						pandas_database.to_csv(DATABASE_FILE, index=False)
						
						print('Updated storage')

			if caught_up_to_last_savepoint:
				with open(COMPLETION_FILE, 'w', encoding='utf-8') as f:
					json.dump(completion_status, f, ensure_ascii=False)

					# Merge the buffer to the main database
					pandas_database = pd.concat([pandas_database, buffer_database], copy=False, ignore_index=True)
					buffer_database = pd.DataFrame(columns=DATABASE_FIELDS)
					
					pandas_database.to_csv(DATABASE_FILE, index=False)
					
					print('Updated storage')

				total_pages_parsed += len(pdf)
				percent_through = total_pages_parsed / TOTAL_PAGES_TO_PARSE * 100
				percent_through = math.floor(percent_through)
				print(f'{percent_through:02d}% complete. {total_pages_parsed} pages parsed')
			else:
				total_pages_parsed += len(pdf)

			# print(document_data)

print('Done')