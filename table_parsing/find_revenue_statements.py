import sys
import pandas as pd
from difflib import SequenceMatcher
import os
import re
import fitz
import io
from PIL import Image, ImageDraw
from handle_formats.process_report_test import find_table
from handle_formats.cell_class import PRINT_TABLE
import pickle
import time

DATABASE_FIELDS = ['year', 'tif_number', 'page_num', 'block_num', 'par_num', 'line_num', 'word_num', 'left', 'top', 'width', 'height', 'conf', 'text']
COMPLETION_STATUS_CSV = 'butter_json.csv'
PARSED_PDFS_DIR = '../parsed_pdfs'

# Load in completion status of files and their pages
completion_csv = pd.read_csv(COMPLETION_STATUS_CSV)
completion_csv.drop(labels=['id'], axis=1, inplace=True)

page_status = {}
for _, row in completion_csv.iterrows():

	key = f"{row['year']}_{row['tif_number']}"

	if key not in page_status:
		page_status[key] = { 'successful': [], 'failed': [] }
		page_status[key]['year'] = row['year']
		page_status[key]['tif_number'] = row['tif_number']

	if row['successful'] == 1:
		if isinstance(row['page_list'], str):
			page_status[key]['successful'] = row['page_list'].split(',')
	else:
		if isinstance(row['page_list'], str):
			page_status[key]['failed'] = row['page_list'].split(',')

# Check to make sure all of the entries in the page_status dictionary are
# actually in the parsed_pdfs folder
for pair in page_status:
	if not os.path.isfile(os.path.join(PARSED_PDFS_DIR, f'{pair}.csv')):
		print('Missing entry', pair)

# We want to loop through each year_tif pair and scan through all of the text in
# each document

# Realistically though we only want to see the top 500px worth of content.

# Perform the search query then when we get a match query the rest of the page

SIMILARITY_THRESHOLD = 0.7

def is_finance(query_vector, log=False):
	flags_to_watch = {
		# 'combined': False,
		'expenditures': False,
		'balance': False,
		'revenue': False,
		# 'schedule': False
	}

	# Loop over all text in the query bag and compare it to our dict
	for word in query_vector:
		for buzz_word in flags_to_watch:
			similar_ratio = SequenceMatcher(None, word.lower(), buzz_word.lower())

			if similar_ratio.ratio() > SIMILARITY_THRESHOLD:
				flags_to_watch[buzz_word] = True
				break
	if log:
		print(' '.join(query_vector))
		print(flags_to_watch)

	# If not all the flags are met return False
	return all(flag for flag in flags_to_watch.values())

IGNORE_STRING_1 = 'no tax increment project expenditures' # First seen 1997
IGNORE_STRING_2 = 'no tax increment expenditures within the project area' # First seen 1998_4
IGNORE_STRING_3 = 'no tax increment expenditures or cumulative deposits over' # First seen 2002_10

def is_ignored(query_vector):
	# Join all elements of vector
	doc_string = ' '.join(query_vector)
	doc_string = doc_string.lower()

	match_ignore_1 = re.search(IGNORE_STRING_1, doc_string) is not None
	match_ignore_2 = re.search(IGNORE_STRING_2, doc_string) is not None
	match_ignore_3 = re.search(IGNORE_STRING_3, doc_string) is not None

	return match_ignore_1 or match_ignore_2 or match_ignore_3

pages_we_skip = 0

