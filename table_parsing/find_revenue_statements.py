print('Loading...')

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
import math
from handle_formats.statement import Statement

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

	# 1999 Section
	"1999_10", # No finance
	"1999_49", # No finance
	"1999_50", # No finance
	"1999_57", # No finance
	"1999_60", # No finance
	"1999_62", # No finance
	"1999_64", # No finance
	"1999_67", # No finance
	"1999_68", # No finance
	"1999_69", # No finance
	"1999_71", # No finance
	"1999_73", # No finance
	"1999_74", # No finance
	"1999_75", # No finance
	"1999_76", # No finance
	"1999_77", # No finance
	"1999_78", # No finance
	"1999_79", # No finance
	"1999_141", # No finance

	# 2000 Section
	"2000_10", # No finance
	"2000_12", # No finance
	"2000_49", # No finance
	"2000_51", # No finance
	"2000_60", # No finance
	"2000_62", # No finance
	"2000_68", # No finance
	"2000_76", # No finance
	"2000_78", # No finance
	"2000_80", # No finance
	"2000_81", # No finance
	"2000_82", # No finance
	"2000_83", # No finance
	"2000_84", # No finance
	"2000_85", # No finance
	"2000_87", # No finance
	"2000_89", # No finance
	"2000_90", # No finance
	"2000_91", # No finance
	"2000_92", # No finance
	"2000_93", # No finance
	"2000_94", # No finance
	"2000_96", # No finance
	"2000_98", # No finance
	"2000_99", # No finance
	"2000_100", # No finance
	"2000_101", # No finance
	"2000_102", # No finance
	"2000_103", # No finance

	# 2001 section
	"2001_10", # No finance
	"2001_81", # No finance
	"2001_83", # No finances
	"2001_85", # No finances
	"2001_90", # No finance
	"2001_99", # No finance
	"2001_103", # No finance
	"2001_104", # No finance
	"2001_105", # No finance
	"2001_106", # No finance
	"2001_107", # No finance
	"2001_108", # No finance
	"2001_109", # No finance
	"2001_110", # No finance
	"2001_111", # No finance
	"2001_112", # No finance
]

