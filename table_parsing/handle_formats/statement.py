import re
import sys
import pandas as pd
from handle_formats.cell_class import full_negative_pattern, revenue_after_expenditure_pattern
from handle_formats.expenditures import Expenditures
from handle_formats.revenues import Revenues

revenue_header_pattern = re.compile(r'^[^a-z]*revenues?(: en)?[^a-z]*$', re.IGNORECASE)

expenditure_header_pattern = re.compile(""
	r"[\.:|;‘_]*\s*expenditures:?$|"
	r"[\.:|;‘_]*\s*expenditures\/expenses?:?$|"	 # Introduced 2002_1
	r"expenditu\. 2s$|"  # Edge case 1997_27
	r"expenditures\/expenses: \."  # Edge case 2007_46
"", re.IGNORECASE)

# Make sure this is only used with match
# The alternate match is specifically for 2014_127 where 'other' was cut off
other_finance_sources_header_pattern = re.compile(r'other financ.{3} (sources\s?)?(\/?\(?uses\)?)?[:. ”]*|financing uses:', re.IGNORECASE)

transfers_in_pattern = re.compile(r'.*transfers in.*$', re.IGNORECASE)
transfers_out_pattern = re.compile(r'.*transfers? out.*$', re.IGNORECASE)
surplus_pattern = re.compile(r'.*surp[li]us distr[iu]bution.*$', re.IGNORECASE)
tax_liability_pattern = re.compile(r'tax liability distribution.*', re.IGNORECASE)
debt_plus_bond_refund_pattern = re.compile(r'^.*proceeds of debt.*|and refunding expenses \(note 2\)', re.IGNORECASE)  # Specifically for 1999 and 2000_31
escrow_agent_pattern = re.compile(r'payment to refunded bond escrow agent', re.IGNORECASE)

total_other_finance_sources_pattern = re.compile(r'tota[li!] other financ.{3} (sources ?)?(\/?\(?uses\)?)?( ?- net)?', re.IGNORECASE)

change_in_net_position_pattern = re.compile(r'.*change in ?ne[it] ?(assets|position).*', re.IGNORECASE)

net_assets_funds_header_pattern = re.compile(r'^(’ )?fund ba[tl]ance( \(deficit\))?\/ne[it] (position|asse[ti]s).*$', re.IGNORECASE)

begin_of_year_pattern = re.compile('.*beginn(ing|gin) of year.*$', re.IGNORECASE)
end_of_year_pattern = re.compile('.*end of year.*$', re.IGNORECASE)


expenditure_header_pairs = (
	(revenue_after_expenditure_pattern, 'revenue_after_expend_index', 'index')
)

rev_after_exp_pairs = (
	(revenue_after_expenditure_pattern, 'revenues_after_expenditures', 'value'),
	(other_finance_sources_header_pattern, 'other_finance_sources_header_index', 'index'),
	(change_in_net_position_pattern, 'change_in_net_position_index', 'index'),
	(net_assets_funds_header_pattern, 'net_assets_funds_header_index', 'index'),
	(begin_of_year_pattern, 'begin_balance', 'value')
)

other_financing_pairs = (
	(transfers_in_pattern, 'transfers_in', 'value'),
	(transfers_out_pattern, 'transfers_out', 'value'),
	(surplus_pattern, 'surplus', 'value'),
	(tax_liability_pattern, 'tax_liability', 'value'),
	(debt_plus_bond_refund_pattern, 'debt_plus_bond_refund', 'value'),
	(escrow_agent_pattern, 'escrow_agent', 'value'),
	# (total_other_finance_sources_pattern, 'total_other_finance_sources_index', 'index')

	# Need to watch for a value but no label
	# ('', 'sum_all_finance', 'blank')
)

total_other_finance_pairs = (
	(total_other_finance_sources_pattern, 'total_other_finance_sources', 'value'),
	# Need to watch for a value but no label
	('', 'sum_all_finance', 'blank')
)

# Go here after value but no label
sum_all_pairs = (
	(change_in_net_position_pattern, 'change_in_net_position', 'index'),
	(net_assets_funds_header_pattern, 'net_assets_funds_header_index', 'index'),
	(begin_of_year_pattern, 'begin_balance', 'value')
)

