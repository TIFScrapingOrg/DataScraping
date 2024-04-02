class Expenditures:
	
	def __init__(self) -> None:
		self.capital_projects = None
		self.principle_retirement = None
		self.interest = None
		self.financing_costs = None
		self.bond_issuance_costs = None

		self.other = True

	def total_expenditures(self) -> int:
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

a = Expenditures()


a.capital_projects = 5
a.financing_costs = 5

print(a.financing_costs)
print(a.capital_projects)

print(a.total_expenditures())