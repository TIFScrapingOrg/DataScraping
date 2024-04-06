import pandas as pd
import re
import pprint

DATABASE_FIELDS = ['year', 'tif_number', 'page_num', 'block_num', 'par_num', 'line_num', 'word_num', 'left', 'top', 'width', 'height', 'conf', 'text']

DOC_YEAR = 1999
DOC_NUM = 41
DOC_PAGE = 11

csv_path = f'../../parsed_pdfs/{DOC_YEAR}_{DOC_NUM}.csv'
tif_text = pd.read_csv(csv_path, header=None, names=DATABASE_FIELDS)

# Get text specifically for this page
page = tif_text[tif_text['page_num'] == DOC_PAGE]

# Add another column to every row that is the center of the recognized text
def find_center_x(row):
	return row['left'] + row['width'] / 2

def find_center_y(row):
	return row['top'] + row['height'] / 2

col_x = page.apply(find_center_x, axis=1)
col_y = page.apply(find_center_y, axis=1)

page = page.assign(center_x=col_x.values)
page = page.assign(center_y=col_y.values)

# Drop columns that don't help us for this task
USELESS_COLS = ['year', 'tif_number', 'page_num', 'block_num', 'par_num', 'line_num', 'word_num']
page = page.drop(USELESS_COLS, axis=1)

# Create a dictionary of 'lines' in the document. A line is defined as a group
# of words that are all within 15px along the y-axis of each other.

# To do this, first create an empty dictionary and simply sort the entire dataframe by center_y

# Initially, put all of the items that share the same center_y into the same
# list (inside the dict) keyed by their average

# Iteratively join groups that have an average closer than 15px until there are no merges

page.sort_values(['center_y'])

line_dict = {}

for _, row in page.iterrows():

	if row['center_y'] not in line_dict:
		line_dict[row['center_y']] = []

	line_dict[row['center_y']].append(row.to_dict())

# Now iteratively reduce the list

REDUCED = True
merges = 0
while REDUCED:

	REDUCED = False

	current_keys = sorted(list(line_dict.keys()))

	for i in range(len(current_keys) - 2):
		if not REDUCED and abs(float(current_keys[i]) - float(current_keys[i+1])) <= 15:

			REDUCED = True
			merges += 1

			avg = (current_keys[i] + current_keys[i+1]) / 2

			
			line_dict[avg] = line_dict[current_keys[i]] + line_dict[current_keys[i+1]]

			# Get rid of the original keys
			del line_dict[current_keys[i]]
			del line_dict[current_keys[i+1]]



# Combine line items that are closer than 50px to each other on the horizontal
# axis
			
for key, words in line_dict.items():

	REDUCED = True
	while REDUCED:

		REDUCED = False
		
		for i in range(len(words) - 2):

			words.sort(key=lambda w: w['left'])

			distance = words[i+1]['left'] - (words[i]['width'] + words[i]['left'])
			
			if not REDUCED and distance < 40:

				REDUCED = True
				
				top = min(words[i]['top'], words[i+1]['top'])
				replacement = {
					'left': words[i]['left'],
					'top': top,
					'width': words[i]['width'] + distance + words[i+1]['width'],
					'height': max(words[i]['top'] + words[i]['height'], words[i+1]['top'] + words[i+1]['height']) - top,
					'conf': min(words[i]['conf'], words[i+1]['conf']),
					# 'text': words[i]['text'] + '_' + words[i+1]['text']
					'text': words[i]['text'] + words[i+1]['text']
				}

				words[i] = replacement
				words.pop(i+1)

				line_dict[key] = words

# Create a string representation of each line

document_line_dict = {}

for level in sorted(list(line_dict.keys())):
	line_dict[level].sort(key=lambda r: r['left'])
	document_line_dict[level] = ''
	for word in line_dict[level]:
		document_line_dict[level] += word['text'] + ' '
	
	if len(line_dict) > 0:
		document_line_dict[level] = document_line_dict[level][:-1]

print('List of lines')
pprint.pp(document_line_dict)


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

# My solution is to compute two evenly spaced out lines spanning the entire
# width of the caught numbers and then putting any element that crosses over
# either of those lines inside of the column:
#     |    |
#     1999
# -----------
#     |    |
#       5,555
#      10,666
#      64,111
#     |    |
#         333
#    (659,000)
#   1,511,632
#     |    |
# The drawback is that this may catch words above or below the columns.
# The solution? We know where the top and bottom rows of the table should be.
# They will always be either "Revenues" or have "end of year" in them.
#                                 |    |
#                                 1999
#  Revenues                   
#    Property tax                   7,455
#    Sales tax                      5,555
#    Interest                      10,666
#
#  Expenditures                    64,111
#                                 |    |
#  ...                                333
#                                (659,000)
#  Fund balance, end of year    1,511,632
#                                 |    |
# This will cut off the column headers though. My one guess as to how to fix
# that is to just draw the column of numbers up until there is a gap of at least
# 50 px. It's probably not fool proof, but it will work