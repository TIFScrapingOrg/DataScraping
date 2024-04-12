from __future__ import annotations
from enum import StrEnum
import re

DEBUG = False
PRINT_TABLE = False

# UGGGGGHhhhh
revenue_after_expenditure_pattern = re.compile(""
	"^over expenditures and other financing uses$|"
	"^[’! ]*(excess of )?expenditures over revenues?( and)?[’!\s.,:\s]*$|"
	"^[’!\s,]*(excess of )?(revenues? |sources )(over|and) (under )?expenditures( and)?[’!\s.,:\s]*$|"
	"^[’!\s.,: —]*(financing )?uses over revenues?[’!\s.,: —]*$|"
	"^[’!\s.,: —]*(financing sources )?over expenditures[’!\s.,: —]*|^[’!\s.,: —]*(revenues? )?over \(under\) expenditures[’!\s.,: —]*$|"
	"^.*other financing sources.*$|"
	"^.*of revenues over expen?ditures$|"
	"^[’!\s.,: —]*(revenues? )?\(?under\)? expenditures$|"
	"^over revenues$"
"", re.IGNORECASE)


full_negative_pattern = re.compile('^\(\d*\)$|^[^\(]\d*\)|^\(\d*[^\)]')


class CELL:

	def __init__(self, row) -> None:
		self.text: str = row['text']
		self.left: int = row['left']
		self.top: int = row['top']
		self.width: int = row['width']
		self.height: int = row['height']
		self.conf: float = row['conf']

		self.center_x: float = self.left + self.width / 2
		self.center_y: float = self.top + self.height / 2
		self.right: int = self.left + self.width

		self.row_marker: float = -1
		self.col_marker: float = -1

		self.does_contain_numbers: bool = False

	def __str__(self) -> str:
		print_me = f"""text: {self.text},
left: {self.left},
top: {self.top},
width: {self.width},
height: {self.height},
conf: {self.conf},
center_x: {self.center_x},
center_y: {self.center_y},
right: {self.right},
row_marker: {self.row_marker},
col_marker: {self.col_marker},
does_contain_numbers: {self.does_contain_numbers}"""
		return print_me
	
	def clone_onto(self, other: CELL) -> None:
		other.text = self.text
		other.left = self.left
		other.top = self.top
		other.width = self.width
		other.height = self.height
		other.conf = self.conf
		other.center_x = self.center_x
		other.center_y = self.center_y
		other.right = self.right
		other.row_marker = self.row_marker
		other.col_marker = self.col_marker
		other.does_contain_numbers = self.does_contain_numbers

class NUMBER_COLUMN_TYPE(StrEnum):
	CURR_YEAR = 'Current year'
	PREV_YEAR = 'Previous year'
	GOV_FUNDS = 'Governmental Funds'
	ADJUSTMTS = 'Adjustments'
	STATEMENT = 'Statement of Activities'