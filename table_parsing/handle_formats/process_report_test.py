import pandas as pd
import re
import pprint
import sys
from difflib import SequenceMatcher
from handle_formats.cell_class import CELL, NUMBER_COLUMN_TYPE, DEBUG
from handle_formats.find_rows import find_rows
from handle_formats.find_columns import find_columns
from handle_formats.expand_columns import expand_columns
	
DATABASE_FIELDS = ['year', 'tif_number', 'page_num', 'block_num', 'par_num', 'line_num', 'word_num', 'left', 'top', 'width', 'height', 'conf', 'text']

DOC_YEAR = 2015
DOC_NUM = 23
DOC_PAGE = 30

PROBLEM_CHARACTERS = re.compile(u'[|;‘i]$')

def find_table(csv_path: str, page_num: int, year: int, tif_num: int):

	tif_text = pd.read_csv(csv_path, header=None, names=DATABASE_FIELDS)

	# Get text specifically for this page
	page = tif_text[tif_text['page_num'] == page_num]

	# Convert every row into cells that are easy to work with
	cell_list: list[CELL] = []
	for _, row in page.iterrows():
		if not re.match(PROBLEM_CHARACTERS, row['text']):
			cell_list.append(CELL(row))

	# Label the rows
	row_query = find_rows(cell_list)
	if row_query:
		_, cell_list = row_query
	else:
		return False
	
	# Label the columns
	column_dictionary, cell_list = find_columns(cell_list)
	# Expand the columns upwards
	column_dictionary, cell_list, number_columns = expand_columns(cell_list, column_dictionary)

	# That changed up some of the cells, so create the row_dictionary again
	row_dictionary: dict[int, list[CELL]] = {}
	for cell in cell_list:
		if cell.row_marker not in row_dictionary:
			row_dictionary[cell.row_marker] = [cell]
		else:
			row_dictionary[cell.row_marker].append(cell)

	row_dictionary = { key: row_dictionary[key] for key in sorted(list(row_dictionary.keys()))}

	# Create a string representation of each line
	string_line_dict: dict[int, list[str]] = {}
	for label, row in row_dictionary.items():
		string_line_dict[label] = [' '.join([word.text for word in row])]

	if DEBUG:

		print('List of lines')
		pprint.pp(string_line_dict)

		# Create a string representation of each column
		string_col_dict: dict[int, list[str]] = {}
		for label, col in column_dictionary.items():
			string_col_dict[label] = ['  '.join(word.text for word in col)]

		# Sort
		string_col_dict = { key: string_col_dict[key] for key in sorted(string_col_dict.keys())}

		print('List of columns')
		pprint.pp(string_col_dict)


	# Lets try to find labels for those number columns
	# First, find the row-marker of the revenue label
	revenue_pattern = re.compile(""
		"[\.:|;‘_\s-]*revenues?[:\.,\s-]*$|"
		"tota[l!] revenues \.$|" # 2004_44. Speck
		"Tota[l!] reven e[sn]\'?$|" # 2008_14
		"Revenues: en$" # 2006_15
	"", re.IGNORECASE)
	revenue_marker = -1
	for label, row in string_line_dict.items():
		if re.match(revenue_pattern, row[0]):
			revenue_marker = label
			break
	else:
		print('Could not find revenue marker')
		return False
	
	# Now that we know where revenue is, we can grab the results above it and
	# then get rid of them
	number_header = []
	is_just_year = False
	for number_column_index, column in enumerate(number_columns):
		# Walk until we find that row marker or pass it
		index_oi = 0
		for index in range(len(column)):
			if column[index].row_marker >= revenue_marker:
				index_oi = index
				break
		else:
			print('Column is empty?')
			pprint.pp([w.text for w in column])
			return False
		# Our column header should be the first n elements of the column
		supposed_header = column[:index_oi]
		# Remove our supposed header from elsewhere
		column = column[index_oi:]
		for w in supposed_header:
			cell_list.remove(w)
			column_dictionary[w.col_marker].remove(w)
			row_dictionary[w.row_marker].remove(w)
			if len(column_dictionary[w.col_marker]) == 0: # uff da if this happens
				del column_dictionary[w.col_marker]
			if len(row_dictionary[w.row_marker]) == 0:
				del row_dictionary[w.row_marker]
		header_string = ''.join([w.text.lower() for w in supposed_header])
		if number_column_index == 0:
			# It's either the current year or 'Governmental Funds'
			if DEBUG: print(f'The header string is: {header_string}')
			relation_year = SequenceMatcher(None, header_string, str(year)).ratio()
			relation_gov = SequenceMatcher(None, header_string, 'governmentalfunds').ratio()

			if relation_year < 0.5 and relation_gov < 0.5:
				if DEBUG: print('It is likely empty')
				if relation_gov > relation_year:
					if DEBUG: print('relation to government is higher than year. Defaulting to government')
					number_header = [
						NUMBER_COLUMN_TYPE.GOV_FUNDS,
						NUMBER_COLUMN_TYPE.ADJUSTMTS,
						NUMBER_COLUMN_TYPE.STATEMENT
					]
				else:
					if DEBUG: print('relation to government is lower than year. Defaulting to year')
					is_just_year = True
					number_header.append(NUMBER_COLUMN_TYPE.CURR_YEAR)
			elif relation_year > 0.5: # 0 is usually what it is if we compare numbers to letters
				is_just_year = True
				number_header.append(NUMBER_COLUMN_TYPE.CURR_YEAR)
			else: # Assume it's GF
				number_header = [
					NUMBER_COLUMN_TYPE.GOV_FUNDS,
					NUMBER_COLUMN_TYPE.ADJUSTMTS,
					NUMBER_COLUMN_TYPE.STATEMENT
				]
				# break
		elif number_column_index == 1:
			# Idk why, but check just in case
			if is_just_year:
				if SequenceMatcher(None, header_string, str(year - 1)).ratio() > 0.5:
					number_header.append(NUMBER_COLUMN_TYPE.PREV_YEAR)
				else:
					print('Why do we have an extra column? The label does not match. Is page tilted?')
					print("Because this is 'is_just_year', assume that it just didn't get recognized")
					number_header.append(NUMBER_COLUMN_TYPE.PREV_YEAR)
					# TODO: Write something to get return flags to signal possible issues
					# return False

	label_column: dict[int, str] = {}

	for row in row_dictionary.values():

		row.sort(key=lambda c: c.left)
		label_column[row[0].row_marker] = (' '.join([word.text for word in row if not word.does_contain_numbers]))


	# Now it's time to create the dataframe
	possible_rows = sorted(list({word.row_marker for word in cell_list}))
	if DEBUG: print(possible_rows)

	label_column = [ label_column.get(key, pd.NA) for key in possible_rows ]

	if DEBUG:
		print('Label column')
		pprint.pp(label_column)

		print('Number of columns:', len(number_columns))
		for column in number_columns:
			pprint.pp([ w.text for w in column ])
			print( [w.row_marker for w in column] )

	data_columns: list[str] = []
	for numbers in number_columns:
		build: list[str] = []
		ind_spot = 0
		
		for row in possible_rows:
			if ind_spot < len(numbers) and numbers[ind_spot].row_marker == row:
				build.append(numbers[ind_spot].text)
				ind_spot += 1
			else:
				build.append(pd.NA)

		data_columns.append(build)


	table_layout = { 'rows': possible_rows, 'labels': label_column }
	for index, column in enumerate(data_columns):
		if DEBUG:
			pprint.pp(table_layout)
			print(number_header[index])
		table_layout[number_header[index]] = column
		
		
	document_frame = pd.DataFrame(table_layout)

	document_frame = document_frame.dropna(subset=['labels'], ignore_index=True)


	if DEBUG: print(document_frame)
	return document_frame

