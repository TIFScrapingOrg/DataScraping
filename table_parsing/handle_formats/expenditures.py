import re
import sys
import pandas as pd
from handle_formats.cell_class import full_negative_pattern

bond_pattern = re.compile('.*bond\s*issuance.*$', re.IGNORECASE)
capital_projects_pattern = re.compile('.*capital\s*projects.*$', re.IGNORECASE)
principle_retirement_pattern = re.compile('.*principa[lt]\s*retirement.*$', re.IGNORECASE)
interest_pattern = re.compile('.*[li]nterest.*$', re.IGNORECASE)
debt_pattern = re.compile('.*deb[ti](\s*service)?:?.*$', re.IGNORECASE)
economic_dev_pattern = re.compile('.*eco[nm][oa][mn]ic\s*(deve[li]opment|projects?)?\s*(deve[li]opment|projects?)?.*$', re.IGNORECASE)

total_expenditures_pattern = re.compile('.*tota[l!]\sexpenditures.*$', re.IGNORECASE)


class Expenditures:

	# Debt service
	#	Principal retirement
	#	Interest
	# I believe that you can also have 'interest' outside and it's assumed to be
	# debt
	
	# Here we want
	# 	total expenditures
 
	
	def __init__(self, labels: pd.Series, column: pd.Series, revenues_after_expenditures_index: int, expenditures_index: int) -> None:

		print('indices')
		print(expenditures_index, revenues_after_expenditures_index)

		print(labels)
		print(column)

		has_one_entry = False
		if revenues_after_expenditures_index - expenditures_index == 2:
			self.total_expenditures = int(column[revenues_after_expenditures_index - 1])
			print('I Have one!')
			has_one_entry = True
		else:
			self.total_expenditures = 0

		# Limit our area to just the ones that contain expenditures
		use_labels = labels.iloc[expenditures_index : revenues_after_expenditures_index]
		use_column = column.iloc[expenditures_index : revenues_after_expenditures_index]
		
		self.bond_issuance_costs = 0
		self.capital_projects = 0
		self.principle_retirement = 0
		self.interest = 0
		self.debt = 0
		self.economic_dev = 0


		pattern_pairs = [
			(bond_pattern, 'bond_issuance_costs'),
			(capital_projects_pattern, 'capital_projects'),
			(principle_retirement_pattern, 'principle_retirement'),
			(interest_pattern, 'interest'),
			(debt_pattern, 'debt'),
			(economic_dev_pattern, 'debt'),
			(total_expenditures_pattern, 'total_expenditures')
		]

		unmatched = []

		print(use_labels)

		for index, value in use_labels.items():

			if has_one_entry: break

			if pd.isna(use_column[index]) or use_column[index].isspace():
				print('Empty value')
				if not value.isspace():
					print(f'{value} has empty value')
				continue

			found_match = False

			print('The value is:', value)
			for pair in pattern_pairs:
				if re.match(pair[0], value):
					# Check to see if negative
					is_negative = False

					print('Found match for', pair[1])

					was_dirty = False
					unclean_value = None

					use_me = use_column[index]
					
					if found_match:
						print(f'Found duplicate match for {value}')
						continue
						
					found_match = True
					
					if re.match(full_negative_pattern, use_me):

						
						is_negative = True
						# We'll remove parents next
						use_me = re.sub('\(|\)', '', use_me)
					if re.match('\D', use_me, re.IGNORECASE):
						was_dirty = True
						unclean_value = use_me
						use_me = re.sub('\D', '', use_me, flags=re.IGNORECASE)
					try:
						use_me = int(use_me)
						if is_negative: use_me *= -1
						setattr(self, pair[1], use_me)
						if has_one_entry:
							print("hey done!")
							self.total_expenditures = use_me
							break

					except ValueError as _:
						print('Number is invalid in "Statement" step')
						if is_negative:
							print('It was originally negative')
						if was_dirty:
							print(f'{use_me} was adapted from original "{unclean_value}"')
					continue

			if not found_match:
				unmatched.append(value)
				print(f'Unmatched field {value}')
		
		print(self.total_expenditures)

		if self.total_expenditures == 0:
			print(labels)
			print("Couldn't find total expenditure hey I changed!")
			sys.exit()

	def total_expenditures_check(self) -> int:
		sum = 0

		finances = [
			self.capital_projects,
			self.principle_retirement,
			self.interest,
			self.financing_costs,
			self.bond_issuance_costs,

			self.other
		]

		deficits = (loss for loss in finances if loss is not None)

		return sum(deficits)

# a = Expenditures()


# a.capital_projects = 5
# a.financing_costs = 5

# print(a.financing_costs)
# print(a.capital_projects)

# print(a.total_expenditures())