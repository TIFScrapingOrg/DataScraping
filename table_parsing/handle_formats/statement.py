import re
import sys
import pandas as pd
from handle_formats.cell_class import full_negative_pattern, revenue_after_expenditure_pattern
from handle_formats.expenditures import Expenditures
from handle_formats.revenues import Revenues

end_of_year_pattern = re.compile('.*end of year.*$', re.IGNORECASE)
transfers_in_pattern = re.compile('.*transfers in.*$', re.IGNORECASE)
transfers_out_pattern = re.compile('.*transfers out.*$', re.IGNORECASE)
surplus_pattern = re.compile('.*surp[li]us distr[iu]bution.*$', re.IGNORECASE)

begin_of_year_pattern = re.compile('.*beginn(ing|gin) of year.*$', re.IGNORECASE)

expenditure_pattern = re.compile(""
	"[\.:|;‘_]*\s*expenditures:?$|"
	"[\.:|;‘_]*\s*expenditures\/expenses?:?$|"	# Introduced 2002_1
	"Expenditu\. 2s$|" # Edge case 1997_27
	"Expenditures/expenses: ." # Edge case 2007_46
"", re.IGNORECASE)


class Statement:

	# We just want
	# 	property tax
	# 	transfers in
	#	total expenditures
	#	transfers out
	#	re-distribution
	#   end balance
 
	# So here that means
	# 	transfers in
	# 	transfers out
	# 	re-distribution
	# 	end-balance
 
	# And for checksum
	# 	start-balance
	# 	revenue after expenditures
	
	def __init__(self, labels: pd.Series, column: pd.Series):

		self.end_balance = 0
		self.transfers_in = 0
		self.transfers_out = 0
		self.surplus = 0

		self.expenditures_index = -1
		self.revenue_after_expend_index = -1

		pattern_pairs = [
			(end_of_year_pattern, 'end_balance'),
			(transfers_in_pattern, 'transfers_in'),
			(transfers_out_pattern, 'transfers_out'),
			(surplus_pattern, 'surplus')
		]

		unmatched = []

		# Find the location of revenue and drop items up until that point

		print(len(labels))
		for index, value in labels.items():
			print(index, value, column[index])

			found_match = False

			if re.match(expenditure_pattern, value) and self.expenditures_index == -1:
				print('found expenditres')
				self.expenditures_index = index
				continue
			elif re.match(revenue_after_expenditure_pattern, value) and self.revenue_after_expend_index == -1:
				print('found rev after')
				self.revenue_after_expend_index = index
				continue

			if pd.isna(column[index]):
				print('Skipping na value')
				continue

			for pair in pattern_pairs:


				if re.match(pair[0], value):
					# Check to see if negative

					if found_match:
						print(f'Found duplicate match for {value}')
						continue


					found_match = True
					is_negative = False

					was_dirty = False
					unclean_value = None

					use_me = column[index]
					
					if re.match(full_negative_pattern, use_me):
						is_negative = True
						# We'll remove parents next
						use_me = re.sub('\(|\)', '', use_me)
					if re.match('\D', use_me, re.IGNORECASE):
						was_dirty = True
						unclean_value = use_me
						use_me = re.sub('\D', '', use_me, flags=re.IGNORECASE)
					try:
						if is_negative: use_me *= -1
						setattr(self, pair[1], use_me)
						# self[pair[1]] = int(value)
						# if is_negative: self[pair[1]] *= -1
					except ValueError as _:
						print('Number is invalid in "Statement" step')
						if is_negative:
							print('It was originally negative')
						if was_dirty:
							print(f'{use_me} was adapted from original "{unclean_value}"')
					break

			if not found_match:
				unmatched.append(value)
				print(f'Unmatched field {value}')

		if self.expenditures_index == -1:
			print(labels)
			print('No expenditure index')
			sys.exit()

		if self.revenue_after_expend_index == -1:
			print(labels)
			print('No rev after')
			sys.exit()


		self.revenue_object = Revenues(labels, column, self.expenditures_index)
		self.expenditure_object = Expenditures(labels, column, self.revenue_after_expend_index, self.expenditures_index)


		