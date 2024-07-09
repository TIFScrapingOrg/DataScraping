print('Loading modules...', end='', flush=True)

import sys
import os
import fitz
import requests
import pandas as pd

# Image processing modules
from PIL import Image
import pytesseract
import io
import json
import time

print('Modules loaded')

COLLECTION_NAME = 'TIFpdfs'
FINISHED_NAME = 'finished'
DATABASE_FIELDS = ['year', 'tif_number', 'page_num', 'block_num', 'par_num', 'line_num', 'word_num', 'left', 'top', 'width', 'height', 'conf', 'text']
DATABASE_DTYPES = {
	'year': int,
	'tif_number': int,
	'page_num': int,
	'block_num': int,
	'par_num': int,
	'line_num': int,
	'word_num': int,
	'left': int,
	'top': int,
	'width': int,
	'height': int,
	'conf': float,
	'text': str
}
DATABASE_DEFAULT = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 99.99, 'zilch']]

MAX_NETWORK_FAILS = 10
network_fails = 0

work_requested = []
looking_at = []
url_list = []

def check_broken(save_path):
	try:
		with fitz.open(save_path) as pdf:
			if len(pdf) == 0:
				return True

	except fitz.FileDataError as file_error:
		return True
		
	return False

def download_pdf(url, year, save_path, ignore_corrupted=False, dont_redownload=False):

	# Check to see if we already downloaded it
	if os.path.exists(save_path):
		print("Already have, skipping download")

		# Check if it's broken
		is_broken = not ignore_corrupted and check_broken(save_path)
		if is_broken:
			print(f'Download is corrupted, downloading again')
			os.remove(save_path)
			download_pdf(url, year, save_path, True)

			is_broken = check_broken(save_path)
			if is_broken:
				# Something fishy is going on
				print(f'Cannot download {url}')
				os.remove(save_path)
				return False
			else:
				return True
		else:
			return True
		
	if not os.path.isdir(os.path.join(COLLECTION_NAME, year)):
		os.makedirs(os.path.join(COLLECTION_NAME, year))

	try:
		response = requests.get(url, stream=True)

		with open(save_path, 'wb') as pdf_file:
			for chunk in response.iter_content(chunk_size=1024):
				if chunk:
					pdf_file.write(chunk)

		# Check to see if the file is corrupted
		is_broken = not ignore_corrupted and check_broken(save_path)

		# Try again if broken
		if is_broken:
			print(f'Corrupted download of {url}, retrying')
			os.remove(save_path)
			download_pdf(url, year, save_path, True)

			is_broken = check_broken(save_path)
			if is_broken:
				# Something fishy is going on
				print(f'Cannot download {url}')
				os.remove(save_path)
				return False
			else:
				return True
		else:
			return True
		
	except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:

		if dont_redownload:
			print(f'Cannot download {url}')
			return False
		
		print('Error while downloading document. Waiting a bit then trying again')
		time.sleep(10)
		
		return download_pdf(url, year, save_path, ignore_corrupted=ignore_corrupted, dont_redownload=True)
		
	except Exception as e:
		print(f'General error while getting work: {e}')

		if dont_redownload:
			print(f'Cannot download {url}')
			return False
		
		print('Waiting a bit then trying again')
		time.sleep(10)
		
		return download_pdf(url, year, save_path, ignore_corrupted=ignore_corrupted, dont_redownload=True)

def upload_done_documents(json_path, csv_path, year_tif_pairs):

	global network_fails
	
	try:

		URL = 'http://noahbaxley.com/tiftastic/send_work.php'

		# bread = [[1998, 2]]

		year_tif_pairs = [[year, number.lstrip('0')] for year, number in year_tif_pairs]

		with open(csv_path, 'rb') as cheese, open(json_path, 'rb') as butter:
			files = {
				'butter': butter,
				'cheese': cheese,
			}
			data = {
				'bread': str(year_tif_pairs),
			}
			response = requests.post(URL, data=data, files=files)
			print(response.text)
			if response.status_code == 200:
				if response.text == 'You have redundant data!':
					print('Files either took too long or were incorrectly assigned')
					print('Is this device worth keeping alive?')
				else:
					print("Files uploaded successfully!")

				network_fails = 0

			else:
				print(f"Failed to upload file. Status code: {response.status_code}")
				print(response.text)

				network_fails += 1

				if network_fails > MAX_NETWORK_FAILS:
					print('Network fails exceeded threshold, stopping')
					sys.exit()
				
				# Just try sending it again and hope it doesn't fail
				time.sleep(45)
				upload_done_documents(json_path, csv_path, year_tif_pairs)


	except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:

		network_fails += 1

		if network_fails > MAX_NETWORK_FAILS:
			print('Network fails exceeded threshold, stopping')
			sys.exit()
		
		# Just try sending it again and hope it doesn't fail
		print('There was a connection error. Wait a bit, then we\'ll attempt to resend')
		time.sleep(45)
		upload_done_documents(json_path, csv_path, year_tif_pairs)
	
	except Exception as e:
		network_fails += 1
		print(f'Exception when uploading: {e}')
		print('Continuing, but this loop was not tracked')

