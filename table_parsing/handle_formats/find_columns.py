from handle_formats.cell_class import CELL, DEBUG


def find_columns(cell_list: list[CELL], horizontal_threshold=10):

	# This dictionary will hold all of the columns
	column_dictionary: dict[float, list[CELL]] = {}
	
	# By default, put each word in it's own column or whatever column it happens
	# to share with others
	for word in cell_list:

		if word.right not in column_dictionary:
			column_dictionary[word.right] = []

		column_dictionary[word.right].append(word)

	# Next reduce the number of columns to what they should actually be
	REDUCED = True
	while REDUCED:

		REDUCED = False
		current_keys = sorted(list(column_dictionary.keys()))

		for i in range(len(current_keys) - 1):

			# If the distance between two keys is below threshold, combine them
			if abs(float(current_keys[i]) - float(current_keys[i+1])) <= horizontal_threshold:

				REDUCED = True
				avg = (current_keys[i] + current_keys[i+1]) / 2

				column_dictionary[avg] = column_dictionary[current_keys[i]] + column_dictionary[current_keys[i+1]]
				
				# Get rid of the original keys
				del column_dictionary[current_keys[i]]
				del column_dictionary[current_keys[i+1]]

				break

	# Go through and sort each column
	for col in column_dictionary.values():
		col.sort(key=lambda w: w.top)

	# Round of the column indices
	column_dictionary = {round(index): col for index, col in column_dictionary.items()}

	# Now go though and give each cell a col_marker
	for marker, column in column_dictionary.items():
		for cell in column:
			cell.col_marker = marker

	if DEBUG:
		for col in column_dictionary.values():
			print(col[0].col_marker, ', '.join([c.text for c in col]))

	return column_dictionary, cell_list
