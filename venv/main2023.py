import requests
import json
import pandas as pd
import time
import re
from bs4 import BeautifulSoup
from pathlib import Path

headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.2903.86'
}

URL = "https://www.fire.ca.gov"
parkUpdates = 'https://www.fire.ca.gov/incidents/2024/7/24/park-fire/updates'
parkFire = 'https://www.fire.ca.gov/incidents/2024/7/24/park-fire'

response = requests.get(URL)
replace = 'Update as of '
filePath = Path("output.txt")



# masterURL: https://www.fire.ca.gov
# url: lives within csv datasheet (2024-2016)
# year also found within datasheet (is hardcoded to 2024 for testing purposes)

def updateExtraction(masterURL, url, year, file):

    processed_dates = set()
    arr = [] #This holds the dates for the updates
    # These are dictionaries that will create the 1 to many relationship for updates
    zones = []
    evacOrders = {}
    updates = []
    ordersList = []
    evacWarnings = {}
    warningsList = []

    # This shows up twice can be made into a small method to just call to be able to run this.
    r = requests.get(url + 'updates', headers=headers)
    if r.status_code != 200:
        print(f"ERROR\nExit code {r.status_code} for URL: {url}/updates")
        return
    else:
        soup = BeautifulSoup(r.content, 'html5lib')
        table = soup.find(class_="detail-page")
        if table and "No updates were found for this incident" in table.text:
            print(f"Skipping {url}/updates - No updates found.")
            return  # Skip processing for this incident

        # Extract all update links and their corresponding dates
        table = table.find_all('li')
        for item in table:
            date_string = item.find('a').string.replace(replace, '').strip()
            date_day = date_string.split(' at ')[0]  # Get only the date part (e.g., "August 16, 2021")
            update_url = masterURL + item.find('a').get('href')

            # Add to the list if not already processed
            if date_day not in processed_dates:
                updates.append((date_day, update_url))
                processed_dates.add(date_day)

    # Sort updates by date (ascending order)
    updates.sort(key=lambda x: pd.to_datetime(x[0]))

    # Visit each update link in chronological order
    for date, update_url in updates:
        print(f"Processing update for {date}: {update_url}")
        time.sleep(1)  # Avoid overwhelming the server
        r = requests.get(update_url, headers=headers)
        if r.status_code != 200:
            print(f"ERROR\nExit code {r.status_code} for URL: {update_url}")
            continue
        else:
            soup = BeautifulSoup(r.content, 'html5lib')

            # Extract evacuation zones
            pattern = r'\b[A-Za-z]{3}-\d{3}\b'
            evacBox = soup.find_all(class_="border border-danger-dark mt-4")
            for parent in evacBox:
                if parent.find('h2').string == 'Evacuation Zones':
                    evacOrders = list(parent.find('div', {"class": 'p-3'}).strings)

                    c = 0
                    while c < len(evacOrders):
                        if '\n' in evacOrders[c]:
                            evacOrders.pop(c)
                            continue
                        else:
                            extractedZones = re.findall(pattern, evacOrders[c])
                            if len(extractedZones) > 0:
                                zones.extend(extractedZones)
                        c += 1

    # Write results to the file
    file.write(f"Processed Dates: {', '.join(date for date, _ in updates)}\n")
    for zone in zones:
        file.write(f"{zone}\n")

    # Add two new lines after each incident's zones
    file.write("\n")
    print(f"Zones extracted: {zones}")

def main2023():
    print("Hello World")

if __name__ == '__main__':

    #somewhere here we are going to use wget to download the latest version of the cs
    # some for-loop that goes through and collects incident links 
    # we are using csv file to be able to find links
    # file = open('output.txt', 'w')
    with open('output.txt', 'w') as file:
        # Read the CSV file
        df = pd.read_csv('calFire2023.csv')
        incident = df['incident_url']
        incidentName = df['incident_name']

        # Loop through each incident and process
        for i in range(5):  # Adjust range to process all incidents in the CSV
            file.write(f"Incident Name: {incidentName[i]}\n")
            print(f"Processing: {incidentName[i]}")

            # Call the updateExtraction function with the year 2023
            updateExtraction(URL, incident[i], "2023", file)