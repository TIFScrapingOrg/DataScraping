class Revenues:

	def __init__(self) -> None:
		self.property_taxes = None
		self.investment_income = None
		self.sales_tax = None

		self.other = True

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