MANUAL_CORRECTIONS = {
	'1998_31': 24,	# Line through top of page disrupts recognition
	'1998_37': 90,	# The word 'revenues' was not scraped from the pdf
	'1998_3': 18,	# Two matches. Second match is 1997 report
	'2007_2': 14,	# Two matches. Second is only Governmental funds
	'2007_4': 14,	# ditto
	'2007_1': 14,
	'2007_3': 14,
	'2007_6': 14,

	# 1999 section
	"1999_1": 11,
	"1999_2": 11,
	"1999_7": 10,
	"1999_13": 11,
	"1999_15": 11,
	"1999_16": 11,
	"1999_17": 11,
	"1999_18": 11,
	"1999_19": 11,
	"1999_22": 11,
	"1999_24": 11,
	"1999_25": 11,
	"1999_26": 11,
	"1999_27": 11,
	"1999_28": 11,
	"1999_29": 11,
	"1999_30": 11, # Previous year cut off
	"1999_31": 11,
	"1999_32": 11,
	"1999_33": 10,
	"1999_34": 11,
	"1999_36": 11,
	"1999_37": 11,
	"1999_38": 11,
	"1999_39": 11,
	"1999_40": 11,
	"1999_41": 11,
	"1999_42": 11,
	"1999_43": 10,
	"1999_45": 11,
	"1999_47": 11,
	"1999_48": 11,
	# There should be 1999_141, rename them later
	"1999_52": 11,
	"1999_54": 10,
	"1999_59": 11,
	"1999_61": 11,
	"1999_65": 11,
	"1999_66": 11,

	# 2000 section
	"2000_1": 10,
	"2000_2": 9,
	"2000_3": 10,
	"2000_4": 10,
	"2000_5": 10,
	"2000_6": 10,
	"2000_7": 10,
	"2000_8": 10,
	"2000_9": 10,
	"2000_11": 10,
	"2000_13": 10, # Manual???
	"2000_17": 10,
	"2000_18": 10,
	"2000_19": 10,
	"2000_20": 10,
	"2000_21": 10,
	"2000_22": 10,
	"2000_24": 10,
	"2000_25": 10,
	"2000_26": 10,
	"2000_27": 10,
	"2000_28": 10,
	"2000_29": 10,
	"2000_30": 10,
	"2000_31": 10,
	"2000_32": 10,
	"2000_33": 10,
	"2000_34": 10,
	"2000_36": 18,
	"2000_37": 10,
	"2000_38": 10,
	"2000_39": 21,
	"2000_41": 10,
	"2000_42": 10,
	"2000_43": 10,
	"2000_45": 10,
	"2000_46": 10,
	"2000_47": 10,
	"2000_52": 10,
	"2000_53": 10,
	"2000_54": 10,
	"2000_55": 10,
	"2000_56": 10,
	"2000_58": 11,
	"2000_59": 10,
	"2000_61": 10,
	"2000_63": 10,
	"2000_64": 10,
	"2000_65": 10,
	"2000_66": 10,
	"2000_69": 10,
	"2000_71": 10,
	"2000_75": 10,
	"2000_77": 107,

	# 2001 section
	"2001_1": 10,
	"2001_2": 10,
	"2001_3": 10,
	"2001_4": 10,
	"2001_5": 10,
	"2001_6": 10,
	"2001_7": 10,
	"2001_8": 10,
	"2001_9": 10,
	"2001_11": 10,
	"2001_13": 10,
	"2001_15": 10,
	"2001_17": 10,
	"2001_18": 10,
	"2001_19": 10,
	"2001_20": 10,
	"2001_21": 10,
	"2001_22": 10,
	"2001_23": 10,
	"2001_24": 10,
	"2001_25": 10,
	"2001_26": 10,
	"2001_27": 10,
	"2001_28": 10,
	"2001_29": 9,
	"2001_30": 10,
	"2001_31": 16,
	"2001_32": 17,
	"2001_33": 10,
	"2001_34": 10,
	"2001_35": 10,
	"2001_36": 10,
	"2001_37": 10,
	"2001_38": 10,
	"2001_39": 10,
	"2001_40": 10,
	"2001_41": 10,
	"2001_42": 10,
	"2001_43": 10,
	"2001_44": 10,
	"2001_45": 10,
	"2001_46": 10,
	"2001_47": 10,
	"2001_48": 10,
	"2001_49": 10,
	"2001_50": 13, # Manually fill?
	"2001_51": 13, # Manually fill?
	"2001_52": 10,
	"2001_53": 10,
	"2001_54": 10,
	"2001_55": 10,
	"2001_56": 10,
	"2001_57": 10,
	"2001_58": 10,
	"2001_59": 10,
	"2001_60": 10,
	"2001_61": 10,
	"2001_62": 13, # Manually fill?
	"2001_63": 10,
	"2001_64": 10,
	"2001_65": 10,
	"2001_66": 10,
	"2001_67": 13, # Manually fill?
	"2001_68": 13, # Manually fill?
	"2001_69": 10,
	"2001_71": 10,
	"2001_73": 10,
	"2001_74": 10,
	"2001_75": 10,
	"2001_76": 10,
	"2001_77": 10,
	"2001_78": 13, # Manually fill?
	"2001_79": 13, # Manually fill?
	"2001_82": 10,
	"2001_84": 10,
	"2001_86": 10,
	"2001_87": 10,
	"2001_88": 10,
	"2001_91": 10,
	"2001_92": 10,
	"2001_93": 10,
	"2001_94": 10,
	"2001_95": 10,
	"2001_101": 10,

}

