print('Loading...')

import sys
import pandas as pd
from difflib import SequenceMatcher
import os
import re
from handle_formats.process_report_test import find_table
import pickle
import math
import copy
from colorama import Fore, Style, init as colorama_init
from handle_formats.statement import Statement
from page_dictionary import SKIP_LIST, HAND_FILLED, MANUAL_CORRECTIONS
import hmac
import uuid
import hashlib

colorama_init()

DATABASE_FIELDS = ['year', 'tif_number', 'page_num', 'block_num', 'par_num', 'line_num', 'word_num', 'left', 'top', 'width', 'height', 'conf', 'text']
COMPLETION_STATUS_CSV = 'butter_json.csv'
PARSED_PDFS_DIR = '../parsed_pdfs'
PICKLE_KEY = uuid.getnode().to_bytes(6)

FINDING_UNIQUE_FIELDS = False

# Load in completion status of files and their pages
completion_csv = pd.read_csv(COMPLETION_STATUS_CSV)
completion_csv.drop(labels=['id'], axis=1, inplace=True)

page_status = {}
for _, row in completion_csv.iterrows():

	key = f"{row['year']}_{row['tif_number']}"

	if key not in page_status:
		page_status[key] = {'successful': [], 'failed': []}
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


# Adapted from
# https://pycharm-security.readthedocs.io/en/latest/checks/PIC100.html
# https://stackoverflow.com/a/7100202/7362680
def read_pickle(fname):

	if not os.path.exists(fname):
		return {}
	
	print('Found pickle', fname)
	with open(fname, 'rb') as fp:
		contents = fp.read()
		digest = contents[:64]
		pickle_maybe = contents[64:]
		expected_digest = hmac.new(PICKLE_KEY, pickle_maybe, hashlib.blake2b).digest()

	if hmac.compare_digest(digest, expected_digest):
		# Keys match!
		return pickle.loads(pickle_maybe)
	else:
		# Keys don't match. Scary pickle
		return {}


def write_pickle(data, fname):
	write_me = pickle.dumps(data)
	digest = hmac.new(PICKLE_KEY, write_me, hashlib.blake2b).digest()
	with open(fname, 'wb') as fp:
		fp.write(digest + write_me)
		

IGNORE_STRING_1 = 'no tax increment project expenditures'  # First seen 1997
IGNORE_STRING_2 = 'no tax increment expenditures within the project area'  # First seen 1998_4
IGNORE_STRING_3 = 'no tax increment expenditures or cumulative deposits over'  # First seen 2002_10


def is_ignored(query_vector):
	# Join all elements of vector
	doc_string = ' '.join(query_vector)
	doc_string = doc_string.lower()

	match_ignore_1 = re.search(IGNORE_STRING_1, doc_string) is not None
	match_ignore_2 = re.search(IGNORE_STRING_2, doc_string) is not None
	match_ignore_3 = re.search(IGNORE_STRING_3, doc_string) is not None

	return match_ignore_1 or match_ignore_2 or match_ignore_3


