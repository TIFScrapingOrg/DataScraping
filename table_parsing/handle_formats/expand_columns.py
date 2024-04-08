import re
import sys
from cell_class import CELL, DEBUG

MAX_TRIES = 20


def expand_columns(cell_list: list[CELL], column_dictionary: dict[int, list[CELL]]):
	
	tries = 0
 
	COMBINATION_OCCURRED = True

	was_number_at_some_point = []

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

			was_number = any([ w in was_number_at_some_point for w in column ])

			squashed = ''.join([word.text for word in column])
			count_numeric = sum([1 if re.match(u'[\d,$]', c) else 0 for c in squashed])

			if was_number or count_numeric / len(squashed) >= 0.6:
				expand_these.append(column)
				for word in column:
					was_number_at_some_point.append(word)
					word.does_contain_numbers = True
		
		if DEBUG:
			print('There are', len(expand_these), 'columns')
			for col in expand_these:
				print(col[0].col_marker, '  '.join([c.text for c in col]))

			print()
		
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

				if DEBUG: print(f'Adding {word.text} from {word.col_marker} to {column[0].col_marker}')

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

		was_number = any([ w in was_number_at_some_point for w in column ])

		if was_number:
			unique_columns.append(column)
			column.sort(key=lambda c: c.row_marker)
			for word in column:
				word.does_contain_numbers = True

	# We altered the input cells a bit, we we need to return our new version of them
	altered_cells = []
	for row in column_dictionary.values():
		for cell in row:
			altered_cells.append(cell)

	return column_dictionary, altered_cells, unique_columns
