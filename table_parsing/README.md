# The purpose of this folder
This folder is for the purposes of testing and creating scripts to analyze and pull out Statement of Revenues information.
The final result of all of the testing is in find_revenue_statements.py and the files it imports.

This folder won't exist in the final submission, but it will contain all of testing and work I did up until that point.

## What it needs to run
For it to run, it needs, at the bare minimum, a copy of all of the csv's that came out of OCR testing.
By default, they should be put into a folder called parsed_pdfs inside of the main directory, but you can put them anywhere as long as you adjust the `PARSED_PDFS_DIR` variable.
If you want it to show images to you while you are doing manual corrections, you will also need a copy of all the TIF pdfs named in the format year_tifnum (e.g. 2007_13).
See Noah if you want an easy copy of those.
In order to actually produce the image files, run the code snippets inside of the find_revenue_statements.ipynb file.
The similar sounding name was a stylistic choice made by me, so don't expect it to be changed. Just like butter_json.csv and the other names inside of the TIF_Portable folder

## Notes
The thing is not necessarily the most optimized, so it is a little slow and will take a few minutes to run the first time.
It does cache results it finds, though, so that reduces the amount of work on subsequent runs.
The cache is inside of the `.txt` files, so if you change something in the code, make sure you delete the appropriate cache file before you run it again if you want to see the changes.
**DO NOT** upload those cache files to github though.
Although if you do, it's not necessarily a biggy. The cache should just reset if it doesn't recognize your computer.