change_net_pairs = (
	(change_in_net_position_pattern, 'change_in_net_position', 'value'),
	(net_assets_funds_header_pattern, 'net_assets_funds_header_index', 'index'),
	(begin_of_year_pattern, 'begin_balance', 'value')
)

net_asset_funds_pairs = (
	(begin_of_year_pattern, 'begin_balance', 'value')
)

begin_year_pairs = (
	(end_of_year_pattern, 'end_balance', 'value')
)


class Statement:

	# We just want
	# 	property tax
	# 	transfers in
	# 	total expenditures
	# 	transfers out
	# 	re-distribution
	#   end balance

	# So here that means
	# 	transfers in
	# 	transfers out
	# 	re-distribution
	# 	end-balance

	# And for checksum
	# 	start-balance
	# 	revenue after expenditures

	"""
	There is a general ordering of things
	
	Revenues and expenditures always follow first followed by their sum

	Immediately after that is the "other financing uses" section which itself
	contains the operating transfers among other things Operating Transfers
	Proceeds of debt. Tax liability distribution. Escrow agents

	To expand on that, "proceeds of debt place", it at least occurs in 1999_31
	and 2000_31. Marking it in unique_cases

	If there is more than one entry in the above section, then there will be a
	"total other financing uses" field below that. Or, in the case of 1999_61,
	it will have one even if there is only one entry. So look for it anyway

	If there is a other financing section, immediately after that section there
	is a "revenues + expenditures + other finances" field. All of these things
	are stated in the sum. THIS field can be extra long. So we need extra
	strings to catch it and they can overlap with previous strings AS LONG AS
	those strings have been found before

	THAT is really hard to recognize usually SO I might just say "hey yo, there
	should be a field here and if we don't find it (e.g. we find a change in net
	assets or net assets label) then raise a flag because we can't perform the
	checksum. In summary, we find a number after this and we mark it as this,
	but if someone else takes that number before we do or we take it from
	someone else, sound the alarm.


	The second to last thing is a "Change in net assets field" which does not
	contain a value in the government funds column but does contain a value in
	the adjustments and statement of activities columns

	Before the end and beginning balance, there is usually a "fund balance/net
	assets" field. This won't point to anything and if it does, flag it

	And of course last, there is the beginning of year and end of year balance
	"""

	def __init__(self, labels: pd.Series, column: pd.Series, pair_name: str):

		self.pair = pair_name

		self.revenues_index = -1
		
		self.expenditures_index = -1

		self.revenue_after_expend_index = -1
		self.revenues_after_expenditures = 0

		self.other_finance_sources_header_index = -1

		self.transfers_in = 0
		self.transfers_out = 0
		self.surplus = 0
		self.tax_liability = 0
		self.debt_plus_bond_refund = 0
		self.escrow_agent = 0

		self.total_other_finance_sources_index = -1
		self.total_other_finance_sources = 0

		self.sum_all_finance = 0

		self.change_in_net_position_index = -1
		self.change_in_net_position = 0

		self.net_assets_funds_header_index = -1

		self.begin_balance = 0
		self.begin_balance_index = -1
		self.end_balance = 0
		self.end_balance_index = -1

		self.hazards: list[str] = []

		stage = 'searching-revenue-header'
		index = 0
		FORM_COMPLETED = False
		while not FORM_COMPLETED:
			while index < len(labels):

				print(f'Index: {index} at stage: {stage}')
				print(labels.iloc[index], column.iloc[index])

				# First find the number
				number = 0
				is_negative = False
				test_me = column.iloc[index]
				number_na = False
				number_absent = False
				if pd.isna(test_me):
					number_na = True
					print('Field blank, setting 0')
					# number = 2 ** 34 + int(random.random() * 100)
					number = 0
				elif re.sub(r'\D', '', test_me) == '':
					print('Number value is absent, set 0')
					number_absent = True
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

				# After that match the field
				field = labels.iloc[index]
				if pd.isna(field):
					field = ''

				# Okay.... this is not good code, but I'm sorta thinking out loud
				# here. The idea is to create some finite state machine-esq looking
				# thing. Of course, I didn't go all the way there but you still get
				# the picture if you squint your eyes enough.
				match stage:
					case 'searching-revenue-header':                                   # Entry
						if re.match(revenue_header_pattern, field):
							self.revenues_index = index
							stage = 'searching-expenditure-header'
					
					case 'searching-expenditure-header':                               # Found revenues, next expenditures
						if re.match(expenditure_header_pattern, field):
							self.expenditures_index = index
							stage = 'searching-rev-after-exp-index'

					case 'searching-rev-after-exp-index':                              # Found expenditures, next sum rev/exp
						if re.match(revenue_after_expenditure_pattern, field):
							self.revenue_after_expend_index = index
							index -= 1
							stage = 'scanning-under-expenditures'
					
					# The previous must be found to continue processing the form

					case 'scanning-under-expenditures':                                # Where do we go after expenditures?
						if re.match(revenue_after_expenditure_pattern, field):
							if number_na or number_absent:
								self.hazards.append(f'Revenue after expenditures had no value {field, number}')
							else:
								if re.match(r'expenditures over revenues?$', field, re.IGNORECASE):
									number = -number
								self.revenues_after_expenditures = number
						elif re.match(other_finance_sources_header_pattern, field):
							self.other_finance_sources_header_index = index
							stage = 'scanning-under-other-finance-header'
						elif re.match(change_in_net_position_pattern, field):
							self.change_in_net_position_index = index
							index -= 1
							stage = 'scanning-under-net-position'
						elif re.match(net_assets_funds_header_pattern, field):
							self.net_assets_funds_header_index = index
							stage = 'scanning-under-net-assets'
						elif re.match(begin_of_year_pattern, field):
							self.begin_balance_index = index
							index -= 1
							stage = 'scanning-under-begin-year'
							if number_na or number_absent:
								self.hazards.append('Beginning of year balance has no value')
							else:
								self.begin_balance = number

					case 'scanning-under-other-finance-header':                        # Looking at other finance fields
						if re.match(total_other_finance_sources_pattern, field):
							self.total_other_finance_sources_index = index
							index -= 1
							stage = 'searching-sum-everything'
						else:
							for pair in other_financing_pairs:
								if re.match(pair[0], field):
									if number_na or number_absent:
										self.hazards.append(f'field "{pair[1]}" had no value attached')
									else:
										setattr(self, pair[1], number)
									break
							else:
								if number != 0 and not number_na and not number_absent:
									self.sum_all_finance = number
									stage = 'scanning-after-sum-all'

					case 'searching-sum-everything':                                   # Looking for the sum of EVERYTHING
						if re.match(total_other_finance_sources_pattern, field):
							if number_na or number_absent:
								self.hazards.append('Sum of everything has no value')
							else:
								self.total_other_finance_sources = number
						elif number != 0 and not number_na and not number_absent:
							self.sum_all_finance = number
							stage = 'scanning-after-sum-all'

					case 'scanning-after-sum-all':                                     # Where do we go after other finances
						if re.match(change_in_net_position_pattern, field):
							self.change_in_net_position_index = index
							index -= 1
							stage = 'scanning-under-net-position'
						elif re.match(net_assets_funds_header_pattern, field):
							self.net_assets_funds_header_index = index
							stage = 'scanning-under-net-assets'
						elif re.match(begin_of_year_pattern, field):
							self.begin_balance_index = index
							index -= 1
							stage = 'scanning-under-begin-year'
							if number_na or number_absent:
								self.hazards.append('Beginning of year balance has no value')
							else:
								self.begin_balance = number

					case 'scanning-under-net-position':                                # Where do we go after finding adjustment-shift value
						if re.match(change_in_net_position_pattern, field):
							# No hazard needed here because this will usually be 0
							# in the "Governmental Funds column"
							self.change_in_net_position = number
						if re.match(net_assets_funds_header_pattern, field):
							self.net_assets_funds_header_index = index
							stage = 'scanning-under-net-assets'
						elif re.match(begin_of_year_pattern, field):
							self.begin_balance_index = index
							index -= 1
							stage = 'scanning-under-begin-year'
							if number_na or number_absent:
								self.hazards.append('Beginning of year balance has no value')
							else:
								self.begin_balance = number

					case 'scanning-under-net-assets':                                  # Find beginning balance
						if re.match(begin_of_year_pattern, field):
							if self.begin_balance_index == -1:
								self.begin_balance_index = index
							stage = 'scanning-under-begin-year'
							if number_na or number_absent:
								self.hazards.append('Beginning of year balance has no value')
							else:
								self.begin_balance = number

					case 'scanning-under-begin-year':                                    # Find end balance
						if re.match(end_of_year_pattern, field):
							stage = 'completed'
							self.end_balance_index = index
							if number_na or number_absent:
								self.hazards.append('End of year balance has no value')
							else:
								self.end_balance = number
					
					case 'completed':                                                  # Completed stage (shouldn't go here)
						if number != 0:
							self.hazards.append(f'Number {number} found after scan completed')
							print('Found number, but scan was completed!')
							sys.exit()

				index += 1

			if stage != 'completed':
				print('Table looped over without completing!')
				print('Ended in state:', stage)

				# Force progression to the next section
				match stage:
					case 'searching-revenue-header':
						self.hazards.append("Could not find Revenues header")
						stage = 'searching-expenditure-header'
					
					case 'searching-expenditure-header':
						self.hazards.append("Could not find Expenditures header")
						stage = 'searching-rev-after-exp-index'

					case 'searching-rev-after-exp-index':
						self.hazards.append('Could not find Revenues after Expenditures')
						stage = 'scanning-under-expenditures'

					case 'scanning-under-expenditures':
						self.hazards.append('Could not find any header after expenditures. Is the table blank?')
						stage = 'scanning-under-other-finance-header'

					case 'scanning-under-other-finance-header' | 'searching-sum-everything':
						# There was NEVER a number after the other finances section.
						# We can still look for headers of lower values though.
						self.hazards.append('Could not exit other finance section')
						stage = 'scanning-after-sum-all'

					case 'scanning-after-sum-all':
						self.hazards.append('Could not find any header after other finance section. Is the table blank?')
						stage = 'scanning-under-net-position'

					case 'scanning-under-net-position':
						self.hazards.append('Could not find anything after net position. Is the table blank')
						stage = 'scanning-under-net-assets'

					case 'scanning-under-net-assets':
						self.hazards.append('Could not find beginning of year balance')
						stage = 'scanning-under-begin-year'

					case 'scanning-under-begin-year':
						self.hazards.append('Could not find end of year balance')
						stage = 'completed'

			else:
				FORM_COMPLETED = True

		if self.other_finance_sources_header_index != -1 and self.total_other_finance_sources == 0:
			self.total_other_finance_sources = (
				self.transfers_in +
				self.transfers_out +
				self.surplus +
				self.tax_liability +
				self.debt_plus_bond_refund +
				self.escrow_agent
			)
			self.hazards.append('Total of other finances did not match anything. Guessing total by adding individual')
		else:
			check_me = (
				self.transfers_in +
				self.transfers_out +
				self.surplus +
				self.tax_liability +
				self.debt_plus_bond_refund +
				self.escrow_agent
			)
			if check_me != self.total_other_finance_sources:
				self.hazards.append('Other finances checksum failed')
		
		self.revenue_object = Revenues(labels, column, self.revenues_index, self.expenditures_index)
		if not self.revenue_object.vertical_check_sum():
			print('Revenue checksum failed')
			self.hazards.append('Revenue checksum fails')
			# self.revenue_object.fix_self(pair_name)

		self.expenditure_object = Expenditures(labels, column, self.revenue_after_expend_index, self.expenditures_index)
		if not self.expenditure_object.vertical_check_sum():
			print('Expenditure checksum failed')
			self.hazards.append('Expenditure checksum fails')
			# self.expenditure_object.fix_self(labels, column, self.revenue_after_expend_index, self.expenditures_index, pair_name)

		if self.expenditures_index != -1 and self.revenue_after_expend_index != -1 and self.revenues_index != -1:

			# Correct this, the pattern is not always the same, so I figure it is easier to correct it like this
			if self.revenue_object.total_revenue - self.expenditure_object.total_expenditures == -self.revenues_after_expenditures:
				self.revenues_after_expenditures *= -1
			
			if self.revenue_object.total_revenue - self.expenditure_object.total_expenditures != self.revenues_after_expenditures:
				self.hazards.append('Revenues after expenditure checksum failed')

			elif self.other_finance_sources_header_index != -1 and self.total_other_finance_sources_index != -1:
				check_me = (
					self.revenue_object.total_revenue -
					self.expenditure_object.total_expenditures +
					self.total_other_finance_sources
				)
				if check_me != self.sum_all_finance:
					self.hazards.append('Summing all rev/exp/other checksum failed')

				elif self.begin_balance_index != -1 and self.end_balance_index != -1:
					large_check_me = check_me + self.begin_balance
					if large_check_me != self.end_balance:
						self.hazards.append('Summing everything checksum failed')
					else:
						print('Wahoo!')
				# else boohoo
				
	def revenues_and_expenditures_checksum(self):
		return self.revenue_object.total_revenue - self.expenditure_object.total_expenditures == self.revenues_after_expenditures

	def __str__(self):
		return f"""{self.pair}
Indices:
revenues_index: {self.revenues_index}
expenditures_index: {self.expenditures_index}
revenue_after_expend_index: {self.revenue_after_expend_index}
other_finance_sources_header_index: {self.other_finance_sources_header_index}
total_other_finance_sources_index: {self.total_other_finance_sources_index}
change_in_net_position_index: {self.change_in_net_position_index}
net_assets_funds_header_index: {self.net_assets_funds_header_index}
begin_balance_index: {self.begin_balance_index}
end_balance_index: {self.end_balance_index}

Values:
revenues_after_expenditures: {self.revenues_after_expenditures}
total_other_finance_sources: {self.total_other_finance_sources}
sum_all_finance: {self.sum_all_finance}
change_in_net_position: {self.change_in_net_position}
begin_balance: {self.begin_balance}
end_balance: {self.end_balance}
Other finances:
transfers_in: {self.transfers_in}
transfers_out: {self.transfers_out}
surplus: {self.surplus}
tax_liability: {self.tax_liability}
debt_plus_bond_refund: {self.debt_plus_bond_refund}
escrow_agent: {self.escrow_agent}

Hazards: {self.hazards}
"""

	def get_list_representation(self):
		# We just want
		# 	property tax
		# 	transfers in
		# 	total expenditures
		# 	transfers out
		# 	re-distribution
		#   end balance
		return [
			int(self.pair[:4]),
			int(self.pair[5:]),
			self.revenue_object.property_tax,
			self.expenditure_object.total_expenditures,
			self.transfers_in,
			self.transfers_out,
			self.surplus,
			self.end_balance,
			'|'.join(self.hazards + self.revenue_object.hazards + self.expenditure_object.hazards)
		]

	def get_full_list_representation(self):
		return [
			int(self.pair[:4]),
			int(self.pair[5:]),
			self.revenue_object.interest,
			self.revenue_object.interest_other,
			self.revenue_object.property_tax,
			self.revenue_object.sales_tax,
			self.revenue_object.rent,
			self.revenue_object.miscellaneous,
			self.revenue_object.other,
			self.revenue_object.land,
			self.revenue_object.liquor,
			self.revenue_object.reimbursed,
			self.revenue_object.total_revenue,
			
			self.expenditure_object.bond_issuance_costs,
			self.expenditure_object.capital_projects,
			self.expenditure_object.principle_retirement,
			self.expenditure_object.interest,
			# self.expenditure_object.debt,
			self.expenditure_object.economic_dev,
			self.expenditure_object.total_expenditures,
			
			self.transfers_in,
			self.transfers_out,
			self.surplus,
			self.tax_liability,
			self.debt_plus_bond_refund,
			self.escrow_agent,

			self.sum_all_finance,

			self.begin_balance,
			self.end_balance,
			'|'.join(self.hazards + self.revenue_object.hazards + self.expenditure_object.hazards)
		]
