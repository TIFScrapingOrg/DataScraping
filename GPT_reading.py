#!/usr/bin/env python
# coding: utf-8

# In[27]:


import os
import csv
import glob
import pandas as pd
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from PIL import Image
import base64
from io import BytesIO
from openai import OpenAI
import time


# Define helper functions
def findBottom(year, tif, page_number):
    tif = f"{int(tif):03d}"
    filename = f"csv_files/{year}_{tif}.csv"
    df_bot = pd.read_csv(filename)
    filtered_df = df_bot[df_bot.iloc[:, 2] == page_number]
    filtered_values = filtered_df[filtered_df.iloc[:, 8] < 2600].iloc[:, 8]
    max_value = filtered_values.max()
    return max_value

def parse_and_write_to_csv(folder_name, year, output_string):
    os.makedirs(folder_name, exist_ok=True)
    file_path = os.path.join(folder_name, f"{year}_statements.csv")
    file_exists = os.path.isfile(file_path)
    
    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["property_tax", "transfers_in", "expenses", "fund_balance_end", "transfers_out", "admin_costs", "finance_costs"])
            print(f"{year}_statements.csv created")
        if output_string:
            data = output_string.split(',')
            writer.writerow(data)
            print(f"{year}_statements.csv updated")

def open_pdf_and_convert_to_image(df, base_directory):
    output_folder = "scraped/GPTstatements"
    client = OpenAI(api_key= "")  # Use environment variable for API key

    for index, row in df.iterrows():
        year = row['Year']
        tif = f"{row['TIF']:03}"  # Zero-pad TIF number
        page_number = row['Page'] - 1  # Adjust for zero-indexed page numbers
        
        
        year_directory = os.path.join(base_directory, str(year))
        
        if not os.path.exists(year_directory):
            print(f"Directory for year {year} does not exist.")
            continue

        pattern = os.path.join(year_directory, f"T_{tif}_*.pdf")
        files = glob.glob(pattern)
        if not files:
            print(f"No PDF file found for TIF {tif} in year {year}.")
            continue

        pdf_file_path = files[0]
        try:
            images = convert_from_path(pdf_file_path, first_page=page_number+1, last_page=page_number+1, dpi=300, poppler_path="C:/Users/wesam/OneDrive/Documents/poppler-24.02.0/Library/bin")
            image = images[0]
            width, height = image.size
            left, top, right, bottom = 100, 600, width - 100, findBottom(year, tif, page_number) + 200
            cropped_image = image.crop((left, top, right, bottom))
            # Convert PIL Image to base64 string
            
            
            buffered = BytesIO()
            cropped_image.save(buffered, format="JPEG", quality=50)
            img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
            
            diff = bottom - top
            time.sleep(2)
            qual = "low"
            if diff > 1200:
                qual = "high"
                
            # OpenAI API call with base64 image
            response = client.chat.completions.create(
                model='gpt-4-vision-preview', 
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Make your only output a STRING, in the following format if the values within the image is found. (, separated): [property_tax, transfers_in, expenses, fund_balance_end, transfers_out, admin_costs, finance_costs]. If there are no values found then make the value of NA. make sure there are no commas within the numbers"},
                            {
                                "type": "image_url",
                                "image_url": "data:image/jpeg;base64," + img_str
                            }
                        ],
                    }
                ],
                max_tokens=500,
            )
            output_string = response.choices[0].message.content
            print(output_string)
            parse_and_write_to_csv(output_folder, year, output_string)
        except Exception as e:
            print(f"Failed to convert page {page_number+1} in '{pdf_file_path}': {str(e)}")


# In[26]:


df = pd.read_csv('scraped/statements.csv')
filtered_df = df[df.iloc[:, 2] > 0]



base_directory = 'TIFpdfs'
open_pdf_and_convert_to_image(filtered_df, base_directory)


# In[ ]:




