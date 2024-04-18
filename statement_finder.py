#!/usr/bin/env python
# coding: utf-8

# In[2]:


import difflib
from difflib import SequenceMatcher
import os
import pandas as pd
import csv

import re




# In[3]:



"""
Here we create a similarty function that returns a similarity percentage of two words, the first being
one of the words from our word_list and the second being the OCR scanned word
"""

def similar(a, b):
    return SequenceMatcher(None, a.lower(), b.lower())


word_list = ['revenue', "expenditure", "balance"]







# In[4]:


def similar(a, b):
    return SequenceMatcher(None, a, b).ratio() * 100

def find_sequence_with_pandas(file_path):
    df = pd.read_csv(file_path, header=None)
    
    filtered_df = df[df.iloc[:, 8] < 560]
    y = df.loc[1,:].values[0]
    t = df.loc[1,:].values[1]
    
    yes_contracts_seq = ['revenue', "expenditure", "balance"]
    page_words = {}
    
    for index, row in filtered_df.iterrows():
        word = row[12].lower()
        word = re.sub(r'[^\w\s]', '', word)  # removes non-alphanumeric characters
        page = row[2]
        
        # Check similarity with each target word and add if similarity is over 70%
        for target_word in yes_contracts_seq:
            if similar(word, target_word) > 70:
                if page not in page_words:
                    page_words[page] = set()
                page_words[page].add(target_word)

                # Check if all words have been found on the same page
                if len(page_words[page]) == len(yes_contracts_seq):
                    year = row[0]
                    tif_district = row[1]
                    return f'{year}*{tif_district}*{page + 1}'
    
    
    
    
    
    
    
    maybe_contracts_seq = ['fund', "balance", "beginning", "of", "year"]
    maybe_contracts_index = 0

    for index, row in df.iterrows():
        word = row[12].lower()
        word = re.sub(r'[^\w\s]', '', word)  # removes non-alphanumeric characters
        page = row[2]

        if word == maybe_contracts_seq[maybe_contracts_index]:
            maybe_contracts_index += 1  

            if maybe_contracts_index == len(maybe_contracts_seq):

                year = row[0]
                tif_district = row[1]
                return f'{year},{tif_district},{row[2] + 1}'

                break  
        else:

            maybe_contracts_index = 0
        
  



    maybe_contracts_seq2 = ['cash', "and","investments", "beginning", "of", "year"]
    maybe_contracts_index2 = 0
    
    
    for index, row in df.iterrows():
        word = row[12].lower()
        word = re.sub(r'[^\w\s]', '', word)  # removes non-alphanumeric characters
        page = row[2]

        if word == maybe_contracts_seq2[maybe_contracts_index2]:
            maybe_contracts_index2 += 1  

            if maybe_contracts_index2 == len(maybe_contracts_seq2):

                year = row[0]
                tif_district = row[1]
                return f'{year},{tif_district},{row[2] + 1}'

                break  
        else:

            maybe_contracts_index2 = 0
    
    return f'{y},{t},{-1}'


# In[5]:



def parse_and_write_to_csv(folder_name, output_string):

    os.makedirs(folder_name, exist_ok=True)
    file_path = os.path.join(folder_name, "statements.csv")
    file_exists = os.path.isfile(file_path)
    
    with open(file_path, mode='a', newline='') as file: 
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Year', 'TIF', 'Page'])
        if output_string: 
            data = output_string.split(',')
            writer.writerow(data)

def process_all_csv_files(input_folder, output_folder):
    for filename in os.listdir(input_folder):
        if filename.endswith(".csv"):
            file_path = os.path.join(input_folder, filename)
            contract_status = find_sequence_with_pandas(file_path)
            parse_and_write_to_csv(output_folder, contract_status)
            print(f"Processed {filename}")


# In[88]:



input_folder = "csv_files"
output_folder = "scraped"


process_all_csv_files(input_folder, output_folder)


# In[1]:


import os
import glob
import pandas as pd
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from PIL import Image

def findBottom(year,tif,page_number):
    tif = f"{int(tif):03d}"
    filename = f"csv_files/{year}_{tif}.csv"
    
    df_bot = pd.read_csv(filename)
    filtered_df = df_bot[df_bot.iloc[:, 2] == page_number]
    
    filtered_values = filtered_df[filtered_df.iloc[:, 8] < 2600].iloc[:, 8]

    # Find the maximum value in the filtered DataFrame
    max_value = filtered_values.max()
    
    return max_value


def open_pdf_and_convert_to_image(df, base_directory):
    for index, row in df.iterrows():
        year = row['Year']
        tif = f"{row['TIF']:03}"  # Ensure TIF number is zero-padded to three digits
        page_number = row['Page'] - 1  # Adjust for zero-indexed page numbers
        
        if index == 0:
             current_year = year
                
        
        
        # Construct the directory path for the given year
        year_directory = os.path.join(base_directory, str(year))
        
        if not os.path.exists(year_directory):
            print(f"Directory for year {year} does not exist.")
            continue

        # Find the PDF file starting with 'T_TIFnumber'
        pattern = os.path.join(year_directory, f"T_{tif}_*.pdf")
        files = glob.glob(pattern)

        if not files:
            print(f"No PDF file found for TIF {tif} in year {year}.")
            continue

        # Open and convert the specified page of the first matching PDF file
        pdf_file_path = files[0]
        try:
            # Using pdf2image to convert the page to an image with specified DPI for higher resolution
            images = convert_from_path(pdf_file_path, first_page=page_number+1, last_page=page_number+1, dpi=300, poppler_path="C:/Users/wesam/OneDrive/Documents/poppler-24.02.0/Library/bin")
            if images:
                # Display the image of the specified page
                image = images[0]

                # Define the bounding box to crop the image (left, upper, right, lower)
                # Example: Crop the center of the image
                width, height = image.size
                left = 100
                top = 600
                right = width - 100
                bottom = findBottom(year,tif,page_number) + 200
 
                cropped_image = image.crop((left, top, right, bottom))

                cropped_image.show()
                print(f"Displayed {year}_{tif}")
            else:
                print(f"No content on page {page_number+1} in '{pdf_file_path}'")
        except Exception as e:
            print(f"Failed to convert page {page_number+1} in '{pdf_file_path}': {str(e)}")


# In[2]:


df = pd.read_csv('scraped/statements.csv')
filtered_df = df[df.iloc[:, 2] > 0]



base_directory = 'TIFpdfs'
open_pdf_and_convert_to_image(filtered_df, base_directory)


# In[ ]:




