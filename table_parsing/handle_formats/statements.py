from expenditures import Expenditures
from revenues import Revenues
import re
import pandas as pd

FUND_BALANCE_BEGIN = re.compile(u'.*beginning\s?of\s?year$', re.IGNORECASE)
FUND_BALANCE_END = re.compile(u'.*end\s?of\s?year$', re.IGNORECASE)

class Statement_of_Revenues:

	def __init__(self, table: pd.DataFrame) -> None:

		# Find beginning of year
		self.beginning_balance = beginning_balance
		
		self.expenditures = Expenditures()
		self.revenues = Revenues()

		self.operating_transfers = None

	def revenues_after_expenditures(self) -> int:

		sum = 0

		sum += self.revenues.total_revenues()
		sum -= self.expenditures.total_expenditures()

		return sum
	
	def ending_balance(self) -> int:

		finances = [
			self.beginning_balance,
			self.revenues_after_expenditures(),
			self.operating_transfers
		]

		gross = (cost for cost in finances if cost is not None)

		return sum(gross)