HAND_FILLED = {
	'1998_44': 51,	# This report is a mess and frankly I'm not sure
					# if this is even right
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
	'1998_14': 35, # This is just a nightmare to parse
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
	'2015_152': 29, # Giant box = bad
	'2002_18': 13, # ditto
	'2004_116': 13, # Missed only expenditure
	'2006_93': 13, # Missed total revenue. Maybe fix with tolerance
	'2007_50': 14, # Total revenue and interest missing
	'2009_69': 14, # Missing total revenue, could fix
	'2010_43': 29, # Missing only expenditure, could fix
	'2011_108': 215, # ditto
	'2011_137': 29, # lines are fucked
	'2011_152': 29, # I hate lines
	'2011_164': 29, # Dear lines,
	'2014_50': 29, # Please let me be
	'2014_110': 30, # OCR missed. Probably because of a line
	'2015_36': 164, # Sorry got distracted
	'2015_140': 29, # Listen, you and I
	'2016_79': 33, # We're on two parallel paths
	'2016_90': 33, # We're not going to intersect
	'2016_122': 33, # So please
	'2016_167': 33,
	'2016_174': 32,
	'2017_74': 33,
	'2017_179': 32,
	'2019_62': 30, # Could fix
	'2019_140': 29,
	'2022_84': 33,
	'2022_185': 146,

	# 1999 section
	'1999_3': 23,	# The table was scanned, put in a field, then the
					# page was scanned
	'1999_4': 11,	# A lot of words got missed. Flagging this because
					# a lot of numbers were messed up during
					# pre-processing too
	'1999_5': 11, # The page is slanted and lines do not line up
	'1999_6': 11,	# Top section was missed. Flagged because numbers bad
	"1999_9": 11, # What the fuck is this scan
	'1999_11': 11, # OCR missed column headers
	"1999_12": 13, # Manually fill this
	'1999_14': 10, # OCR missed investment income row
	'1999_20': 11, # Tilted scan
	'1999_21': 11, # ditto
	"1999_35": 13, # Manually fill
	"1999_46": 13, # Manual
	'1999_53': 11, # ditto ditto
	'1999_56': 11, # ditto ditto ditto
	'1999_44': 11, # end of year fund is mangled
	"1999_55": 13, # Manual
	"1999_58": 12, # Manual, Slanted
	"1999_63": 13, # Manually fill

	# 2000 section
	'2000_14': 15, # OCR missed fields
	'2000_15': 23, # Not the nice form
	"2000_35": 13, # Manually fill
	"2000_50": 13, # Manually fill
	"2000_67": 13, # Manually fill
	"2000_73": 13, # Manually fill
	"2000_74": 13, # Manually fill
	"2000_79": 13, # Manually fill

	# 2001 section
	"2001_12": 13, # Manually fill
	'2001_14': 10, # OCR's a big dumb and missed total expenditures
	'2001_69': 23, # Iffy, I'll just make the call to manually do it
	"2001_80": 13, # Manually fill

	'1999_18': 11, # All revenues missing
	'1999_33': 10, # Misread character
	'1999_47': 11, # ditto
	'2000_71': 10, # Missed the one expenditure
	'2001_50': 13, # Numbers not read. It's a weird format
	'2001_51': 13, # Numbers not read. It's a weird format
	'2001_62': 13, # Numbers not read. It's a weird format
	'2001_67': 13, # Numbers not read. It's a weird format
	'2001_68': 13, # Numbers not read. It's a weird format
	'2001_78': 13, # Numbers not read. It's a weird format
	'2001_79': 13, # Numbers not read. It's a weird format
	"2001_89": 13, # Missed values
	"2001_96": 13, # Missed column
	"2001_98": 13, # Missed column
	"2001_100": 13, # Missed column
	"2001_102": 13, # Missed column
}

