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
replace = 'Update as of '
filePath = Path("output_2024.txt")  # Updated output file for 2024 data


def updateExtraction(masterURL, url, year, file):
    """
    Extracts evacuation zone updates for a wildfire incident (2024).
    Saves extracted data to the specified file.
    """

    processed_dates = set()
    arr = []  # Holds update dates
    zones = []
    evacOrders = {}
    updates = []
    ordersList = []
    evacWarnings = {}
    warningsList = []

    # Fetch incident update page
    r = requests.get(url + 'updates', headers=headers)
    if r.status_code != 200:
        print(f"ERROR\nExit code {r.status_code} for URL: {url}/updates")
        return

    soup = BeautifulSoup(r.content, 'html5lib')
    table = soup.find(class_="detail-page")

    if table and "No updates were found for this incident" in table.text:
        print(f"Skipping {url}/updates - No updates found.")
        return  # Skip if no updates are available

    # Extract update links
    table = table.find_all('li')
    for item in table:
        date_string = item.find('a').string.replace(replace, '').strip()
        date_day = date_string.split(' at ')[0]  # Extract only the date part (e.g., "August 16, 2024")
        update_url = masterURL + item.find('a').get('href')

        if date_day not in processed_dates:
            updates.append((date_day, update_url))
            processed_dates.add(date_day)

    # Sort updates by date (ascending order)
    updates.sort(key=lambda x: pd.to_datetime(x[0]))

    # Process each update page
    for date, update_url in updates:
        print(f"Processing update for {date}: {update_url}")
        time.sleep(1)  # Delay to avoid overwhelming the server

        r = requests.get(update_url, headers=headers)
        if r.status_code != 200:
            print(f"ERROR\nExit code {r.status_code} for URL: {update_url}")
            continue

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

    # Write extracted data to file
    file.write(f"Processed Dates: {', '.join(date for date, _ in updates)}\n")
    for zone in zones:
        file.write(f"{zone}\n")
    file.write("\n")

    print(f"Extracted zones: {zones}")


def main2024():
    print("Hello World")


if __name__ == '__main__':
    with open('output_2024.txt', 'w') as file:
        # Read 2024 CSV file
        df = pd.read_csv('calFire2024.csv')
        incident_urls = df['incident_url']
        incident_names = df['incident_name']

        # Process each incident
        for i in range(5):  # Adjust range as needed
            file.write(f"Incident Name: {incident_names[i]}\n")
            print(f"Processing: {incident_names[i]}")

            # Call the updateExtraction function for 2024
            updateExtraction(URL, incident_urls[i], "2024", file)
