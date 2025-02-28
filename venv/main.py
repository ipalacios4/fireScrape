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
    evacOrders = []
    updates = []
    warningsList = []
    incident_name = None

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

        # Get incident name from the h1 tag on the updates page
        h1_tag = soup.find('h1')
        if h1_tag:
            # Extract incident name by removing "Status Update Reports" from the h1 text
            full_text = h1_tag.text.strip()
            incident_name = full_text.replace(" Status Update Reports", "")

        # Extract all update links and their corresponding dates
        table = table.find_all('li')
        for item in table:
            date_string = item.find('a').string.replace(replace, '').strip()
            # Keep the full datetime string without splitting
            datetime_str = date_string  # e.g., "September 11, 2024 at 5:54 PM"
            update_url = masterURL + item.find('a').get('href')

            # Add to the list if not already processed
            if datetime_str not in processed_dates:
                updates.append((datetime_str, update_url))
                processed_dates.add(datetime_str)

    # Sort updates by datetime (ascending order)
    updates.sort(key=lambda x: pd.to_datetime(x[0], format='%B %d, %Y at %I:%M %p'))

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
            # pattern = r'\b[A-Za-z]{3}-\d{3}\b'

            # evacBox = soup.find_all(class_="border border-danger-dark mt-4")
            # for parent in evacBox:
            #     if parent.find('h2').string == 'Evacuation Zones':
            #         evacOrders = list(parent.find('div', {"class": 'p-3'}).strings)

            #         c = 0
            #         while c < len(evacOrders):
            #             if '\n' in evacOrders[c]:
            #                 evacOrders.pop(c)
            #                 continue
            #             else:
            #                 extractedZones = re.findall(pattern, evacOrders[c])
            #                 if len(extractedZones) > 0:
            #                     zones.extend(extractedZones)
            #             c += 1
            evacBox = soup.find_all(class_="border border-danger-dark mt-4")
            for parent in evacBox:
                # Locate h3: "Evacuation Information"
                h3_element = parent.find('h3', string=re.compile("Evacuation Information", re.IGNORECASE))
                if h3_element:
                    # Find h4: "Evacuation Orders"
                    h4_element = h3_element.find_next_sibling('h4', string=re.compile("Evacuation Orders", re.IGNORECASE))
                    if h4_element:
                        evacOrders = []
                        next_tag = h4_element.find_next_sibling()

                        # Extract all text under "Evacuation Orders" until the next heading (h3/h4)
                        while next_tag and next_tag.name not in ['h3', 'h4']:
                            if next_tag.name in ['p', 'ul', 'li']:  # Only extract meaningful content
                                evacOrders.append(next_tag.get_text(strip=True))
                            next_tag = next_tag.find_next_sibling()

                        zones.extend(evacOrders)

    # Write results to the file
    file.write(f"Processed Dates: {', '.join(date for date, _ in updates)}\n")
    for zone in zones:
        file.write(f"{zone}\n")

    # Add two new lines after each incident's zones
    file.write("\n")
    print(f"Zones extracted: {zones}")

    return {
        'start_date': updates[0][0] if updates else '',  # First update date
        'incident_time': updates[-1][0] if updates else '',   # Last update date,
        'incident_name': incident_name,
        'warning_zones': warningsList,
        'order_zones': zones  # Your existing zones list
    }

def main():
    print("Hello World")

if __name__ == '__main__':

    #somewhere here we are going to use wget to download the latest version of the csv

    csv_file = input("Please enter the name of the CSV file to process (e.g. calFire2023.csv): ")
    year = csv_file.split("calFire")[-1].split(".")[0] # extracting year from file name
    
    try:
        output_file = f'evac_zones_{year}.csv'
        output_df = pd.DataFrame(columns=["Start Date", "Incident Time", 'Incident Name', "Evacuation Warning Zones", "Evacuation Order Zones"])
            
            
        df =pd.read_csv(csv_file)
        incident = df['incident_url']
        incidentName = df['incident_name']
        # loop through each incident and process
        for i in range(500, 502):
            print(f"Processing: {incidentName[i]}")

            # temp file to store the zones data
            with open(f"temp_zones_{year}.txt", "a") as file:
                zones_data = updateExtraction(URL, incident[i], year, file)
            
            new_row = {
                'Start Date': zones_data['start_date'],
                'Incident Time': zones_data['incident_time'],
                'Incident Name': zones_data['incident_name'],
                'Evacuation Warning Zones': ','.join(zones_data['warning_zones']),
                'Evacuation Order Zones': ','.join(zones_data['order_zones'])
            }
            
            output_df = pd.concat([output_df, pd.DataFrame([new_row])], ignore_index=True)
            
            
            # save to csv
            output_df.to_csv(output_file, mode='a', header=not Path(output_file).exists(), index=False)
            print(f"Results saved to: {output_file}")

    except FileNotFoundError:
        print(f"Error: The file '{csv_file}' was not found.")
    except pd.errors.EmptyDataError:
        print(f"Error: The file '{csv_file}' is empty.")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")