HAS_NO_EXPENDITURES = [
	'1999_7',
	"2006_139",
	'2006_124', # Maybe fix with tolerance
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

# I could fix these with code
EMPTY_TOTAL_EXPENDITURES = [
	'1997_28',
	'2014_29',
	'2017_122',
	'2018_27',
]

HAS_ANNOYING_PROBLEM = [
	'1998_11',
	'1998_3', # dot is at beginning
	'2005_25', # extra '-' row
	'2007_53', # Squished column, fix later
	'2017_174', # Property tax missing
	
]

def find_stuff(pair):

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
	
	if not resolved:
		print(pages)

		print(pair)

		print("Couldn't resolve")

total_tried = 0
fails = 0

pickle_timer_pages = 120
pickle_timer_tables = 120
pickle_reset = 120

unique_rev_fields = pd.DataFrame(columns=['labels', 'examples', 'where_at'], dtype=str)

if os.path.exists('known_pages.p'):
	print('Found pickle describing known_pages')
	with open('known_pages.p', 'rb') as fp:
		known_pages = pickle.load(fp)
else:
	known_pages = {}

if os.path.exists('known_tables.p'):
	print('Found pickle describing known_tables')
	with open('known_tables.p', 'rb') as fp:
		known_tables = pickle.load(fp)
else:
	known_tables = {}
	with open('known_tables.p', 'wb') as fp:
		pickle.dump(known_tables, fp, protocol=pickle.HIGHEST_PROTOCOL)

def append_new(row):
	if ((not isinstance(row['examples'], str) and math.isnan(row['examples']) or row['examples'].strip() == '') and
		(not isinstance(row['combined'], str) and math.isnan(row['combined']) or row['combined'].strip() == '')):
		return ''
	if ((not isinstance(row['examples'], str) and math.isnan(row['examples'])) or row['examples'].strip() == '') and not row['combined'].strip() == '':
		return row['combined']
	if ((not isinstance(row['combined'], str) and math.isnan(row['combined'])) or row['combined'].strip() == '') and not row['examples'].strip() == '':
		return row['examples']
	# if len(row['examples'].split('|')) > 40:
	# 	return row['examples']
	
	return f'{row["examples"]} | {row["combined"]}'

def who_dunnit(row):
	if ((not isinstance(row['where_at'], str) and math.isnan(row['where_at'])) or row['where_at'].strip() == '') and not row['this_guy'].strip() == '':
		return row['this_guy']
	if ((not isinstance(row['this_guy'], str) and math.isnan(row['this_guy'])) or row['this_guy'].strip() == '') and not row['where_at'].strip() == '':
		return row['where_at']
	# if len(row['where_at'].split(',')) > 40:
	# 	return row['where_at']
	
	return f'{row["where_at"]}, {row["this_guy"]}'

skip = False
im_fixing = True

# pd.set_option('display.max_colwidth', None)

dot_count = 0

for pair in page_status:

	dot_count += 1
	if dot_count > 34:
		dot_count = 0
		print('.', end='', flush=True)

	if pair in BROKEN:
		continue

	# if not skip:
	# 	sys.exit()

	if pair == '1999_61':
		skip = False

	if pair == '2006_139':
		im_fixing = False

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
	if pair in EMPTY_TOTAL_EXPENDITURES:
		continue
	if pair in HAS_ANNOYING_PROBLEM: # I'll fix these at some point
		continue
		# poi = [ADJUSTMENT_EMPTY[pair]]
	if pair in HAS_NO_EXPENDITURES or pair in HAS_NO_REVENUES:
		continue
	if pair in MANUAL_CORRECTIONS:
		poi = [MANUAL_CORRECTIONS[pair]]
	elif pair in known_pages:
		poi = known_pages[pair]
	else:
		poi = find_stuff(pair)
		pickle_timer_pages -= 1


	if pickle_timer_pages == 0:
		pickle_timer_pages = pickle_reset
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

	if pair in known_tables:
		table = known_tables[pair].copy()
	else:
		csv_path = f'../parsed_pdfs/{pair[0:4]}_{pair[5:]}.csv'

		table = find_table(csv_path, poi[0], int(pair[0:4]), int(pair[5:]))

		known_tables[pair] = table.copy()
		pickle_timer_pages -= 1

	if pickle_timer_tables == 0:
		pickle_timer_tables = pickle_reset
		# Write known_pages
		# Code adapted from https://stackoverflow.com/a/7100202/7362680
		print('Writing pickle')
		with open('known_tables.p', 'wb') as fp:
			pickle.dump(known_tables, fp, protocol=pickle.HIGHEST_PROTOCOL)
		print('Pickle finished writing')

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

	def lower_me(s):
		if isinstance(s, str):
			return s.lower()
		else:
			return ''

	table['labels'] = table['labels'].apply(func=lower_me)
	table.drop_duplicates(subset=['labels'], inplace=True)

	# Collect unique revenue fields
	labels = table['labels']

	# We just want
	# 	property tax
	# 	transfers in
	#	total expenditures
	#	transfers out
	#	re-distribution
	#   end balance
 
	# There is also
	# 	Administration costs
	#	Finance costs
	#	Bank names
	# But we aren't focused on getting those right now
	
	#####
 
	Statement(labels, table[table.columns[2]])
	

	# expenditure_pattern = re.compile(""
	# 	"[\.:|;‘_]*\s*expenditures:?$|"
	# 	"[\.:|;‘_]*\s*expenditures\/expenses?:?$|"	# Introduced 2002_1
	# 	"Expenditu\. 2s$|" # Edge case 1997_27
	# 	"Expenditures/expenses: ." # Edge case 2007_46
	# "", re.IGNORECASE)

	# revenue_pattern = re.compile(""
	# 	"[\.:|;‘_\s-]*revenues?[:\.,\s-]*$" # . at the end is from 2004_29 where there is a speck on the page
	# "", re.IGNORECASE)

	# total_rev_pattern = re.compile(""
	# 	"[\.:|;‘_\s-]*to[ti]a[l!] reven[u\s]es\s*[:-]*$|"
	# 	"tota[l!] revenues \.$|" # 2004_44. Speck
	# 	"Tota[l!] reven e[sn]$" # 2008_14 and 2006_15
	# "", re.IGNORECASE)

	# total_expend_pattern = re.compile(""
	# 	".*tota[l!]\sexpenditures.*$"
	# "", re.IGNORECASE)

	# rev_after_expend_pattern = re.compile(""
	# 	".*(excess\s*)?(of\s*)?(expen?ditures|revenues?)\s*(over|and|after|under)\s*(expen?ditures|revenues?).*$|"
	# 	".*revenues?\s*over(\s*\(under\))?\s*expenditures[$,Ss\-_\'=~\s.—§©:]*$"
	# "", re.IGNORECASE)

	# if pair in HAS_NO_REVENUES:
	# 	continue

	# # Find Revenues
	# rev_loc = -1
	# total_rev_loc = -1
	# expend_loc = -1
	# total_exp_loc = -1
	# rev_p_exp_loc = -1
	# for index, value in labels.items():
	# 	if rev_loc == -1 and re.match(revenue_pattern, value):
	# 		rev_loc = index
	# 	elif total_rev_loc == -1 and re.match(total_rev_pattern, value):
	# 		total_rev_loc = index
	# 	elif expend_loc == -1 and re.match(expenditure_pattern, value):
	# 		expend_loc = index
	# 	elif total_exp_loc == -1 and re.match(total_expend_pattern, value):
	# 		total_exp_loc = index
	# 	elif rev_p_exp_loc == -1 and re.match(rev_after_expend_pattern, value):
	# 		rev_p_exp_loc = index

	# IGNORE_FOR_EXPENDITURE_TESTING = [
	# 	'1997_28',
	# 	'2005_25', # Numbers are correct, there is just an extra dash
	# 	'2007_14', # Extra stuff
	# 	'2007_50', # ditto
	# 	'2008_14', # Extra stuff BUT will not match total revenues maybe
	# 	'2008_154', # Numbers right, just extra stuff
	# 	'2009_120', # Expenditure items missing, but total is still there. Numbers correct
	# ]

	####
	
	# We've iterated everywhere

	# if rev_loc == -1:
	# 	print("Couldn't find 'revenues'")
	# 	print(table)
	# 	sys.exit()
 
	# if pair in IGNORE_FOR_EXPENDITURE_TESTING or pair in HAS_NO_EXPENDITURES:
	# 	continue

	# if expend_loc == -1:
	# 	print("Couldn't find expenditures")
	# 	print(table)
	# 	print(f'Expend: {expend_loc},	Total Expenditures: {total_exp_loc},	rev/exp: {rev_p_exp_loc}')
	# 	correct_loc = input('Where is it?')
	# 	if correct_loc > 0:
	# 		expend_loc = correct_loc
	# 	else:
	# 		continue
	# 	# sys.exit()

	######

	# if rev_p_exp_loc == -1:
	# 	print("Couldn't find revenues after expenditures")
	# 	print(table)
	# 	print(f'Expend: {expend_loc},	Total Expenditures: {total_exp_loc},	rev/exp: {rev_p_exp_loc}')
	# 	correct_loc = int(input('Where is it?'))
	# 	if correct_loc > 0:
	# 		rev_p_exp_loc = correct_loc
	# 	else:
	# 		continue
	# 	# sys.exit()

	# # if total_exp_loc == -1 and rev_p_exp_loc - expend_loc > 2:
	# # 	print('The difference between net and expends is too much')
	# # 	print(table)
	# # 	print(f'Expend: {expend_loc},	Total Expenditures: {total_exp_loc},	rev/exp: {rev_p_exp_loc}')
	# # 	input('Waiting...')
	# # 	# sys.exit()

	# # print(f'Revenues: {rev_loc},\tTotal Revenues: {total_rev_loc},\tExpenditures: {expend_loc}')

	# # if total_rev_loc == -1 and expend_loc - rev_loc > 2 and not pair in HAS_NO_EXPENDITURES:
	# # 	print('The difference between revenues and expends is too much')
	# # 	print(table)
	# # 	sys.exit()

	# if rev_p_exp_loc == -1:
	# 	# Only grab the one field after rev_loc
	# 	# print('No total revenues')
	# 	add_these: str = table.iloc[[expend_loc+1]]
	# 	print(table)
	# 	input("Couldn't find rev/exp")
	# else:
	# 	# Grab everything in the series from rev to total_rev
	# 	# print('Using Total revenues')
	# 	# add_these = labels.iloc[(expend_loc + 1) : total_exp_loc]
	# 	add_these = table.iloc[:(rev_p_exp_loc + 1)]


	# # print('Combining')

	# table['combined'] = table[add_these.columns[2:]].apply(
	# 	lambda c : ', '.join(c.dropna().astype(str)),
	# 	axis=1
	# )
	# combine_me = table[['labels', 'combined']]
	# combine_me = combine_me.assign(this_guy=pair)

	# # print('Merging')

	# unique_rev_fields = unique_rev_fields.merge(combine_me, how='outer', on='labels')
	# # print('Appending')
	# unique_rev_fields['examples'] = unique_rev_fields.apply(append_new, axis=1)
	# unique_rev_fields['where_at'] = unique_rev_fields.apply(who_dunnit, axis=1)
	# # print('Dropping')
	# unique_rev_fields.drop(columns=['combined', 'this_guy'], inplace=True)
 
	######
 
	# print(unique_rev_fields['labels'].tolist())
	# print(unique_rev_fields)
	# I'm just combining these to find which one is unique


	# diffs = pd.Series(list(set(add_these) - set(unique_rev_fields['labels'])))
	# # print(diffs)
	# # print(unique_rev_fields)
	# # input('Waiting...')
	# if len(diffs) > 0:
	# 	print(f'There are {len(diffs)} new unique fields')
	# 	print(diffs)
	# 	print(table)
	# 	print(pair)
	# 	if im_fixing:
	# 		add_them = 'y'
	# 	else:
	# 		add_them = input('Add them? (Y/N)')
	# 	if add_them.lower() != 'n':
	# 		# Get the rows new rows
	# 		new_fields = table[table['labels'].isin(diffs)]
	# 		# Combine those use strings into one
	# 		new_content = new_fields[new_fields.columns[2:]].apply(
	# 			lambda c : ', '.join(c.dropna().astype(str)),
	# 			axis=1
	# 		)
	# 		to_add = pd.DataFrame({'labels': new_fields['labels'], 'examples': new_content})
	# 		unique_rev_fields = pd.concat([unique_rev_fields, to_add], ignore_index=True)
	# 		print('Unique fields is now')
	# 		print(unique_rev_fields)
	# 		time.sleep(2)
		
unique_rev_fields.drop_duplicates(inplace=True)
unique_rev_fields.to_csv('unique_rev_fields.csv', index=False)

print('Writing pickle')
with open('known_pages.p', 'wb') as fp:
	pickle.dump(known_pages, fp, protocol=pickle.HIGHEST_PROTOCOL)
with open('known_tables.p', 'wb') as fp:
	pickle.dump(known_tables, fp, protocol=pickle.HIGHEST_PROTOCOL)
print('Pickle(s) finished writing')
	
print(f'There are {len(unique_rev_fields)} unique fields')
# print(unique_rev_fields.to_string())