import re
import pandas as pd

bond_patter = re.compile('.*bond\s*issuance.*$', re.IGNORECASE)
debt_pattern = re.compile('.*deb[ti](\s*service)?:?.*$', re.IGNORECASE)
economic_dev_pattern = re.compile('.*eco[nm][oa][mn]ic\s*(deve[li]opment|projects?)?\s*(deve[li]opment|projects?)?.*$', re.IGNORECASE)
principle_retirement_pattern = re.compile('.*principa[lt]\s*retirement.*$', re.IGNORECASE)
interest_pattern = re.compile('.*[li]nterest.*$', re.IGNORECASE)
capital_projects_pattern = re.compile('.*capital\s*projects.*$', re.IGNORECASE)

total_expenditures_pattern = re.compile('.*tota[l!]\sexpenditures.*$', re.IGNORECASE)

negative_pattern = re.compile('\^(\d+\)$')

class Expenditures:

	# Debt service
	#	Principal retirement
	#	Interest
	# I believe that you can also have 'interest' outside and it's assumed to be
	# debt
 
	
	def __init__(self, column: pd.Series) -> None:
		self.bond_issuance_costs = 0
		self.capital_projects = 0
		self.principle_retirement = 0
		self.interest = 0
		self.financing_costs = 0
		self.bond_issuance_costs = 0

		self.other = 0

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