# These are here for the purpose of finding labels
HAS_NO_EXPENDITURES = [
	'1999_7',
	"2006_139",
	'2006_124',
]
HAS_NO_REVENUES = [
	"2010_169",
	'2012_7'
]
ADJUSTMENT_EMPTY = {
	"2008_50": 14,
	"2009_113": 14,
	'2015_177': 29,
	"2017_154": 32
}
EMPTY_TOTAL_EXPENDITURES = [
	'1997_28',
	'2014_29',
	'2017_122',
	'2018_27',
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
	pages: list[int] = top_section['page_num'].unique()

	matched_pages: list[int] = []

	for page in pages:

		page_df = top_section[top_section['page_num'] == page]
		page_vector = page_df['text']

		if is_finance(page_vector.to_list()):
			matched_pages.append(page)

	# These all have exactly 2 matches (when not 0)
	if pair[0:4] in ['2007', '2008', '2009'] and len(matched_pages) == 2:
		matched_pages = [matched_pages[0]]
		print('Corrected', matched_pages)
		return matched_pages[0]
		# return [matched_pages[0], tif_text[tif_text['page_num'] == int(matched_pages[0])]]

	elif len(matched_pages) > 1:
		print('Too many pages')
		return False

	if len(matched_pages) > 0:
		return matched_pages[0]
		# return [matched_pages[0], tif_text[tif_text['page_num'] == int(matched_pages[0])]]

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
		return -1

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
		return matched_pages[0]
	
	if not resolved:
		print(pages)

		print(pair)

		print("Couldn't resolve")
	return False


fails = 0

pickle_timer_pages = 120
pickle_timer_tables = 120
pickle_timer_statements = 120
pickle_reset = 680

unique_rev_fields = pd.DataFrame(columns=['labels', 'examples', 'where_at'], dtype=str)


known_pages: dict[str, int] = read_pickle('known_pages.txt')

known_tables: dict[str, pd.DataFrame] = read_pickle('known_tables.txt')

known_statements: dict[str, Statement] = read_pickle('known_statements.txt')


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

dot_count = 0

all_statements: list[Statement] = []

for pair in page_status:

	dot_count += 1
	if dot_count > 34:
		dot_count = 0
		print('.', end='', flush=True)

	if pair == '2012_60':
		skip = False

	if skip:
		continue
	
	print(pair)

	if pair in SKIP_LIST or pair in HAND_FILLED or pair in ADJUSTMENT_EMPTY:
		continue

	if pair in MANUAL_CORRECTIONS:
		poi = MANUAL_CORRECTIONS[pair]
	elif pair in known_pages and known_pages[pair]:
		poi = known_pages[pair]
	else:
		poi = find_stuff(pair)
		pickle_timer_pages -= 1

	if pickle_timer_pages == 0:
		# Write known_pages
		pickle_timer_pages = pickle_reset
		write_pickle(known_pages, 'known_pages.txt')
	
	if poi is False:
		continue
	
	known_pages[pair] = poi

	print(poi)

	if poi == -1:
		continue

	if pair in known_tables:
		table = known_tables[pair].copy()
	else:
		csv_path = f'../parsed_pdfs/{pair[0:4]}_{pair[5:]}.csv'

		table = find_table(csv_path, poi, int(pair[0:4]), int(pair[5:]))

		if table is False:
			print(pair, poi)
			input('Waiting to continuer...')
			fails += 1
			continue

		known_tables[pair] = table.copy()
		pickle_timer_tables -= 1

		if pickle_timer_tables == 0:
			# Write known_pages
			pickle_timer_tables = pickle_reset
			write_pickle(known_tables, 'known_tables.txt')

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
	labels = table['labels']

	# We just want
	# 	property tax
	# 	transfers in
	#   total expenditures
	#   transfers out
	#   re-distribution
	#   end balance
	
	# There is also
	# 	Administration costs
	#   Finance costs
	#   Bank names
	# But we aren't focused on getting those right now
	
	#####

	print('Unedited table:')
	print(table)

	if pair in known_statements:
		new_statement = known_statements[pair]
	else:
		new_statement = Statement(labels, table[table.columns[2]], pair)
		known_statements[pair] = copy.deepcopy(new_statement)
		pickle_timer_statements -= 1

	all_statements.append(new_statement)

	if pickle_timer_statements == 0:
		# Write known_statements
		pickle_timer_statements = pickle_reset
		write_pickle(known_statements, 'known_statements.txt')

	######

	if FINDING_UNIQUE_FIELDS:
	
		expenditure_pattern = re.compile(""
			r"[\.:|;‘_]*\s*expenditures:?$|"
			r"[\.:|;‘_]*\s*expenditures\/expenses?:?$|"	 # Introduced 2002_1
			r"Expenditu\. 2s$|"  # Edge case 1997_27
			r"Expenditures/expenses: ."  # Edge case 2007_46
		"", re.IGNORECASE)

		revenue_pattern = re.compile(""
			r"[\.:|;‘_\s-]*revenues?[:\.,\s-]*$"  # . at the end is from 2004_29 where there is a speck on the page
		"", re.IGNORECASE)

		total_rev_pattern = re.compile(""
			r"[\.:|;‘_\s-]*to[ti]a[l!] reven[u\s]es\s*[:-]*$|"
			r"tota[l!] revenues \.$|"  # 2004_44. Speck
			r"Tota[l!] reven e[sn]$"  # 2008_14 and 2006_15
		"", re.IGNORECASE)

		total_expend_pattern = re.compile(""
			r".*tota[l!]\sexpenditures.*$"
		"", re.IGNORECASE)

		rev_after_expend_pattern = re.compile(""
			r".*(excess\s*)?(of\s*)?(expen?ditures|revenues?)\s*(over|and|after|under)\s*(expen?ditures|revenues?).*$|"
			r".*revenues?\s*over(\s*\(under\))?\s*expenditures[$,Ss\-_\'=~\s.—§©:]*$"
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
			'2005_25',  # Numbers are correct, there is just an extra dash
			'2007_14',  # Extra stuff
			'2007_50',  # ditto
			'2008_14',  # Extra stuff BUT will not match total revenues maybe
			'2008_154',  # Numbers right, just extra stuff
		]

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

		if rev_p_exp_loc == -1:
			print("Couldn't find revenues after expenditures")
			print(table)
			print(f'Expend: {expend_loc},	Total Expenditures: {total_exp_loc},	rev/exp: {rev_p_exp_loc}')
			correct_loc = int(input('Where is it?'))
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

		print(f'Revenues: {rev_loc},\tTotal Revenues: {total_rev_loc},\tExpenditures: {expend_loc}')

		if total_rev_loc == -1 and expend_loc - rev_loc > 2 and pair not in HAS_NO_EXPENDITURES:
			print('The difference between revenues and expends is too much')
			print(table)
			sys.exit()

		if rev_p_exp_loc == -1:
			# Only grab the one field after rev_loc
			# print('No total revenues')
			add_these: str = table.iloc[[expend_loc+1]]
			print(table)
			input("Couldn't find rev/exp")
		else:
			# Grab everything in the series from rev to total_rev
			# print('Using Total revenues')
			# add_these = labels.iloc[(expend_loc + 1) : total_exp_loc]
			add_these = table.iloc[:(rev_p_exp_loc + 1)]

		# print('Combining')

		table['combined'] = table[add_these.columns[2:]].apply(
			lambda c: ', '.join(c.dropna().astype(str)),
			axis=1
		)
		combine_me = table[['labels', 'combined']]
		combine_me = combine_me.assign(this_guy=pair)
		combine_me.drop_duplicates(subset='labels', inplace=True)

		# print('Merging')

		unique_rev_fields = unique_rev_fields.merge(combine_me, how='outer', on='labels')
		# print('Appending')
		unique_rev_fields['examples'] = unique_rev_fields.apply(append_new, axis=1)
		unique_rev_fields['where_at'] = unique_rev_fields.apply(who_dunnit, axis=1)
		# print('Dropping')
		unique_rev_fields.drop(columns=['combined', 'this_guy'], inplace=True)
		unique_rev_fields.drop_duplicates()

		######

		# print(unique_rev_fields['labels'].tolist())
		# print(unique_rev_fields)
		# I'm just combining these to find which one is unique

		diffs = pd.Series(list(set(add_these) - set(unique_rev_fields['labels'])))
		# print(diffs)
		# print(unique_rev_fields)
		# input('Waiting...')
		if len(diffs) > 0:
			print(f'There are {len(diffs)} new unique fields')
			# print(diffs)
			# print(table)
			# print(pair)
			# if im_fixing:
			# 	add_them = 'y'
			# else:
			# 	add_them = input('Add them? (Y/N)')
			# if add_them.lower() != 'n':
			# Get the rows new rows
			new_fields = table[table['labels'].isin(diffs)]
			# Combine those use strings into one
			new_content = new_fields[new_fields.columns[2:]].apply(
				lambda c: ', '.join(c.dropna().astype(str)),
				axis=1
			)
			to_add = pd.DataFrame({'labels': new_fields['labels'], 'examples': new_content})
			unique_rev_fields = pd.concat([unique_rev_fields, to_add], ignore_index=True)
			# print('Unique fields is now')
			# print(unique_rev_fields)

if FINDING_UNIQUE_FIELDS:
	unique_rev_fields.drop_duplicates(inplace=True)
	unique_rev_fields.to_csv('unique_rev_fields.csv', index=False)

print('Writing pickle')
write_pickle(known_pages, 'known_pages.txt')
write_pickle(known_tables, 'known_tables.txt')
write_pickle(known_statements, 'known_statements.txt')
print('Pickle(s) finished writing')
	
# print(f'There are {len(unique_rev_fields)} unique fields')

print('Testing results')
print('---------------')
print(f'{Fore.RED}{sum([len(s.hazards) + len(s.revenue_object.hazards) + len(s.expenditure_object.hazards) > 1 for s in all_statements])}/{len(all_statements)} statements had two or more flags{Style.RESET_ALL}')
print(f'{Fore.YELLOW}{sum([len(s.hazards) + len(s.revenue_object.hazards) + len(s.expenditure_object.hazards) == 1 for s in all_statements])}/{len(all_statements)} statements had one flag{Style.RESET_ALL}')
print(f'{Fore.GREEN}{sum([len(s.hazards) + len(s.revenue_object.hazards) + len(s.expenditure_object.hazards) == 0 for s in all_statements])}/{len(all_statements)} statements had no flags{Style.RESET_ALL}')

print(f'There were {sum([s.expenditure_object.vertical_check_sum() for s in all_statements])}/{len(all_statements)} correct expenditures')
print(f'There were {sum([s.revenue_object.vertical_check_sum() for s in all_statements])}/{len(all_statements)} correct revenues')
print(f'There were {sum([s.revenues_and_expenditures_checksum() for s in all_statements])}/{len(all_statements)} correct rev/exp checks')
