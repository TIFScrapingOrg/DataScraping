import re
import sys
from handle_formats.cell_class import CELL, DEBUG

MAX_TRIES = 20
COLUMN_NUMBER_MIN_RATIO = 0.7


def expand_columns(cell_list: list[CELL], column_dictionary: dict[int, list[CELL]]):
	
	tries = 0

	COMBINATION_OCCURRED = True

	was_number_at_some_point = []

	min_recognized = 10000
	max_recognized = 0

	while COMBINATION_OCCURRED:

		tries += 1
		if tries > MAX_TRIES:
			print('Column combining step has reached max tries')
			sys.exit()

		COMBINATION_OCCURRED = False

		# Go through each column and count the number of numbers. If it's above
		# ummmmm... 80%? Yeah. If it's above 0.8 mark it as containing mostly
		# numbers.

		expand_these: list[list[CELL]] = []
		for column in column_dictionary.values():

			was_number = any([w in was_number_at_some_point for w in column])

			has_sufficient_ratio = False

			if not was_number:
				for word in column:
					if len(word.text) < 4:
						continue
					count_numeric = sum([1 if re.match(r'[\d,$]', c) else 0 for c in word.text])
					if count_numeric / len(word.text) > COLUMN_NUMBER_MIN_RATIO:
						has_sufficient_ratio = True
						break

			any_contained_in_bounds = False
			if not was_number or has_sufficient_ratio:
				any_contained_in_bounds = any([w.center_x < max_recognized and w.center_x > min_recognized for w in column])

			if was_number or has_sufficient_ratio or any_contained_in_bounds:
				expand_these.append(column)
				for word in column:
					was_number_at_some_point.append(word)
					word.does_contain_numbers = True
		
		# Sort expand these
		expand_these.sort(key=lambda c: c[0].col_marker)
		
		if DEBUG:
			print('There are', len(expand_these), 'columns')
			for col in expand_these:
				print(col[0].col_marker, '  '.join([c.text for c in col]))

			print()

		# Go through and find the min and max of these column's bounds
		for column in expand_these:
			for w in column:
				if w.left < min_recognized and w.text.count('_') < 2:
					min_recognized = w.left
				if w.right > max_recognized and w.text.count('_') < 2:
					max_recognized = w.right
		
		has_moved = []

		while len(expand_these) > 0:
			column = expand_these.pop()

			if len(column) == 0:
				# We combined this column with others, skip it
				continue

			col_left = min([word.left for word in column])
			col_right = max([word.right for word in column])

			# Test every other word to see if it is contained in those bounds
			for word in cell_list:

				# Don't re-move something
				if word in has_moved:
					continue

				# Skip it if it's in our column
				if word in column:
					continue

				left_inside = word.left >= col_left and word.left <= col_right
				right_inside = word.right >= col_left and word.right <= col_right
				spans_column = word.left <= col_left and word.right >= col_right

				# Skip it if it's not contained
				if not (left_inside or right_inside or spans_column):
					continue

				COMBINATION_OCCURRED = True
				has_moved.append(word)

				if DEBUG:
					print(f'Adding {word.text} from {word.col_marker} to {column[0].col_marker}')

				# Anyways... remove it from it's original column
				column_dictionary[word.col_marker].remove(word)

				# If that column is now empty, remove it from the dictionary
				if len(column_dictionary[word.col_marker]) == 0:
					del column_dictionary[word.col_marker]

				for index, column_word in enumerate(column):

					if word.row_marker != column_word.row_marker:
						continue

					# We can combine this new word with another, existing line
					
					# We can replace this index
					top = min(word.top, column_word.top)
					height = max(word.top + word.height, column_word.top + column_word.height)

					if word.center_x < column_word.center_x:
						text = word.text + column_word.text
						left = word.left
						width = column_word.right - word.left
					else:
						text = column_word.text + word.text
						left = column_word.left
						width = word.right - column_word.left
					
					replacement = CELL({
						'text': text,
						'left': left,
						'width': width,
						'top': top,
						'height': height,
						'conf': min(column_word.conf, word.conf)
					})
					
					replacement.col_marker = column[0].col_marker
					replacement.row_marker = word.row_marker

					# Reference stuff boo
					replacement.clone_onto(column[index])

					# Delete the word from the cell_list too
					cell_list.remove(word)
					
					break

				else:
					# We weren't able to find a word that was on the same row, so
					# just append it to the column
					column.append(word)
					word.col_marker = column[0].col_marker
					word.does_contain_numbers = True
					column.sort(key=lambda w: w.top)

	unique_columns: list[list[CELL]] = []
	for column in column_dictionary.values():

		was_number = any([w in was_number_at_some_point for w in column])

		# Go through and check to make sure there are no $ floating off to the
		# side in their own column
		just_dollars = all([re.match(r'[$Ss§]', c.text.strip()) for c in column])

		if was_number and not just_dollars:
			unique_columns.append(column)
			column.sort(key=lambda c: c.row_marker)
			for word in column:
				word.does_contain_numbers = True

	# Go through and remove junk characters that get in the way of our business
	# with numbers
	junk = re.compile(r'[$,Ss\-_\'=~\s.—§©:]')
	alpha = re.compile(r'[A-Za-z]')
	rv_list: list[CELL] = []
	for column in unique_columns:
		for w in column:
			# Only remove junk if we are sure it is a number string
			if len(w.text) - len(re.findall(alpha, w.text)) > 2 or len(w.text.strip()) < 3:
				w.text = re.sub(junk, '', w.text)

				if len(w.text) == 1:
					w.text = re.sub(r'\)', '', w.text)

				if len(w.text) == 0:
					rv_list.append(w)

	for w in rv_list:
		column_dictionary[w.col_marker].remove(w)
		if len(column_dictionary[w.col_marker]) == 0:
			unique_columns.remove(column_dictionary[w.col_marker])
			del column_dictionary[w.col_marker]
			# print(f'REMOGINg {w.col_marker}')

	# Get rid of straggler characters that hang out after the last column. This
	# can happen when there are... lines at the end of the scanned page.
	# First find the maximum right value in our number columns
	max_right = 0
	for column in unique_columns:
		for word in column:
			if word.right > max_right:
				max_right = word.right
	
	# Now loop through all the cells and remove any cells that have left's
	# greater than that
	for word in cell_list:
		if word.left > max_right:
			cell_list.remove(word)
			column_dictionary[word.col_marker].remove(word)
			if len(column_dictionary[word.col_marker]) == 0:
				del column_dictionary[word.col_marker]

	# We altered the input cells a bit, we we need to return our new version of them
	altered_cells = []
	for row in column_dictionary.values():
		for cell in row:
			altered_cells.append(cell)
	# for column in unique_columns:
		# print( [c.text for c in column] )

	# Sort unique_columns
	unique_columns.sort(key=lambda c: c[0].col_marker)

	return column_dictionary, altered_cells, unique_columns
