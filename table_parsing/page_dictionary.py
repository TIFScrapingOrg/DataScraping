SKIP_LIST = [
	'1998_29',  # This document seems to just be the same thing
				# repeated twice and just has estimated costs
	'1998_43',  # Same thing as 1998_29. They didn't include the report
	'2008_162',	 # There is no report but the field is "increment.expenditures"
				# as opposed to "increment expenditures" so it doesn't get
				# caught in the ignore string
	'2010_132',	 # Nothing seems to have happened in this TIF this year, but
				# it is not filled out in a conventional way
	'2010_143',  # ditto
	'2010_170',  # ditto ditto, information not present
	'2010_173',  # ditto ditto ditto
	'2010_168',  # ditto...
	'2010_171',  # ditto. No deposits >= 100_000
	'2011_159',  # Nothing over 100_000,
	'2011_162',
	'2011_168',
	'2011_170',
	'2011_173',
	'2011_174',
	'2012_132',
	'2012_168',
	'2012_170',
	'2012_173',
	'2012_174',
	'2012_175',
	'2013_168',
	'2013_170',
	'2013_173',
	'2013_174',
	'2013_175',
	'2014_168',
	'2014_170',
	'2014_173',
	'2014_174',
	'2014_175',
	'2014_176',
	'2014_177',
	'2014_178',
	'2015_168',
	'2015_170',
	'2015_174',
	'2015_175',
	'2015_176',
	'2016_168',
	'2016_170',
	'2016_175',
	'2016_179',
	'2016_180',
	'2017_170',
	'2018_182',
	'2018_181',
	'2019_183',
	'2019_184',
	'2022_186',

	# 1999 Section
	"1999_10",  # No finance
	"1999_49",  # No finance
	"1999_50",  # No finance
	"1999_57",  # No finance
	"1999_60",  # No finance
	"1999_62",  # No finance
	"1999_64",  # No finance
	"1999_67",  # No finance
	"1999_68",  # No finance
	"1999_69",  # No finance
	"1999_71",  # No finance
	"1999_73",  # No finance
	"1999_74",  # No finance
	"1999_75",  # No finance
	"1999_76",  # No finance
	"1999_77",  # No finance
	"1999_78",  # No finance
	"1999_79",  # No finance
	"1999_141",  # No finance

	# 2000 Section
	"2000_10",  # No finance
	"2000_12",  # No finance
	"2000_49",  # No finance
	"2000_51",  # No finance
	"2000_60",  # No finance
	"2000_62",  # No finance
	"2000_68",  # No finance
	"2000_76",  # No finance
	"2000_78",  # No finance
	"2000_80",  # No finance
	"2000_81",  # No finance
	"2000_82",  # No finance
	"2000_83",  # No finance
	"2000_84",  # No finance
	"2000_85",  # No finance
	"2000_87",  # No finance
	"2000_89",  # No finance
	"2000_90",  # No finance
	"2000_91",  # No finance
	"2000_92",  # No finance
	"2000_93",  # No finance
	"2000_94",  # No finance
	"2000_96",  # No finance
	"2000_98",  # No finance
	"2000_99",  # No finance
	"2000_100",  # No finance
	"2000_101",  # No finance
	"2000_102",  # No finance
	"2000_103",  # No finance

	# 2001 section
	"2001_10",  # No finance
	"2001_81",  # No finance
	"2001_83",  # No finances
	"2001_85",  # No finances
	"2001_90",  # No finance
	"2001_99",  # No finance
	"2001_103",  # No finance
	"2001_104",  # No finance
	"2001_105",  # No finance
	"2001_106",  # No finance
	"2001_107",  # No finance
	"2001_108",  # No finance
	"2001_109",  # No finance
	"2001_110",  # No finance
	"2001_111",  # No finance
	"2001_112",  # No finance
]