SKIP_LIST = [
	'1998_29',	# This document seems to just be the same thing
				# repeated twice and just has estimated costs
	'1998_43',	# Same thing as 1998_29. They didn't include the report
	'2008_162',	# There is no report but the field is "increment.expenditures"
				# as opposed to "increment expenditures" so it doesn't get
				# caught in the ignore string
	'2010_132',	# Nothing seems to have happened in this TIF this year, but
				# it is not filled out in a conventional way
	'2010_143',	# ditto
	'2010_170',	# ditto ditto, information not present
	'2010_173', # ditto ditto ditto
	'2010_168', # ditto...
	'2010_171',	# ditto. No deposits >= 100_000
	'2011_159', # Nothing over 100_000,
	'2011_162',
	'2011_168',
	'2011_170',
	'2011_173',
	'2011_174',
	'2012_132',
	'2012_168',
	'2012_170',
	'2012_173',
	'2012_174',
	'2012_175',
	'2013_168',
	'2013_170',
	'2013_173',
	'2013_174',
	'2013_175',
	'2014_168',
	'2014_170',
	'2014_173',
	'2014_174',
	'2014_175',
	'2014_176',
	'2014_177',
	'2014_178',
	'2015_168',
	'2015_170',
	'2015_174',
	'2015_175',
	'2015_176',
	'2016_168',
	'2016_170',
	'2016_175',
	'2016_179',
	'2016_180',
	'2017_170',
	'2018_182',
	'2018_181',
	'2019_183',
	'2019_184',
	'2022_186',
]

MANUAL_CORRECTIONS = {
	'1998_31': 24,	# Line through top of page disrupts recognition
	'1998_37': 90,	# The word 'revenues' was not scraped from the pdf
	'1999_1': 11,	# ditto
	'2000_1': 10,	# Top section skipped
	'2000_3': 10,	# ditto
	'2000_2': 9,	# ditto ditto
	'2000_4': 10,	# ditto ditto ditto
	'1998_3': 18,	# Two matches. Second match is 1997 report
	'2007_2': 14,	# Two matches. Second is only Governmental funds
	'2007_4': 14,	# ditto
	'2007_1': 14,
	'2007_3': 14,
	'2007_6': 14,
}

HAND_FILLED = {
	'1998_44': 51,	# This report is a mess and frankly I'm not sure
					# if this is even right
	'1999_3': 23,	# The table was scanned, put in a field, then the
					# page was scanned
	'1999_4': 11,	# A lot of words got missed. Flagging this because
					# a lot of numbers were messed up during
					# pre-processing too
	'1999_6': 11,	# Top section was missed. Flagged because numbers bad
	'2020_182': 5,	# Someone at the council is just lazy. Not formatted
	'2010_162': 7,	# Similar to 2010_143 and 132. The information does
					# seem to be there though
	'2010_159': 7,	# ditto
	'2012_159': 7,	# No exchanges >= 100_000 but data still there
	'2012_162': 7,	# ditto
	'2013_159': 7,
	'2013_162': 7,
	'2014_159': 5,
	'2015_178': 6,
	'2019_182': 5,
	'2003_14': 120,	# So many matches. This appears to be in different
					# format from previous 2 pages though.
	'2016_14': [13, 14], # It spans 2 pages

	'2000_15': 23, # Not the nice form
	'2007_12': 14, # Also not nice
	'2008_12': 14, # Just messed up
	'2009_160': 15, # Didn't recognize column
	'2009_166': 15, # Didn't recognize column. It's just got 1's anyways,
	'2013_42': 31, # OCR put a giant line across things which messed up column recognition
	# I'm lazy at fixing
	'1997_14': 115,
	'2013_147': 540, # OCR hallucinated some messed up stuff
	# '2002_54': 13,
	# '2004_89': 13, # Literally same scenario as above
	'1999_5': 11, # The page is slanted and lines do not line up
	'1999_11': 11, # OCR missed column headers
	'1998_14': 35, # This is just a nightmare to parse
	'1999_14': 10, # OCR missed investment income row
	'1999_20': 11, # Tilted scan
	'1999_21': 11, # ditto
	'1999_53': 11, # ditto ditto
	'1999_56': 11, # ditto ditto ditto
	'2000_14': 15, # OCR missed fields
	'1999_44': 11, # end of year fund is mangled
	'2001_69': 23, # Iffy, I'll just make the call to manually do it
	'2005_7': 13, # Giant line messes things up
	'2005_17': 13, # Another line
	'2006_30': 13, # Slanted
	'2006_102': 13, # Slanted
	'2007_90': 14, # Total expenditures missed
	'2007_138': 14, # Missed ALL expenditures!
	'2007_137': 14, # ditto
	'2008_141': 14, # Expenditures missed
	'2009_158': 15, # Fund balance end of year not read. ALthough, it's a new tif, so it would be easy to calculate
	'2009_162': 15, # ditto
}

