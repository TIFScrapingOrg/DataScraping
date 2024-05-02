#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import csv
import glob
import pandas as pd
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from PIL import Image, ImageTk
import base64
from io import BytesIO
from openai import OpenAI
import time
import tkinter as tk

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
    file_path = os.path.join(folder_name, f"statements.csv")
    file_exists = os.path.isfile(file_path)
    
    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["year", "tif_number", "property_tax", "total_expenditures", "transfers_in", "transfers_out","end_balance"])
            print(f"################statements.csv created################")
        if output_string:
            data = output_string.split(',')
            writer.writerow(data)
            print(f"################statements.csv updated################")

def on_next():
    global continue_loop
    continue_loop = True  # Signal that the button has been clicked

def open_pdf_and_convert_to_image(df, base_directory):
    global continue_loop, current_image  # Declare current_image to hold the image reference

    root = tk.Tk()
    root.title("PDF Image Viewer")

    # Create a "Next" button
    next_button = tk.Button(root, text="Next", command=on_next)
    next_button.pack(side=tk.BOTTOM, pady=20)

    # Create a label to display images
    image_label = tk.Label(root)
    image_label.pack(side=tk.TOP, expand=True)

    # Set a maximum size for the images
    max_width = 1300  # Maximum width for the images
    max_height = 1000  # Maximum height for the images

    for index, row in df.iterrows():
        continue_loop = False  # Reset the flag at the start of each iteration
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
            images = convert_from_path(pdf_file_path, first_page=page_number + 1, last_page=page_number + 1, dpi=300, poppler_path="C:/Users/wesam/OneDrive/Documents/poppler-24.02.0/Library/bin")
            image = images[0]
            width, height = image.size
            left, top, right, bottom = 100, 600, width - 100, findBottom(year, tif, page_number) + 200
            cropped_image = image.crop((left, top, right, bottom))

            if cropped_image.width > max_width or cropped_image.height > max_height:
                cropped_image = cropped_image.resize((max_width, max_height), Image.Resampling.LANCZOS)


            current_image = ImageTk.PhotoImage(cropped_image)  
            image_label.config(image=current_image)
            image_label.image = current_image  

            while not continue_loop:
                root.update() 
            continue_loop = False 

        except Exception as e:
            print(f"Failed to process PDF: {e}")

    root.mainloop()


# In[ ]:


df = pd.read_csv('scraped/statements.csv')
filtered_df = df[df.iloc[:, 2] > 0]

tolookfor2 = pd.read_csv('scraped/StatementsWithOneFlag.csv')
tolookfor2_df = tolookfor2[tolookfor2.iloc[:, 0] <= 2009]
tolookfor2_df = tolookfor2_df[['Year', 'TIF']]


merged_df = pd.merge(filtered_df, tolookfor2_df, on=['Year', 'TIF'])
merged_df


base_directory = 'TIFpdfs'
open_pdf_and_convert_to_image(merged_df , base_directory)