def request_work():

	global network_fails

	try:
		URL = 'http://noahbaxley.com/tiftastic/request_work.php'

		response = requests.get(URL)
		if response.status_code == 200:
			json_data = response.json()
			# Structure is
			# [
			#	year
			#	tif_number
			#	url
			# ]
			if len(json_data) == 0:
				print('There is nothing left to process')
				sys.exit()

			network_fails = 0

			return json_data

		else:
			print('Failed to fetch data:', response.status_code)
			network_fails += 1
			print('Waiting a bit, then reattempting to request')
			time.sleep(45)
			return request_work()

	except (requests.ConnectionError, requests.Timeout, requests.HTTPError) as e:
		
		network_fails += 1

		if network_fails > MAX_NETWORK_FAILS:
			print('Network fails exceeded threshold, stopping')
			sys.exit()
		
		# Just try sending it again and hope it doesn't fail
		print('There was a connection error. Waiting a bit, then reattempting to request')
		time.sleep(45)
		return request_work()

	except Exception as e:
		print(f'General error while getting work: {e}')

		network_fails += 1

		if network_fails > MAX_NETWORK_FAILS:
			print('Network fails exceeded threshold, stopping')
			sys.exit()
		
		# Just try sending it again and hope it doesn't fail
		print('Waiting a bit, then reattempting to request')
		time.sleep(45)
		return request_work()


# Make TIF directory if it does not exist
if not os.path.isdir(COLLECTION_NAME):
	os.makedirs(COLLECTION_NAME)

# Make finished directory if it does not exist
if not os.path.isdir(FINISHED_NAME):
	os.makedirs(FINISHED_NAME)

RUNNING = True
loop_count = 0

while RUNNING:

	loop_count += 1
	print(f'Loop {loop_count}')

	# Start off by requesting work
	work_requested = request_work()

	print(work_requested)

	# Create this request's stuff
	completion_status = { }
	pandas_database = pd.DataFrame(data=DATABASE_DEFAULT, columns=DATABASE_FIELDS)
	year_tif_pairs = []


	year = str(work_requested[0]['year'])
	tif_number = str(work_requested[0]['tif_number'])
	url = work_requested[0]['url']

	# Download the document
	save_path = os.path.join(COLLECTION_NAME, str(year), str(tif_number)) + '.pdf'
	successful_download = download_pdf(url, year, save_path)

	if not successful_download:
		continue

	year_tif_pairs.append([year, tif_number])

	# Scan it
	print(f'Scanning {year}/{tif_number}')

	if year not in completion_status:
		completion_status[year] = { } 
	
	completion_status[year][tif_number] = { 'successful': [], 'failed': [] }

	try:
		with fitz.open(save_path) as pdf:
			for page_number in range(len(pdf)):

				page = pdf.load_page(page_number)
				print(f'Scanning page {page_number}')
				pixmap = page.get_pixmap(dpi=300)
				image = Image.frombytes('RGB', [pixmap.width, pixmap.height], pixmap.samples)
				image_bytes = io.BytesIO()

				image.save(image_bytes, jpg_quality=100, format="PNG")
				image_bytes.seek(0)

				try:
					orientation = pytesseract.image_to_osd(Image.open(image_bytes), output_type=pytesseract.Output.DICT)
					orientation['page_num'] = page_number + 1

					# I don't want to bother with rotation right now
					if orientation['rotate'] != 0:
						print(f'{page_number + 1} has non-0 orientation')
						if page_number not in completion_status[year][tif_number]['failed']:
							completion_status[year][tif_number]['failed'].append(page_number)

					else:
						page_df = pytesseract.image_to_data(Image.open(image_bytes), output_type=pytesseract.Output.DATAFRAME, lang='eng')

						# Columns we don't need
						page_df = page_df.drop(['page_num', 'level'], axis=1)
						
						# Get rid of empty values
						page_df = page_df.dropna(subset=['text'])

						# Low confidence and empty values
						page_df.drop(page_df[(page_df['conf'] < 3.0) | (page_df['text'].str.isspace())].index, inplace=True)
						# page_df.drop(page_df[page_df['text'] == '|'].index, inplace=True)

						# Round the confidence
						page_df['conf'] = page_df['conf'].apply(lambda confidence: round(confidence, 2))


						# Add our own 'year', 'tif_number', 'page_num'
						page_df = page_df.assign(year=int(year), tif_number=int(tif_number), page_num=page_number)

						# if pandas_database.empty:
						# 	pandas_database = page_df
						# else:
						pandas_database = pd.concat([pandas_database, page_df], copy=True, ignore_index=True)

						if page_number in completion_status[year][tif_number]['failed']:
							completion_status[year][tif_number]['failed'].remove(page_number)

						completion_status[year][tif_number]['successful'].append(page_number)
						continue

				except pytesseract.pytesseract.TesseractError as tess_error:

					if tess_error.status == 1:
						print(f'{page_number + 1} has "too few characters"')
					else:
						print(f'{page_number + 1} has an unknown error')

					if page_number not in completion_status[year][tif_number]['failed']:
						completion_status[year][tif_number]['failed'].append(page_number)
					continue
				
				except Exception as e:

					print(f'General exception: {e} on page {page_number}')
					
					if page_number not in completion_status[year][tif_number]['failed']:
						completion_status[year][tif_number]['failed'].append(page_number)
					continue

	except fitz.FileDataError as e:
		print(e)
		print(f'Couldn\'t open {save_path}')


	if len(year_tif_pairs) == 0:
		print('Nothing to submit')
		continue

	# Turn in our work
	print('*****Sending work to server! Please do not interrupt!*****')
	time.sleep(1.5)
	print('...')

	json_path = os.path.join(FINISHED_NAME, f'{year}_{tif_number}.json')
	csv_path = os.path.join(FINISHED_NAME, f'{year}_{tif_number}.csv')

	# Write the data to files on the local system
	with open(json_path, 'w', encoding='utf-8') as j:
		json.dump(completion_status, j, ensure_ascii=False)

	# Drop the first placeholder row
	writeable_database = pandas_database.iloc[1:]
	writeable_database.to_csv(csv_path, index=False, header=False)

	# Send the work
	upload_done_documents(json_path, csv_path, year_tif_pairs)

	print('*****Work submitted. Feel free to stop*****')


print('Done')