HAS_NO_EXPENDITURES = [
	"2006_139",
]
HAS_NO_REVENUES = [
	"2010_169",
	'2012_7'
]

BROKEN = [
	'2014_53',
]

ADJUSTMENT_EMPTY = {
	"2008_50": 14,
	"2009_113": 14,
	'2015_177': 29,
	"2017_154": 32
}

def find_stuff(pair):

	# Skip 1999-2001, these seem to be a different breed
	# if pair[0:4] in ['1999', '2000', '2001'] :
	# 	return False

	# Load in the associated TIF csv
	csv_path = os.path.join(PARSED_PDFS_DIR, f'{pair}.csv')
	tif_text = pd.read_csv(csv_path, header=None, names=DATABASE_FIELDS)

	# Only grab top 550 px
	top_section = tif_text[tif_text['top'] <= 550]

	# Sort all words so that they appear in order
	top_section.sort_values(['page_num', 'block_num', 'line_num', 'word_num'])

	# Get a list of all the pages that have words in the top section
	pages = top_section['page_num'].unique()

	matched_pages = []

	for page in pages:

		page_df = top_section[top_section['page_num'] == page]
		page_vector = page_df['text']

		if is_finance(page_vector.to_list()):
			matched_pages.append(page)


	# These all have exactly 2 matches (when not 0)
	if pair[0:4] in ['2007', '2008', '2009'] and len(matched_pages) == 2:
		matched_pages = [matched_pages[0]]
		print('Corrected', matched_pages)
		return [matched_pages[0], tif_text[tif_text['page_num'] == int(matched_pages[0])]]

	elif len(matched_pages) > 1:
		print('Too many pages')
		return False

	if len(matched_pages) > 0:
		return [matched_pages[0], tif_text[tif_text['page_num'] == int(matched_pages[0])]]

	resolved = False
	
	pages = page_status[pair]['successful']

	# Check the contents of every page and look for the string 'no city
	# contracts related to the project area'
	for page in pages:

		page_df = tif_text[tif_text['page_num'] == int(page)]
		page_vector = page_df['text']

		if is_ignored(page_vector.to_list()):
			print(f'gotta killer. Page {page}')
			if pair[0:4] in ['1999', '2000', '2001'] :
				continue
			resolved = True
			break

	if resolved:
		return False

	# The statement of revenues might be lower down on the page. Not all reports
	# actually follow the same format in a year so a document like this needs to
	# be flagged for manual review.
	top_section = tif_text[tif_text['top'] <= 750]

	# Sort all words so that they appear in order
	top_section.sort_values(['page_num', 'block_num', 'line_num', 'word_num'])

	# Get a list of all the pages that have words in the top section
	pages = top_section['page_num'].unique()

	for page in pages:

		page_df = top_section[top_section['page_num'] == page]
		page_vector = page_df['text']

		if is_finance(page_vector.to_list()):
			matched_pages.append(page)

	if len(matched_pages) > 1:
		print('hey too many!')

	if len(matched_pages) > 0:
		resolved = True
		print(pair, matched_pages)
		return [matched_pages[0]]
	
	if pair[0:4] in ['1999', '2000', '2001'] :
		return False

	if not resolved:
		print(pages)

		print(pair)

		print("Couldn't resolve")

total_tried = 0
fails = 0
skip = False

pickle_timer = 120
pickle_reset = 120

unique_rev_fields = pd.Series()

if os.path.exists('known_pages.p'):
	print('Found pickle describing known_pages')
	with open('known_pages.p', 'rb') as fp:
		known_pages = pickle.load(fp)
else:
	known_pages = {}