MANUAL_CORRECTIONS = {
	'1998_31': 24,  # Line through top of page disrupts recognition
	'1998_37': 90,  # The word 'revenues' was not scraped from the pdf
	'1998_3': 18,  # Two matches. Second match is 1997 report
	'2007_2': 14,  # Two matches. Second is only Governmental funds
	'2007_4': 14,  # ditto
	'2007_1': 14,
	'2007_3': 14,
	'2007_6': 14,
	'2009_120': 14,  # Automated process tries to fetch a later page

	# 1999 section
	"1999_1": 11,
	"1999_2": 11,
	"1999_7": 10,
	"1999_13": 11,
	"1999_15": 11,
	"1999_16": 11,
	"1999_17": 11,
	"1999_18": 11,
	"1999_19": 11,
	"1999_22": 11,
	"1999_24": 11,
	"1999_25": 11,
	"1999_26": 11,
	"1999_27": 11,
	"1999_28": 11,
	"1999_29": 11,
	"1999_30": 11,  # Previous year cut off
	"1999_31": 11,
	"1999_32": 11,
	"1999_33": 10,
	"1999_34": 11,
	"1999_36": 11,
	"1999_37": 11,
	"1999_38": 11,
	"1999_39": 11,
	"1999_40": 11,
	"1999_41": 11,
	"1999_43": 10,
	"1999_45": 11,
	"1999_47": 11,
	"1999_48": 11,
	# There should be 1999_141, rename them later
	"1999_52": 11,
	"1999_54": 10,
	"1999_59": 11,
	"1999_61": 11,
	"1999_65": 11,
	"1999_66": 11,

	# 2000 section
	"2000_1": 10,
	"2000_2": 9,
	"2000_3": 10,
	"2000_4": 10,
	"2000_5": 10,
	"2000_6": 10,
	"2000_7": 10,
	"2000_8": 10,
	"2000_9": 10,
	"2000_11": 10,
	"2000_13": 10,  # Manual???
	"2000_17": 10,
	"2000_18": 10,
	"2000_19": 10,
	"2000_20": 10,
	"2000_21": 10,
	"2000_22": 10,
	"2000_24": 10,
	"2000_25": 10,
	"2000_26": 10,
	"2000_27": 10,
	"2000_28": 10,
	"2000_29": 10,
	"2000_30": 10,
	"2000_31": 10,
	"2000_32": 10,
	"2000_33": 10,
	"2000_34": 10,
	"2000_36": 18,
	"2000_37": 10,
	"2000_38": 10,
	"2000_39": 21,
	"2000_41": 10,
	"2000_42": 10,
	"2000_43": 10,
	"2000_45": 10,
	"2000_46": 10,
	"2000_47": 10,
	"2000_52": 10,
	"2000_53": 10,
	"2000_54": 10,
	"2000_55": 10,
	"2000_56": 10,
	"2000_58": 11,
	"2000_59": 10,
	"2000_61": 10,
	"2000_63": 10,
	"2000_64": 10,
	"2000_65": 10,
	"2000_66": 10,
	"2000_69": 10,
	"2000_71": 10,
	"2000_75": 10,
	"2000_77": 107,

	# 2001 section
	"2001_1": 10,
	"2001_3": 10,
	"2001_4": 10,
	"2001_5": 10,
	"2001_6": 10,
	"2001_7": 10,
	"2001_8": 10,
	"2001_9": 10,
	"2001_11": 10,
	"2001_13": 10,
	"2001_15": 10,
	"2001_17": 10,
	"2001_18": 10,
	"2001_19": 10,
	"2001_20": 10,
	"2001_21": 10,
	"2001_22": 10,
	"2001_23": 10,
	"2001_24": 10,
	"2001_25": 10,
	"2001_26": 10,
	"2001_27": 10,
	"2001_28": 10,
	"2001_29": 9,
	"2001_30": 10,
	"2001_31": 16,
	"2001_32": 17,
	"2001_33": 10,
	"2001_34": 10,
	"2001_35": 10,
	"2001_36": 10,
	"2001_37": 10,
	"2001_38": 10,
	"2001_39": 10,
	"2001_40": 10,
	"2001_41": 10,
	"2001_42": 10,
	"2001_43": 10,
	"2001_44": 10,
	"2001_45": 10,
	"2001_46": 10,
	"2001_47": 10,
	"2001_48": 10,
	"2001_49": 10,
	"2001_50": 13,  # Manually fill?
	"2001_51": 13,  # Manually fill?
	"2001_52": 10,
	"2001_53": 10,
	"2001_54": 10,
	"2001_55": 10,
	"2001_56": 10,
	"2001_57": 10,
	"2001_58": 10,
	"2001_59": 10,
	"2001_60": 10,
	"2001_61": 10,
	"2001_62": 13,  # Manually fill?
	"2001_63": 10,
	"2001_64": 10,
	"2001_65": 10,
	"2001_66": 10,
	"2001_67": 13,  # Manually fill?
	"2001_68": 13,  # Manually fill?
	"2001_69": 10,
	"2001_71": 10,
	"2001_73": 10,
	"2001_74": 10,
	"2001_75": 10,
	"2001_76": 10,
	"2001_77": 10,
	"2001_78": 13,  # Manually fill?
	"2001_79": 13,  # Manually fill?
	"2001_82": 10,
	"2001_84": 10,
	"2001_86": 10,
	"2001_87": 10,
	"2001_88": 10,
	"2001_91": 10,
	"2001_92": 10,
	"2001_93": 10,
	"2001_94": 10,
	"2001_95": 10,
	"2001_101": 10,

}

