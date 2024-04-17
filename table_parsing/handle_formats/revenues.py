from __future__ import annotations
import re
import pandas as pd
from handle_formats.cell_class import full_negative_pattern
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# interest_pattern = re.compile('[\(,\-_‘\'=~\s.—:]*[li]nterest[$,s\(\-_‘\'=~\s.—§:\d]*$', re.IGNORECASE)
interest_pattern = re.compile(r'.*[li]nterest.*$', re.IGNORECASE)
interest_other_pattern = re.compile(r'.*investment\sincome.*$', re.IGNORECASE)

property_tax_pattern = re.compile(r'[,\-_\'=~\s.—§©:]*property\s*tax(es)?[$,Ss\-_\'=~\s.—§©:]*$', re.IGNORECASE)
sales_tax_pattern = re.compile(r'[,\-_\'=~\s.—©:]*[5s$§]ales\s*tax(es)?$', re.IGNORECASE)
rent_pattern = re.compile(r'[,\-_\'=~\s.—§©:]*rent(al)?\s*(income|revenue)?[$,Ss\-_\'=~\s.—§©:]*$', re.IGNORECASE)
miscellaneous_pattern = re.compile(r'[,\-_\'=~\s.—§©:]*Mise?cell[ae]neous\s*(income|revenue)?\s*(\(Note \d\))?[$,Ss\-_\'=~\s.—§©:]*$', re.IGNORECASE)
# Make sure 'other' is only used in the revenue context. It catches other fields outside of revenue
other_pattern = re.compile(r'^.*other.*$', re.IGNORECASE)

land_pattern = re.compile(r'.*sale\sof\sland.*$', re.IGNORECASE)
liquor_pattern = re.compile('.*liquor.*$', re.IGNORECASE)
reimbursed_pattern = re.compile(r'.*reimbursed\srevenue.*$', re.IGNORECASE)  # Occurs in ONE place

total_rev_pattern = re.compile(""
	r"[\.:|;‘_\s-]*to[ti]a[l!] reven[u\s]es\s*[:-]*$|"
	r"tota[l!] revenues \.$|"  # 2004_44. Speck
	r"Tota[l!] reven e[sn]$"  # 2008_14 and 2006_15? Idk if these are accurate
"", re.IGNORECASE)

# Here we want
# 	property tax


