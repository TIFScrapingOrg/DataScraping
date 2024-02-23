import re



filename = 'Sample_transcribed_texts/1998/T_001_35thHalstedAR98_pymupdf.txt'
file = open(filename,'r')

attributes = dict()

data = file.readlines()

tifYearTrigger = re.compile('^[1-9]\d{3,}[ ]?Annual Report',re.IGNORECASE) #pattern to check for a valid date

tifNameTrigger = re.compile("ANNUAL REPORT-[ ]?([a-zA-Z0-9_ ]*)[ ]?REDEVELOPMENT",re.IGNORECASE)

tifEndYearBalTrigger = re.compile("Total liabilities and fund balance",re.IGNORECASE)

for x in range(len(data)):
    if tifYearTrigger.search(data[x]):
        if 'tif_year' in attributes.keys():
            pass
        else:
            attributes['tif_year'] = re.search(r'^[1-9]\d{3,}',data[x]).group(0)
    if tifNameTrigger.search(data[x]):
        if 'tif_name' in attributes.keys():
            pass
        else:
            attributes['tif_name'] = re.search(tifNameTrigger,data[x]).group(1)
    if tifEndYearBalTrigger.search(data[x]):
        if 'fund_balance_end' in attributes.keys():
            pass
        else:
            attributes['fund_balance_end'] = data[x+1]


print(attributes)
file.close()