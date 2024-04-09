import re
import pandas as pd

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

negative_pattern = re.compile('\^(\d+\)$')

class Revenues:

	def __init__(self, labels: pd.Series, column: pd.Series) -> None:
		self.interest: int = 0
		self.interest_other: int = 0
		self.property_tax: int = 0
		self.sales_tax: int = 0
		self.rent_pattern: int = 0
		self.miscellaneous: int = 0
		self.other: int = 0
		self.land: int = 0
		self.liquor: int = 0
		self.reimbursed: int = 0

		self.total_revenue: int = 0

		for index, value in labels.items():

			if re.match(interest_pattern, value):
				# Check to see if negative
				is_negative = False
				if re.match(negative_pattern, column.iloc[index]):
					is_negative = True
					# Remove ends
					value = value[1:-1]
				try:
					self.interest = int(value)
				except ValueError as _:
					print('Number is invalid')
					print(value, 'And it is', is_negative, 'negative')


	def total_revenues(self) -> int:
		sum = 0

		finances = [
			self.property_taxes,
			self.investment_income,
			self.sales_tax,

			self.other
		]

		profits = (gain for gain in finances if gain is not None)

		return sum(profits)