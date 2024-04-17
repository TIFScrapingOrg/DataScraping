import re
import pandas as pd
from handle_formats.cell_class import full_negative_pattern
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

bond_pattern = re.compile(r'.*bond\s*issuance.*$', re.IGNORECASE)
capital_projects_pattern = re.compile(r'.*capita[li]\s*projects.*$', re.IGNORECASE)
principle_retirement_pattern = re.compile(r'.*principa[lt]\s*retirement.*$', re.IGNORECASE)
interest_pattern = re.compile(r'.*[li]nterest.*$', re.IGNORECASE)
debt_pattern = re.compile(r'.*deb[ti](\s*service)?:?.*$', re.IGNORECASE)
economic_dev_pattern = re.compile(r'.*eco[nm][oa][mn]ic\s*(deve[li]opment|projects?)?\s*(deve[li]opment|projects?)?.*$', re.IGNORECASE)

total_expenditures_pattern = re.compile(r'.*tota[l!]\sexpenditures.*$', re.IGNORECASE)


class Expenditures:

	# Debt service
	#   Principal retirement
	#   Interest
	# I believe that you can also have 'interest' outside and it's assumed to be
	# debt
	
	# Here we want
	# 	total expenditures

	def __init__(self, labels: pd.Series, column: pd.Series, revenues_after_expenditures_index: int, expenditures_index: int) -> None:

		print('Finding expenditures')
		print(expenditures_index, revenues_after_expenditures_index)

		print(labels)
		print(column)

		self._expenditures_index = expenditures_index
		self._revenues_after_expend_index = revenues_after_expenditures_index

		self.has_one_entry = False

		self.has_one_entry = revenues_after_expenditures_index - expenditures_index == 2
			
		# Limit our area to just the ones that contain expenditures
		use_labels = labels.iloc[expenditures_index: revenues_after_expenditures_index]
		use_column = column.iloc[expenditures_index: revenues_after_expenditures_index]

		self._labels = use_labels.copy().reset_index()
		self._column = use_column.copy().reset_index()
		
		self.bond_issuance_costs: int = 0
		self.capital_projects: int = 0
		self.principle_retirement: int = 0
		self.interest: int = 0
		self.debt: int = 0
		self.economic_dev: int = 0

		self.total_expenditures: int = 0

		self.hazards: list[str] = []

		if expenditures_index == -1 or revenues_after_expenditures_index == -1:
			self.hazards.append('Cannot complete expenditures object')
			return

		pattern_pairs = [
			(bond_pattern, 'bond_issuance_costs'),
			(capital_projects_pattern, 'capital_projects'),
			(principle_retirement_pattern, 'principle_retirement'),
			(interest_pattern, 'interest'),
			(debt_pattern, 'debt'),
			(economic_dev_pattern, 'economic_dev'),
			(total_expenditures_pattern, 'total_expenditures')
		]

		print(use_labels)

		for index, value in use_labels.items():

			print(index, value, use_column[index])

			number = 0
			is_negative = False
			number_na = False
			number_absent = False
			test_me = use_column[index]
			if pd.isna(test_me):
				number_na = True
				print('Field blank, setting 0')
				number = 0
			elif re.sub(r'\D', '', test_me) == '':
				number_absent = True
				print('Number is absent, set 0')
				number = 0
			else:
				if re.match(full_negative_pattern, test_me):
					is_negative = True
					# We'll remove parents next
					test_me = re.sub(r'\(|\)', '', test_me)
				if not test_me.isnumeric():
					print('Number value is non-numeric, removing symbols')
					test_me = re.sub(r'\D', '', test_me)
				number = int(test_me)
				if is_negative:
					number = -number

			# Find label
			field = labels[index]
			if pd.isna(field) or field.strip() == '':
				if number != 0:
					self.hazards.append(f'Number {number} was not attached to a field')
				# It's not going to match anything so why continue
				continue

			# Match field
			for pair in pattern_pairs:
				if re.match(pair[0], value):

					print('match for', pair[1])

					if number_na or number_absent:
						self.hazards.append(f'field "{pair[1]}" had no value attached')
						if self.has_one_entry:
							print("The 'total_expenditures' had no value because of that")
					else:
						print('setting', pair[1], number)
						setattr(self, pair[1], number)
						
						if self.has_one_entry:
							print("Found 'the one' field")
							self.total_expenditures = number
					break
			else:
				if number != 0:
					self.hazards.append(f'Number {number} was not attached to a field')

		if self.total_expenditures == 0:
			print(use_labels)
			print(use_column)
			print("Couldn't find total expenditures. Attempting replacement by adding")
			self.hazards.append('Total expenditures did not match. Guessing total by adding individual')
			self.total_expenditures = (
				self.bond_issuance_costs +
				self.capital_projects +
				self.principle_retirement +
				self.interest +
				self.debt +
				self.economic_dev
			)
		else:
			check_me = (
				self.bond_issuance_costs +
				self.capital_projects +
				self.principle_retirement +
				self.interest +
				self.debt +
				self.economic_dev
			)
			if self.total_expenditures != check_me:
				self.hazards.append('Checksum failed')
		
	def vertical_check_sum(self) -> bool:
		if self._expenditures_index == -1 or self._revenues_after_expend_index == -1:
			return False

		check_me = (self.bond_issuance_costs +
		self.capital_projects +
		self.principle_retirement +
		self.interest +
		self.debt +
		self.economic_dev)

		return check_me == self.total_expenditures
	
	def fix_self(self, labels: pd.Series, column: pd.Series, revenues_after_expenditures_index: int, expenditures_index: int, pair_name: str) -> bool:
		print(pair_name)
		print('Table looks like:')
		path_to_image = f'table_images/{pair_name}.png'
		image = mpimg.imread(path_to_image)
		plt.imshow(image)
		plt.show(block=False)
		# Limit our area to just the ones that contain expenditures
		use_labels = labels.iloc[expenditures_index: revenues_after_expenditures_index]
		use_column = column.iloc[expenditures_index: revenues_after_expenditures_index]
		temp_table = pd.DataFrame({'labels': use_labels, 'column': use_column})
		print('Current status is:')
		print('0) bond_issuance_costs: ', self.bond_issuance_costs)
		print('1) capital_projects:    ', self.capital_projects)
		print('2) principle_retirement:', self.principle_retirement)
		print('3) interest:            ', self.interest)
		print('4) debt:                ', self.debt)
		print('5) economic_dev:        ', self.economic_dev)
		print('6) total_expenditures:  ', self.total_expenditures)
		print(temp_table)
		already_fixed = input('Is this correct (y/n): ')
		if already_fixed == 'y':
			plt.clf()
			return True
		trying = input('Is this salvageable (y/n): ')
		if trying == 'n':
			plt.clf()
			return False

		un_fixable = False

		while not self.vertical_check_sum():
			print()
			print('Current status is:')
			print('0) bond_issuance_costs: ', self.bond_issuance_costs)
			print('1) capital_projects:    ', self.capital_projects)
			print('2) principle_retirement:', self.principle_retirement)
			print('3) interest:            ', self.interest)
			print('4) debt:                ', self.debt)
			print('5) economic_dev:        ', self.economic_dev)
			print('6) total_expenditures:  ', self.total_expenditures)
			print(pair_name)
			print('The vertical checksum fails')
			index = '7'
			while int(index) > 6 or int(index) < 0:
				index = input('Which index do you want to fix ')
				if not index.isnumeric():
					index = '7'
					print('Not valid number')
					continue
			field = [
				'bond_issuance_costs',
				'capital_projects',
				'principle_retirement',
				'interest',
				'debt',
				'economic_dev',
				'total_expenditures',
			][int(index)]
			correct = '0'
			got_correct = False
			while not got_correct:
				correct = input(f'What is correct value for {field} ')
				is_negative = correct[0] == '-'
				if is_negative:
					correct = correct[1:]
				if not correct.isnumeric():
					print('Not valid number')
					continue
				got_correct = True
			fix = int(correct)
			if is_negative:
				fix = -fix
			print(f'Setting {field} to {fix}')
			setattr(self, field, fix)

		if self.vertical_check_sum():
			print('Checksum passes')
		else:
			print('Checksum fails')

		input()

		plt.clf()
				
		return un_fixable
	
	def display(self):
		print('bond_issuance_costs:', self.bond_issuance_costs)
		print('capital_projects:', self.capital_projects)
		print('principle_retirement:', self.principle_retirement)
		print('interest:', self.interest)
		print('debt:', self.debt)
		print('economic_dev:', self.economic_dev)
		print('total_expenditures:', self.total_expenditures)

# a = Expenditures()


# a.capital_projects = 5
# a.financing_costs = 5

# print(a.financing_costs)
# print(a.capital_projects)

# print(a.total_expenditures())