HAND_FILLED = {
	'1998_44': 51,  # This report is a mess and frankly I'm not sure
					# if this is even right
	'2020_182': 5,  # Someone at the council is just lazy. Not formatted
	'2010_162': 7,  # Similar to 2010_143 and 132. The information does
					# seem to be there though
	'2010_159': 7,  # ditto
	'2012_159': 7,  # No exchanges >= 100_000 but data still there
	'2012_162': 7,  # ditto
	'2013_159': 7,
	'2013_162': 7,
	'2014_159': 5,
	'2015_178': 6,
	'2019_182': 5,
	'2003_14': 120,  # So many matches. This appears to be in different
					# format from previous 2 pages though.

	'2007_12': 14,  # Also not nice
	'2008_12': 14,  # Just messed up
	'2009_160': 15,  # Didn't recognize column
	'2009_166': 15,  # Didn't recognize column. It's just got 1's anyways,
	# '2013_42': 31,  # OCR put a giant line across things which messed up column recognition
	# I'm lazy at fixing
	'1997_14': 115,
	'2013_147': 540,  # OCR hallucinated some messed up stuff
	# '2002_54': 13,
	# '2004_89': 13,  # Literally same scenario as above
	# '2005_7': 13,  # Giant line messes things up
	# '2005_17': 13,  # Another line
	'2006_30': 13,  # Slanted
	'2006_102': 13,  # Slanted
	'2007_90': 14,  # Total expenditures missed
	'2007_138': 14,  # Missed ALL expenditures!
	'2007_137': 14,  # ditto
	'2009_162': 15,  # ditto
	'2015_152': 29,  # Giant box = bad
	'2002_18': 13,  # ditto
	'2014_162': 6,  # No finance, but page given

	# '2011_152': 29,  # I hate lines
	# '2011_164': 29,  # Dear lines,
	# '2014_50': 29,  # Please let me be
	# '2014_110': 30,  # OCR missed. Probably because of a line
	# '2015_36': 164,  # Sorry got distracted
	# '2015_140': 29,  # Listen, you and I
	# '2016_79': 33,  # We're on two parallel paths
	# '2016_90': 33,  # We're not going to intersect
	# '2016_122': 33,  # So please
	# '2016_167': 33,
	# '2016_174': 32,
	# '2017_74': 33,
	# '2017_179': 32,

	# 1999 section
	'1999_3': 23,  # The table was scanned, put in a field, then the
					# page was scanned
	'1999_4': 11,  # A lot of words got missed. Flagging this because
					# a lot of numbers were messed up during
					# pre-processing too
	'1999_5': 11,  # The page is slanted and lines do not line up
	'1999_6': 11,  # Top section was missed. Flagged because numbers bad
	"1999_9": 11,  # What the fuck is this scan
	'1999_11': 11,  # OCR missed column headers
	"1999_12": 13,  # Manually fill this
	'1999_14': 10,  # OCR missed investment income row
	'1999_20': 11,  # Tilted scan
	'1999_21': 11,  # ditto
	"1999_35": 13,  # Manually fill
	"1999_46": 13,  # Manual
	'1999_53': 11,  # ditto ditto
	'1999_56': 11,  # ditto ditto ditto
	'1999_44': 11,  # end of year fund is mangled
	"1999_55": 13,  # Manual
	"1999_58": 12,  # Manual, Slanted. That and only two fields recognized
	"1999_63": 13,  # Manually fill

	# 2000 section
	'2000_15': 23,  # Not the nice form
	"2000_35": 13,  # Manually fill
	"2000_50": 13,  # Manually fill
	"2000_67": 13,  # Manually fill
	"2000_73": 13,  # Manually fill
	"2000_74": 13,  # Manually fill
	"2000_79": 13,  # Manually fill

	# 2001 section
	# "2001_2": 10,  # Columns get squished together
	"2001_12": 13,  # Manually fill
	# '2001_14': 10,  # OCR's a big dumb and missed total expenditures
	'2001_69': 23,  # Iffy, I'll just make the call to manually do it
	"2001_80": 13,  # Manually fill

	'1999_18': 11,  # All revenues missing
	'2001_7': 10,  # Columns get combined. Could fix
	'2001_50': 13,  # Numbers not read. It's a weird format
	'2001_51': 13,  # Numbers not read. It's a weird format
	'2001_62': 13,  # Numbers not read. It's a weird format
	'2001_67': 13,  # Numbers not read. It's a weird format
	'2001_68': 13,  # Numbers not read. It's a weird format
	'2001_78': 13,  # Numbers not read. It's a weird format
	'2001_79': 13,  # Numbers not read. It's a weird format
	"2001_89": 13,  # Missed values
	"2001_96": 13,  # Missed column
	"2001_98": 13,  # Missed column
	"2001_100": 13,  # Missed column
	"2001_102": 13,  # Missed column

	'2004_93': 13,  # Rows do not line up. Could fix
	'2006_19': 13,  # Ditto
	'2006_53': 13,  # DITTO
	'2006_74': 13,  # Yeah
	'2006_75': 13,  # Yeah? Weird pattern
	'2006_98': 13,

	'1997_4': 21,  # The page literally is cut off. You can find the correct values in 1998_4
	# '1997_17': 21,  # Two values got cut off
	# '1998_2': 23,  # 1155 in interest misread as 2155
	'1999_13': 11,  # A lot of things missing
	'1999_17': 11,  # Lot of things misread

	'2007_14': 31,  # It's the extra large ones that are hard to process
	'2008_14': 30,  # Ditto

	# '2003_20': 13,  # Lines at bottom mean columns conflict
	# '2003_34': 13,  # Columns get squished
	# '2007_118': 14,  # Columns smooshed
	# '2008_150': 14,  # Smoooosed
	# '2002_65': 13,  # Too many _'s at the bottom
	# '2007_63': 14,  # Big line
	'2011_137': 29,  # lines are fucked
	# '2009_140': 14,  # Bigg bigg line
	'2009_157': 14,  # Bigg box?
	'2015_163': 28,  # Literally the entire adjustments column was missed by OCR somehow
	'2014_50': 29,  # NA value, something missed. Could fix
	'2014_53': 30,
}

