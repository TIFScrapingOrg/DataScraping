from expenditures import Expenditures
from revenues import Revenues

class Statement_of_Revenues:

	def __init__(self, beginning_balance) -> None:

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