# print('List of columns')
# pprint.pp(string_col_dict)

# Now try to extract columns
# All of the numbers, at least, are right aligned in the columns
# What this looks like is:
#     1999
# -----------
#       5,555
#      10,666
#      64,111
#         333
#    (659,000)
#   1,511,632

# Now you'll notice that the parens () on the negative numbers don't follow this
# rule so we won't catch everything like that

# My solution is to find the two outer lines that are at the left and right of
# the the caught numbers and then putting any element that crosses over either
# of those lines or are contained in them inside of the column:
#   |       |
#     1999
# -----------
#   |       |
#       5,555
#      10,666
#      64,111
#   |       |
#         333
#    (659,000)
#   1,511,632
#   |       |
# The drawback is that this may catch words above or below the columns.
# The solution? We know where the top and bottom rows of the table should be.
# They will always be either "Revenues" or have "end of year" in them.
#                               |       |
#                                 1999
#  Revenues                   
#    Property tax                   7,455
#    Sales tax                      5,555
#    Interest                      10,666
#
#  Expenditures                    64,111
#                                     333
#   ...                         |       |
#                                (659,000)
#  Fund balance, end of year    1,511,632
#                               |       |
# This will cut off the column headers though. My one guess as to how to fix
# that is to just draw the column of numbers up until there is a gap of at least
# 50 px. It's probably not fool proof, but it will work