time.sleep(1.5)
print('Building suspense...')
time.sleep(1.5)
print('...')
time.sleep(2)
print('Suspense sufficiently built. Lesgo!')
time.sleep(1.5)

for pair in page_status:

	if pair in BROKEN:
		continue

	# if not skip:
	# 	sys.exit()

	if pair == '2016_87':
		skip = False

	if skip:
		continue
	

	print(pair)

	# I'm organizing these if statements like this because if I correct an
	# error, I want it to actually show up
	if pair in SKIP_LIST:
		continue
		# return False <- poi = False
	if pair in HAND_FILLED:
		continue
		# return False <- poi = False
	if pair in ADJUSTMENT_EMPTY:
		continue
		# poi = [ADJUSTMENT_EMPTY[pair]]
	if pair in MANUAL_CORRECTIONS:
		poi = [MANUAL_CORRECTIONS[pair]]
	elif pair in known_pages:
		poi = known_pages[pair]
	else:
		poi = find_stuff(pair)
		pickle_timer -= 1


	if pickle_timer == 0:
		pickle_timer = pickle_reset
		# Write known_pages
		# Code adapted from https://stackoverflow.com/a/7100202/7362680
		print('Writing pickle')
		with open('known_pages.p', 'wb') as fp:
			pickle.dump(known_pages, fp, protocol=pickle.HIGHEST_PROTOCOL)
		print('Pickle finished writing')
	
	
	known_pages[pair] = poi

	if poi is False:
		continue

	total_tried += 1

	print(poi[0])

	csv_path = f'../parsed_pdfs/{pair[0:4]}_{pair[5:]}.csv'

	table = find_table(csv_path, poi[0], int(pair[0:4]), int(pair[5:]))

	if table is False:
		print(pair, poi[0])
		input('Waiting to continuer...')
		fails += 1
		continue
	# elif PRINT_TABLE:
	# 	print(table)

	if len(table.columns) == 2 or len(table.columns) > 5:
		print('Too many/few columns')
		print(table)
		sys.exit()

	continue

	# Collect unique revenue fields
	labels = table['labels']

	# We just want
	# 	property tax
	# 	transfers in
	#	total expenditures
	#	transfers out
	#	re-distribution
 
	# There is also
	# 	Administration costs
	#	Finance costs
	#	Bank names
	# But we aren't focused on getting those right now
	
	

	expenditure_pattern = re.compile(""
		"[\.:|;‘_]*\s*expenditures:?$|"
		"[\.:|;‘_]*\s*expenditures\/expenses?:?$|"	# Introduced 2002_1
		"Expenditu\. 2s$|" # Edge case 1997_27
		"Expenditures/expenses: ." # Edge case 2007_46
	"", re.IGNORECASE)

	revenue_pattern = re.compile(""
		"[\.:|;‘_\s-]*revenues?[:\.,\s-]*$" # . at the end is from 2004_29 where there is a speck on the page
	"", re.IGNORECASE)

	total_rev_pattern = re.compile(""
		"[\.:|;‘_\s-]*to[ti]a[l!] reven[u\s]es\s*[:-]*$|"
		"tota[l!] revenues \.$|" # 2004_44. Speck
		"Tota[l!] reven e[sn]$" # 2008_14 and 2006_15
	"", re.IGNORECASE)

	total_expend_pattern = re.compile(""
		".*tota[l!]\sexpenditures.*$"
	"", re.IGNORECASE)

	rev_after_expend_pattern = re.compile(""
		".*(excess\s*)?(of\s*)?(expen?ditures|revenues?)\s*(over|and|after|under)\s*(expen?ditures|revenues?).*$|"
		".*revenues?\s*over(\s*\(under\))?\s*expenditures[$,Ss\-_\'=~\s.—§©:]*$"
	"", re.IGNORECASE)

	if pair in HAS_NO_REVENUES:
		continue

	# Find Revenues
	rev_loc = -1
	total_rev_loc = -1
	expend_loc = -1
	total_exp_loc = -1
	rev_p_exp_loc = -1
	for index, value in labels.items():
		if rev_loc == -1 and re.match(revenue_pattern, value):
			rev_loc = index
		elif total_rev_loc == -1 and re.match(total_rev_pattern, value):
			total_rev_loc = index
		elif expend_loc == -1 and re.match(expenditure_pattern, value):
			expend_loc = index
		elif total_exp_loc == -1 and re.match(total_expend_pattern, value):
			total_exp_loc = index
		elif rev_p_exp_loc == -1 and re.match(rev_after_expend_pattern, value):
			rev_p_exp_loc = index

	IGNORE_FOR_EXPENDITURE_TESTING = [
		'1997_28',
		'2005_25', # Numbers are correct, there is just an extra dash
		'2007_14', # Extra stuff
		'2007_50', # ditto
		'2008_14', # Extra stuff BUT will not match total revenues maybe
		'2008_154', # Numbers right, just extra stuff
		'2009_120', # Expenditure items missing, but total is still there. Numbers correct
	]
	
	# We've iterated everywhere

	# if rev_loc == -1:
	# 	print("Couldn't find 'revenues'")
	# 	print(table)
	# 	sys.exit()
 
	if pair in IGNORE_FOR_EXPENDITURE_TESTING or pair in HAS_NO_EXPENDITURES:
		continue

	if expend_loc == -1:
		print("Couldn't find expenditures")
		print(table)
		print(f'Expend: {expend_loc},	Total Expenditures: {total_exp_loc},	rev/exp: {rev_p_exp_loc}')
		correct_loc = input('Where is it?')
		if correct_loc > 0:
			expend_loc = correct_loc
		else:
			continue
		# sys.exit()

	if rev_p_exp_loc == -1:
		print("Couldn't find revenues after expenditures")
		print(table)
		print(f'Expend: {expend_loc},	Total Expenditures: {total_exp_loc},	rev/exp: {rev_p_exp_loc}')
		correct_loc = input('Where is it?')
		if correct_loc > 0:
			rev_p_exp_loc = correct_loc
		else:
			continue
		# sys.exit()

	if total_exp_loc == -1 and rev_p_exp_loc - expend_loc > 2:
		print('The difference between net and expends is too much')
		print(table)
		print(f'Expend: {expend_loc},	Total Expenditures: {total_exp_loc},	rev/exp: {rev_p_exp_loc}')
		input('Waiting...')
		# sys.exit()

	# print(f'Revenues: {rev_loc},\tTotal Revenues: {total_rev_loc},\tExpenditures: {expend_loc}')

	# if total_rev_loc == -1 and expend_loc - rev_loc > 2 and not pair in HAS_NO_EXPENDITURES:
	# 	print('The difference between revenues and expends is too much')
	# 	print(table)
	# 	sys.exit()


	if total_exp_loc == -1:
		# Only grab the one field after rev_loc
		# print('No total revenues')
		add_these = labels.iloc[[expend_loc+1]]
	else:
		# Grab everything in the series from rev to total_rev
		# print('Using Total revenues')
		add_these = labels.iloc[(expend_loc + 1) : total_exp_loc]

	diffs = pd.Series(list(set(add_these) - set(unique_rev_fields)))
	# print(diffs)
	# print(unique_rev_fields)
	# input('Waiting...')
	if len(diffs) > 0:
		print(f'There are {len(diffs)} new unique fields')
		print(diffs)
		print(table)
		add_them = input('Add them? (Y/N)')
		if add_them.lower() != 'n':
			unique_rev_fields = pd.concat([unique_rev_fields, diffs], ignore_index=True)
		

print('hWriting pickle')
with open('known_pages.p', 'wb') as fp:
	pickle.dump(known_pages, fp, protocol=pickle.HIGHEST_PROTOCOL)
print('Pickle finished writing')
	
# unique_rev_fields.drop_duplicates(inplace=True)
# print(f'There are {len(unique_rev_fields)} unique fields')
# print(unique_rev_fields.to_string())