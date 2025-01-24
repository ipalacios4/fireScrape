# CalFIRE Web Crawl 
### Main goal  
To extract zone info from text. Zone name is in ABC-###-a where 'a' is not applied to all zones. 
- Information to extract
    - Name in ABC-###-a format
    - Start date of when the zone is a warning
    - End date of when zone is a warning
    - Start date of when it moves to an order
    - End date of when a zone is out of an order (whether it goes down to a warning or just completely removes)
- All this information should be gathered and stored in a CSV file for each year 
- Each row should contain these attributes (some of these attributes are already in the provided CSV)
    - Zone Name
    - Name of incident 
    - Start date of incident (format MM,DD,YYYY)
    - End date of incident (format MM,DD,YYYY)
    - Zone warning status Start (MM, DD, YYYY)
    - Zone warning status end (MM, DD, YYYY)
    - Zone order status start (mm, dd, yyyy)
    - Zone order status end (mm, dd, yyyy)
    - incident county
    - incident acers burned
    - incident url

## Current Version

The way this project is structured is that it is built within a Python virtual environment. This is to make sure you have all the necessary packages needed without having to download them all locally. To activate the virtual environment, head over to the directory fireScrape and run the following

'''bash 
source .venv/bin/activate
'''
In case that the virtual environment these are the following packages being use in the script
- requests
- pandas
- time
- re
- BeautifulSoup
- Path

Also included in the files is calFire2024.csv and mapdataall.csv, mapdataallClean.xlsx
- calFire2024.csv is only 2024 data of incidents for testing and only contains the incidents for 2024. There are less columns in calFire2024.csv is derived from mapdataallClean.xlsx
- mapdataallClean.xlsx is a removes unwanted columns from mapadataall.csv



# Some issues that need to be done
- Break the mapdataall.csv into seperate years so that students can work on each 
    - The only concern is how seperated the code is gonna be for each year knowing that text data isn't uniform

- Text data is not uniformed
    - Some zone status start/end dates are built into paragraph while others are in an <ul> in the <div>. We have to find the best way to try to retrieve this zone data

- Zone Update status edge cases
    - There could be a possibility where a zone will start as a warning (start date) move to an order (end date for warning, start date for order) then move back down to a warning (start date warning, end date order). The question is how should we format this with in the csv file (should we override previous end date or create another row for this zone indicating this change.)