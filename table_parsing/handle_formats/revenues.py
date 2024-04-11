from __future__ import annotations
import re
import sys
import pandas as pd
from handle_formats.cell_class import full_negative_pattern

# interest_pattern = re.compile('[\(,\-_‘\'=~\s.—:]*[li]nterest[$,s\(\-_‘\'=~\s.—§:\d]*$', re.IGNORECASE)
interest_pattern = re.compile('.*[li]nterest.*$', re.IGNORECASE)
interest_other_pattern = re.compile('.*investment\sincome.*$', re.IGNORECASE)

property_tax_pattern = re.compile('[,\-_\'=~\s.—§©:]*property\s*tax(es)?[$,Ss\-_\'=~\s.—§©:]*$', re.IGNORECASE)
sales_tax_pattern = re.compile('[,\-_\'=~\s.—©:]*[5s$§]ales\s*tax(es)?$', re.IGNORECASE)
rent_pattern = re.compile('[,\-_\'=~\s.—§©:]*rent(al)?\s*(income|revenue)?[$,Ss\-_\'=~\s.—§©:]*$', re.IGNORECASE)
miscellaneous_pattern = re.compile('[,\-_\'=~\s.—§©:]*Mise?cell[ae]neous\s*(income|revenue)?\s*(\(Note \d\))?[$,Ss\-_\'=~\s.—§©:]*$', re.IGNORECASE)
other_pattern = re.compile('^.*other.*$', re.IGNORECASE)

land_pattern = re.compile('.*sale\sof\sland.*$', re.IGNORECASE)
liquor_pattern = re.compile('.*liquor.*$', re.IGNORECASE)
reimbursed_pattern = re.compile('.*reimbursed\srevenue.*$', re.IGNORECASE)

total_rev_pattern = re.compile(""
	"[\.:|;‘_\s-]*to[ti]a[l!] reven[u\s]es\s*[:-]*$|"
	"tota[l!] revenues \.$|" # 2004_44. Speck
	"Tota[l!] reven e[sn]$" # 2008_14 and 2006_15? Idk if these are accurate
"", re.IGNORECASE)

# I'm too lazy to fix this right now
# TODO: Incorporate this at an earlier step, revenue SHOULD be the top row
revenue_pattern = re.compile('^[^a-z]*revenues?[^a-z]*$', re.IGNORECASE)

# Here we want
#	property tax


class Revenues:

	# It's structured in two because we have year/statement/adjustments/governmental
	def __init__(self, labels: pd.Series, column: pd.Series, expenditures_index: int) -> None:

		self.revenue_index = -1

		# First find revenues
		for index, value in labels.items():
			if pd.isna(value) or value.isspace():
				continue
			if re.match(revenue_pattern, value):
				self.revenue_index = index

		if self.revenue_index == -1:
			print(labels)
			print("Couldn't find revenue index")
			sys.exit()

		self.total_revenue: int = 0
		has_one_entry = False
		if expenditures_index == self.revenue_index + 2:
			self.total_revenue = int(column[self.revenue_index + 1])
			has_one_entry = True

		use_labels = labels.iloc[:expenditures_index]
		use_column = column.iloc[:expenditures_index]
		
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

		unmatched = []

		for index, value in use_labels.items():

			if pd.isna(use_column[index]) or use_column[index].isspace():
				print('Empty value')
				if not value.isspace():
					print(f'{value} has empty value')
				continue

			found_match = False

			for pair in pattern_pairs:
				if re.match(pair[0], value):
					# Check to see if negative
					is_negative = False

					print('matche')
					was_dirty = False
					unclean_value = None
					if found_match:
						print(f'Found duplicate match for {value}')
						continue
					
					found_match = True
					use_me = use_column[index].strip()
					if re.match(full_negative_pattern, use_me):


							
						
						is_negative = True
						# We'll remove parents next
						use_me = re.sub('\(|\)', '', use_me)
					
					print(use_me)
					if re.match('\D', use_me, re.IGNORECASE):
						was_dirty = True
						unclean_value = use_me
						use_me = re.sub('\D', '', use_me, flags=re.IGNORECASE)
						print(use_me, 'heey')
					try:
						use_me = int(use_me)
						if is_negative:
							use_me = -use_me
						print('setting', pair[1], use_me)
						print('can set int')
						setattr(self, pair[1], use_me)
					except ValueError as e:
						print('Number is invalid in "Statement" step')
						print(e)
						if is_negative:
							print('It was originally negative')
						if was_dirty:
							print(f'{use_me} was adapted from original "{unclean_value}"')

					continue

			if not found_match:
				unmatched.append(value)
				print(f'Unmatched field {value}')

		print(self.total_revenue)
		print(self.property_tax)
		if self.total_revenue == 0:
			print(use_labels)
			print(use_column)
			print("Couldn't find total revenue")
			sys.exit()

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

		# self.passes_vertical_checksum = sum(all_fields) == self.total_revenue
		# self.passes_horizontal_checksum = False
		# self.passes_whole_checksum = False
  
		

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