class Revenues:

	# It's structured in two because we have year/statement/adjustments/governmental
	def __init__(self, labels: pd.Series, column: pd.Series, revenue_index: int, expenditures_index: int) -> None:

		print('FINDING REVENUES')

		self._revenue_index = revenue_index
		self._expenditures_index = expenditures_index

		self.has_one_entry = expenditures_index == revenue_index + 2

		use_labels = labels.iloc[revenue_index:expenditures_index]
		use_column = column.iloc[revenue_index:expenditures_index]

		self._labels = use_labels.copy().reset_index()
		self._column = use_column.copy().reset_index()

		print(use_labels)
		print(use_column)

		self.interest: int = 0
		self.interest_other: int = 0
		self.property_tax: int = 0
		self.sales_tax: int = 0
		self.rent: int = 0
		self.miscellaneous: int = 0
		self.other: int = 0
		self.land: int = 0
		self.liquor: int = 0
		self.reimbursed: int = 0

		self.total_revenue: int = 0

		self.hazards: list[str] = []

		if revenue_index == -1 or expenditures_index == -1:
			self.hazards.append('Cannot complete revenues object')
			return

		print(f'Expenditures are at index {expenditures_index}: labels: {labels[expenditures_index]}')
		
		pattern_pairs = [
			(total_rev_pattern, 'total_revenue'),
			(interest_pattern, 'interest'),
			(interest_other_pattern, 'interest_other'),
			(property_tax_pattern, 'property_tax'),
			(sales_tax_pattern, 'sales_tax'),
			(rent_pattern, 'rent'),
			(miscellaneous_pattern, 'miscellaneous'),
			(other_pattern, 'other'),
			(land_pattern, 'land'),
			(liquor_pattern, 'liquor'),
			(reimbursed_pattern, 'reimbursed'),
		]

		# rv_list = []
		# for pattern in pattern_pairs:
		# 	if pattern in corrections['']

		for index, value in use_labels.items():

			print(index, value, use_column[index])

			# Find number
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
					test_me = re.sub(r'\D', '', test_me, flags=re.IGNORECASE)
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
							print("The 'total_revenue' had no value because of that")
					else:
						print('setting', pair[1], number)
						setattr(self, pair[1], number)
						
						if self.has_one_entry:
							print("Found 'the one' field")
							self.total_revenue = number
					break
			else:
				if number != 0:
					self.hazards.append(f'Number {number} was not attached to a field')

		if self.property_tax == 0:
			print('Did this one have no property tax?')

		if self.total_revenue == 0:
			print(use_labels)
			print(use_column)
			print("Couldn't find total revenue. Attempting replacement by adding")
			self.hazards.append('Total revenue did not match. Guessing total by adding individual')
			self.total_revenue = (
				self.interest +
				self.interest_other +
				self.property_tax +
				self.sales_tax +
				self.rent +
				self.miscellaneous +
				self.other +
				self.land +
				self.liquor +
				self.reimbursed
			)
		else:
			check_me = (
				self.interest +
				self.interest_other +
				self.property_tax +
				self.sales_tax +
				self.rent +
				self.miscellaneous +
				self.other +
				self.land +
				self.liquor +
				self.reimbursed
			)

			if self.total_revenue != check_me:
				self.hazards.append('Checksum failed')

		# all_fields = [
		# 	self.interest,
		# 	self.interest_other,
		# 	self.property_tax,
		# 	self.sales_tax,
		# 	self.rent,
		# 	self.miscellaneous,
		# 	self.other,
		# 	self.land,
		# 	self.liquor,
		# 	self.reimbursed
		# ]

	def vertical_check_sum(self):
		if self._revenue_index == -1 or self._expenditures_index == -1:
			return False
		
		check_me = (self.interest +
		self.interest_other +
		self.property_tax +
		self.sales_tax +
		self.rent +
		self.miscellaneous +
		self.other +
		self.land +
		self.liquor +
		self.reimbursed)

		return check_me == self.total_revenue
	
	def fix_self(self, pair_name: str) -> bool:
		print(pair_name)
		print('Table looks like:')
		path_to_image = f'table_images/{pair_name}.png'
		image = mpimg.imread(path_to_image)
		plt.imshow(image)
		plt.show(block=False)
		
		temp_table = pd.DataFrame({'labels': self._labels, 'column': self._column})
		print('Current status is:')
		print('0) property_tax:  ', self.property_tax)
		print('1) sales_tax:     ', self.sales_tax)
		print('2) liquor tax:    ', self.liquor)
		print('3) rent:          ', self.rent)
		print('4) interest:      ', self.interest)
		print('5) investment/na: ', self.interest_other)
		print('6) other:         ', self.other)
		print('7) land:          ', self.land)
		print('8) reimbursed:    ', self.reimbursed)
		print('9) miscellaneous: ', self.miscellaneous)
		print('10) total_revenue:', self.total_revenue)
		print(temp_table)
		if self.vertical_check_sum():
			already_fixed = input('Is this correct (y/n)?: ')
			if already_fixed == 'y':
				are_you_sure = input('Type y again to confirm: ')
				if are_you_sure == 'y':
					plt.clf()
					return True
		trying = input('Is this salvageable (y/n)?: ')
		if trying == 'n':
			plt.clf()
			return False

		completed_fixing = False
		while not completed_fixing:
			while not self.vertical_check_sum():
				print()
				print('Current status is:')
				print('0) property_tax:  ', self.property_tax)
				print('1) sales_tax:     ', self.sales_tax)
				print('2) liquor tax:    ', self.liquor)
				print('3) rent:          ', self.rent)
				print('4) interest:      ', self.interest)
				print('5) investment/na: ', self.interest_other)
				print('6) other:         ', self.other)
				print('7) land:          ', self.land)
				print('8) reimbursed:    ', self.reimbursed)
				print('9) miscellaneous: ', self.miscellaneous)
				print('10) total_revenue:', self.total_revenue)
				print(pair_name)
				print('The vertical checksum fails')
				index = '11'
				while int(index) > 10 or int(index) < 0:
					index = input('Which index do you want to fix?: ')
					if not index.isnumeric():
						index = '11'
						print('Not valid number')
						continue
				field = [
					'property_tax',
					'sales_tax',
					'liquor',
					'rent',
					'interest',
					'interest_other',
					'other',
					'land',
					'reimbursed',
					'miscellaneous',
					'total_revenue',
				][int(index)]
				correct = '0'
				got_correct = False
				while not got_correct:
					correct = input(f'What is correct value for {field} (do -123 for negative, not (123))?: ')
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
				already_fixed = input('Is this correct (y/n)?: ')
				if already_fixed == 'y':
					are_you_sure = input('Type y again to confirm: ')
					if are_you_sure == 'y':
						plt.clf()
						return True
		print('Checksum fails')
		input('Waiting for confirmation to continue: ')
		plt.clf()
		
		return False

	def horizontal_check_sum(governmental_funds: Revenues, adjustments: Revenues, statement: Revenues):
		governmental_funds.passes_horizontal_checksum = statement.total_revenue - adjustments.total_revenue == governmental_funds.total_revenue

		governmental_funds.passes_whole_checksum = (
			statement.interest - adjustments.interest == governmental_funds.interest and
			statement.interest_other - adjustments.interest_other == governmental_funds.interest_other and
			statement.property_tax - adjustments.property_tax == governmental_funds.property_tax and
			statement.sales_tax - adjustments.sales_tax == governmental_funds.sales_tax and
			statement.rent - adjustments.rent == governmental_funds.rent and
			statement.miscellaneous - adjustments.miscellaneous == governmental_funds.miscellaneous and
			statement.other - adjustments.other == governmental_funds.other and
			statement.land - adjustments.land == governmental_funds.land and
			statement.liquor - adjustments.liquor == governmental_funds.liquor and
			statement.reimbursed - adjustments.reimbursed == governmental_funds.reimbursed and
			governmental_funds.passes_horizontal_checksum
		)

	def display(self):
		print('interest:', self.interest)
		print('interest_other:', self.interest_other)
		print('property_tax:', self.property_tax)
		print('sales_tax:', self.sales_tax)
		print('rent:', self.rent)
		print('miscellaneous:', self.miscellaneous)
		print('other:', self.other)
		print('land:', self.land)
		print('liquor:', self.liquor)
		print('reimbursed:', self.reimbursed)
		print('total_revenue:', self.total_revenue)
