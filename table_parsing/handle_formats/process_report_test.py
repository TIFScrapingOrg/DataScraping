import pandas as pd
import re
import pprint
import sys
from handle_formats.cell_class import CELL, DEBUG
from handle_formats.find_rows import find_rows
from handle_formats.find_columns import find_columns
from handle_formats.expand_columns import expand_columns
	
DATABASE_FIELDS = ['year', 'tif_number', 'page_num', 'block_num', 'par_num', 'line_num', 'word_num', 'left', 'top', 'width', 'height', 'conf', 'text']

DOC_YEAR = 2015
DOC_NUM = 23
DOC_PAGE = 30

PROBLEM_CHARACTERS = re.compile(u'[|;‘i]')

def find_table(csv_path, page_num) -> pd.DataFrame | bool:

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

	if DEBUG:
		# Create a string representation of each line
		string_line_dict = {}
		for label, row in row_dictionary.items():
			string_line_dict[label] = [' '.join([word.text for word in row])]

		print('List of lines')
		pprint.pp(string_line_dict)

		# Create a string representation of each column
		string_col_dict = {}
		for label, col in column_dictionary.items():
			string_col_dict[label] = ['  '.join(word.text for word in col)]

		print('List of columns')
		pprint.pp(string_col_dict)

	label_column: dict[int, str] = {}

	for row in row_dictionary.values():

		row.sort(key=lambda c: c.left)
		label_column[row[0].row_marker] = (' '.join([word.text for word in row if not word.does_contain_numbers]))


	# Now it's time to create the dataframe
	possible_rows = sorted(list({word.row_marker for word in cell_list}))
	if DEBUG: print(possible_rows)

	label_column = [ label_column.get(key, ' ') for key in possible_rows ]

	if DEBUG:
		print('Label column')
		pprint.pp(label_column)

		print('Number of columns:', len(number_columns))

	data_columns = []
	for numbers in number_columns:
		build = []
		ind_spot = 0
		
		for row in possible_rows:
			if ind_spot < len(numbers) and numbers[ind_spot].row_marker == row:
				build.append(numbers[ind_spot].text)
				ind_spot += 1
			else:
				build.append(' ')

		data_columns.append(build)

	table_layout = { 'rows': possible_rows, 'labels': label_column }
	for number, column in enumerate(data_columns):
		table_layout[f'Col {number}'] = column
		
		
	document_frame = pd.DataFrame(table_layout)

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