BROUGHT_OUT = {
	'2008_154': 14,  # ditto ditto, but it did correctly get all of the data with OCR. Could fix
	'1999_33': 10,  # Misread character. Possibly negative
	"1999_42": 11,  # Fund balance end of year missing and £20,102 used there
	'1999_47': 11,  # ditto, A£098 used somewhere
	'2000_14': 15,  # OCR missed fields
	'2000_71': 10,  # Missed the one expenditure and weird char somewhere
	'2011_74': 29,  # 7 misread as /
	'2011_169': 59,  # Missed property taxes
	'2005_36': 13,  # Misread character
	'1997_44': 22,  # A lot of things got missed
	'1997_46': 21,  # Not recognized stuff
	'2005_44': 13,  # 142433 misread as {42433 for field in expenditures
	'2010_30': 97,  # 2720618 misread as 2/20618 for field in expenditures. Could fix
	'2022_185': 146,
	'2022_84': 33,
	'2019_62': 30,  # Could fix
	'2019_140': 29,
	'2003_64': 13,  # Ditto
	'2005_42': 13,  # ditto
	'2005_41': 13,  # bro it's literally the same character
	'1998_14': 35,  # This is just a nightmare to parse
	'2008_141': 14,  # Expenditures missed
	'2009_158': 15,  # Fund balance end of year not read. ALthough, it's a new tif, so it would be easy to calculate
	'2004_116': 13,  # Missed only expenditure
	'2006_93': 13,  # Missed total revenue. Maybe fix with tolerance
	'2007_50': 14,  # Total revenue and interest missing
	'2009_69': 14,  # Missing total revenue, could fix
	'2010_43': 29,  # Missing only expenditure, could fix
	'2011_108': 215,  # ditto

}
