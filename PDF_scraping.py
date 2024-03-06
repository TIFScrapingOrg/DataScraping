import os
import requests
import fitz
from bs4 import BeautifulSoup
from urllib.parse import urljoin


## Create urls

# Change years below

linkBefore_2004 = "https://www.chicago.gov/content/city/en/depts/dcd/supp_info/district-annual-reports--{}-.html"
linkBefore_2013 = "https://www.chicago.gov/content/city/en/depts/dcd/supp_info/district_annual_reports{}.html"
linkAfter_2013 = "https://www.chicago.gov/city/en/depts/dcd/supp_info/district-annual-reports--{}-.html"
start_year = 1997
end_year = 2022
years = [*range(start_year, end_year+1, 1)]

urls = []

# Generate and append URLs to the array
for year in range(start_year, end_year + 1):
    if year <= 2003:
        urls.append(linkBefore_2004.format(year))
    elif year <= 2012:
        urls.append(linkBefore_2013.format(year))
    elif year == 2022:
        urls.append("https://www.chicago.gov/city/en/depts/dcd/supp_info/district-annual-reports--2022-2.html")
    elif year == 2016:
        urls.append("https://www.chicago.gov/city/en/depts/dcd/supp_info/2016TIFAnnualReports.html")
    else:
        urls.append(linkAfter_2013.format(year))


    
for index, url in enumerate(urls):
    print(url)
    


## Download pdfs

# Function to check if the download was successful
def check_broken(save_path):
    try:
        with fitz.open(save_path) as pdf:
            if len(pdf) == 0:
                return True

    except fitz.FileDataError as file_error:
        return True
    
    return False


# Function to download PDF file
def download_pdf(url, save_path, ignore_corrupted=False):

    # Check to see if we already downloaded it
    if os.path.exists(save_path):
        print("Already have, skipping download")
        return

    response = requests.get(url, stream=True)
    with open(save_path, 'wb') as pdf_file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                pdf_file.write(chunk)

    # Check to see if the file is corrupted
    is_broken = not ignore_corrupted and check_broken(pdf_name)

    # Try again if broken
    if is_broken:
        print(f'Corrupted download of {full_url}, retrying')
        os.remove(pdf_name)
        download_pdf(full_url, pdf_name, True)

        is_broken = check_broken(pdf_name)
        if is_broken:
            # Something fishy is going on
            print(f'Cannot download {full_url}')
            os.remove(pdf_name)

                
print("Starting download...")

# Loop through each URL
for year, url in enumerate(urls):
    print(f"************************ Year {years[year]} Download Starting ************************")
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract all links with .pdf extension
    pdf_links = soup.find_all('a', href=lambda href: (href and href.endswith('.pdf')))

    # Specify the directory to save PDF files
    save_directory = 'TIFpdfs/'+str(years[year])
    os.makedirs(save_directory, exist_ok=True)

    # Download each PDF file
    for pdf_link in pdf_links:
        full_url = urljoin(url, pdf_link['href'])
        pdf_name = os.path.join(save_directory, os.path.basename(full_url))
        print(f"Downloading: {full_url}")
        download_pdf(full_url, pdf_name)
        
    print(f"************************ Year {years[year]} Download Complete ************************")
    
    
print("All Downloads complete.")