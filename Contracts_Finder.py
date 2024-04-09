#!/usr/bin/env python
# coding: utf-8

# In[41]:


import os
import pandas as pd
import csv

def find_sequence_with_pandas(file_path):

    df = pd.read_csv(file_path, header=None)
    y = df.loc[1,:].values[0]
    t = df.loc[1,:].values[1]
    

    no_contracts_seq = ["no", "contracts", "were", "entered"]
    no_contracts_index = 0
    
    yes_contracts_seq = ["description", "of", "certain", "external"]
    yes_contracts_index = 0
    

    for index, row in df.iterrows():

        if row[12].lower() == no_contracts_seq[no_contracts_index]:
            no_contracts_index += 1  

            if no_contracts_index == len(no_contracts_seq):

                year = row[0]
                tif_district = row[1]
                return f'{year}*{tif_district}*-1'

                break  
        else:

            no_contracts_index = 0
            
        
        
        
        if row[12].lower() == yes_contracts_seq[yes_contracts_index]:
            yes_contracts_index += 1  

            if yes_contracts_index == len(yes_contracts_seq):

                year = row[0]
                tif_district = row[1]
                return f'{year}*{tif_district}*{row[2]}'

                break  
        else:

            yes_contracts_index = 0
            


    return f'{y}*{t}*-2'

def parse_and_write_to_csv(folder_name, output_string):

    os.makedirs(folder_name, exist_ok=True)
    file_path = os.path.join(folder_name, "output.csv")
    file_exists = os.path.isfile(file_path)
    
    with open(file_path, mode='a', newline='') as file: 
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(['Year', 'TIF', 'Page'])
        if output_string: 
            data = output_string.split('*')
            writer.writerow(data)

def process_all_csv_files(input_folder, output_folder):
    for filename in os.listdir(input_folder):
        if filename.endswith(".csv"):
            file_path = os.path.join(input_folder, filename)
            contract_status = find_sequence_with_pandas(file_path)
            parse_and_write_to_csv(output_folder, contract_status)
            print(f"Processed {filename}")

input_folder = "csv_files"
output_folder = "contracts"


process_all_csv_files(input_folder, output_folder)


# In[57]:


cont_df = pd.read_csv("contracts/output.csv")
cont_df


# In[62]:


filtered_df = cont_df[cont_df['Page'] == -2]
 


# In[63]:


filtered_df


# In[ ]:





# In[ ]:




