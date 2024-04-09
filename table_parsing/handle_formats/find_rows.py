import re
import sys
import pprint
from handle_formats.cell_class import CELL, DEBUG

def find_rows(cell_list: list[CELL], vertical_threshold=15, horizontal_threshold=40):

	if DEBUG:
		print(f'There are {len(cell_list)} cells available')
		pprint.pp([word.text for word in cell_list])

	# This dictionary will hold all of the lines
	row_dictionary: dict[float, list[CELL]] = {}

	# By default, put each word on it's own line or whatever line it happens to
	# share with others
	for word in cell_list:

		if word.center_y not in row_dictionary:
			row_dictionary[word.center_y] = []
		
		row_dictionary[word.center_y].append(word)

	# Next reduce the number of rows to what they should actually be
	REDUCED = True
	while REDUCED:

		REDUCED = False
		current_keys = sorted(list(row_dictionary.keys()))

		for i in range(len(current_keys) - 1):

			# If the distance between two keys is below threshold, combine them
			if abs(current_keys[i] - current_keys[i+1]) <= vertical_threshold:

				REDUCED = True
				avg = (current_keys[i] + current_keys[i+1]) / 2
				
				row_dictionary[avg] = row_dictionary[current_keys[i]] + row_dictionary[current_keys[i+1]]

				# Get rid of the original keys
				del row_dictionary[current_keys[i]]
				del row_dictionary[current_keys[i+1]]

				break

	# Go through and sort each row
	for row in row_dictionary.values():
		row.sort(key=lambda w: w.left)

	if DEBUG:
		print(f'After processing, there are {len(row_dictionary.keys())} rows:')
		for row in row_dictionary.values():
			print(', '.join([word.text for word in row]))
		print()

	# Next, we need to "crunch the numbers" hehe. Joking aside, this means we
	# need to combine line items that are closer than 50px to each other on the
	# horizontal axis AND are majority numbers. This is to catch things like
	#   "$ 3,455,555"
	# being recognized as
	#   $  +  3,455,55  +  5
	# They are the same number, OCR just didn't put them in the same group
 
	for row, words in row_dictionary.items():

		furthest_reduced = 0
		REDUCED = True
		while REDUCED:

			REDUCED = False
			words.sort(key=lambda w: w.left)

			for ind in range(furthest_reduced, len(words) - 1):

				curr = words[ind]
				next = words[ind+1]
				
				# If the word we are looking at is not majority numbers, skip it
				curr_percent_numeric = sum([1 if re.match(u'[\d,$]', c) else 0 for c in curr.text]) / len(curr.text)
				next_percent_numeric = sum([1 if re.match(u'[\d,$]', c) else 0 for c in next.text]) / len(next.text)

				
				edgecase_1 = curr.text.lower() == "ad" and next.text.lower() == "justments"

				if (curr_percent_numeric < 0.5 or next_percent_numeric < 0.5) and not edgecase_1:
					continue

				# If the words are sufficiently far apart, we don't care
				distance = next.left - curr.right
				if distance > horizontal_threshold:
					continue

				# Okay, now we KNOW that we want to "crunch" the numbers
				REDUCED = True

				top = min(curr.top, next.top)
				width = curr.width + distance + next.width
				height = max(curr.top + curr.height, next.top + next.height) - top

				# Cronch, cronch
				replacement = CELL({
					'text': curr.text + next.text,
					'left': curr.left,
					'top': top,
					'width': width,
					'height': height,
					'conf': min(curr.conf, next.conf),
				})

				words[ind] = replacement
				words.pop(ind+1)

				# Update the dictionary to save our work
				row_dictionary[row] = words

				break
		
	# Go ahead and round off the row indices
	row_dictionary = { round(index): row for index, row in row_dictionary.items() }

	# The table we are after has bounds. The bottom of tables will always have
	# 'end of year' in it and the top will always be 'revenues'. Of course we
	# need to go a tad above revenues to catch the column headers.
	
	row_keys = sorted(list(row_dictionary.keys()))
	revenue_location = -1
	end_year_location = -1

	height_of_revenue = -1

	# Find the revenue location
	for index in range(len(row_keys)):

		content = row_dictionary[row_keys[index]]

		# If true, 'revenues' will be the only word in that row
		if len(content) == 1 and re.search('revenue', content[0].text.lower()):
			revenue_location = index
			height_of_revenue = content[0].height
			break

		# Also gotta check for the case that an extra character slips in that
		# would make the length longer than 1. Additionally, this character will
		# only be of length 1
		if len(content) > 1:
			revenue_in_row = any([ re.search('revenue', c.text.lower()) for c in content])
			if revenue_in_row:
				# Check to see if there is only one count of a string longer than 1 char
				# And 'en' because this is the pinnacle of machine learning
				if sum([ 1 if len(c.text) > 1 and c.text != 'en' else 0 for c in content]) == 1:
					revenue_location = index
					height_of_revenue = max([c.height for c in content])
					break
	else:
		print("Couldn't find revenue")
		return False
		sys.exit()

	# Find the 'end of year' location
	for index in range(revenue_location, len(row_keys)):

		content = row_dictionary[row_keys[index]]
		squashed = ''.join([w.text for w in content]).lower()

		if re.search('endofyear', squashed):
			end_year_location = index
			break
	else:
		print("Couldn't find 'end of year'")
		return False
		sys.exit()

	

	# Now delete everything after 'end of year'
	for index in range(end_year_location+1, len(row_keys)):
		del row_dictionary[row_keys[index]]

	# And just before 'revenues'
	for index in range(revenue_location):
		# To catch the column headers, we're just gonna subtract a little from the
		# revenue location
		if row_keys[index] < row_keys[revenue_location] - 5 * height_of_revenue:
			del row_dictionary[row_keys[index]]

	# Now go though and give each cell a row_marker
	for marker, row in row_dictionary.items():
		for cell in row:
			cell.row_marker = marker

	# We altered the input cells a bit, we we need to return our new version of them
	altered_cells = []
	for row in row_dictionary.values():
		for cell in row:
			altered_cells.append(cell)

	return row_dictionary, altered_cells