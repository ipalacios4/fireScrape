"""
This script scrapes and collects all text related to evacuation orders and warnings from California wildfires
listed on the CAL FIRE website. Unlike main.py that only extracts evacuation zone codes, this version 
keeps all text from the evacuation order and warning sections. 

It processes fire incidents from a given CSV file, fetches updates for each incident, and compiles a structured dataset 
containing full evacuation details. The script also sorts and saves the extracted data into temporary text files 
as well as a final CSV file for further analysis. 
"""

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

def updateExtraction(masterURL, url, year, file, session):
    updates = []          # Holds tuples of (date_time_str, update_url)
    zones = []            # Accumulates evacuation order zones
    warningsList = []     # Accumulates evacuation warnings
    incident_name = None

    # Fetch the main updates page for the incident
    r = session.get(url + 'updates', headers=headers)
    if r.status_code != 200:
        print(f"ERROR\nExit code {r.status_code} for URL: {url}/updates")
        return None
    else:
        soup = BeautifulSoup(r.content, 'lxml')  # Use lxml for speed
        detail_section = soup.find(class_="detail-page")
        if detail_section and "No updates were found for this incident" in detail_section.text:
            print(f"Skipping {url}/updates - No updates found.")
            return None

        # Get incident name from the h1 tag
        h1_tag = soup.find('h1')
        if h1_tag:
            full_text = h1_tag.text.strip()
            incident_name = full_text.replace(" Status Update Reports", "")

        # Extract all update links and their corresponding date strings
        li_items = detail_section.find_all('li')
        for item in li_items:
            a_tag = item.find('a')
            if a_tag and a_tag.string:
                date_string = a_tag.string.replace(replace, '').strip()
                update_url = masterURL + a_tag.get('href')
                updates.append((date_string, update_url))
    
    if not updates:
        print(f"No updates found for URL: {url}/updates")
        return None

    # Sort updates by their datetime value
    updates.sort(key=lambda x: pd.to_datetime(x[0], format='%B %d, %Y at %I:%M %p'))

    # Group updates by date (ignoring time)
    grouped_updates = {}
    for dt_str, update_url in updates:
        date_only = dt_str.split(" at ")[0]  # e.g., "April 12, 2024"
        grouped_updates.setdefault(date_only, []).append((dt_str, update_url))
    
    # Select only the first and last update for each date group
    final_updates = []
    for date_only, group in grouped_updates.items():
        if len(group) == 1:
            final_updates.append(group[0])
        else:
            final_updates.append(group[0])
            if group[-1] != group[0]:
                final_updates.append(group[-1])
    
    # Re-sort the final updates by datetime
    final_updates.sort(key=lambda x: pd.to_datetime(x[0], format='%B %d, %Y at %I:%M %p'))
    
    # Process each selected update link
    for dt, update_url in final_updates:
        print(f"Processing update for {dt}: {update_url}")
        time.sleep(0.5)  # Reduced sleep to speed up processing
        r = session.get(update_url, headers=headers)
        if r.status_code != 200:
            print(f"ERROR\nExit code {r.status_code} for URL: {update_url}")
            continue
        else:
            soup = BeautifulSoup(r.content, 'lxml')
            evacBox = soup.find_all(class_="border border-danger-dark mt-4")
            for parent in evacBox:
                h3_element = parent.find('h3', string=re.compile("Evacuation Information", re.IGNORECASE))
                if h3_element:
                    h4_orders = h3_element.find_next_sibling('h4', string=re.compile("Evacuation Orders", re.IGNORECASE))
                    h4_warnings = h3_element.find_next_sibling('h4', string=re.compile("Evacuation Warnings", re.IGNORECASE))
                    
                    # Extract Evacuation Orders
                    if h4_orders:
                        evacOrders = []
                        next_tag = h4_orders.find_next_sibling()
                        while next_tag and next_tag.name not in ['h3', 'h4']:
                            if next_tag.name in ['p', 'ul', 'li']:
                                evacOrders.append(next_tag.get_text(strip=True))
                            next_tag = next_tag.find_next_sibling()
                        zones.extend(evacOrders)
                    
                    # Extract Evacuation Warnings
                    if h4_warnings:
                        temp_warnings = []
                        next_tag = h4_warnings.find_next_sibling()
                        while next_tag and next_tag.name not in ['h3', 'h4']:
                            if next_tag.name in ['p', 'ul', 'li']:
                                temp_warnings.append(next_tag.get_text(strip=True))
                            next_tag = next_tag.find_next_sibling()
                        warningsList.extend(temp_warnings)
    
    # Write evacuation orders to the temporary file
    file.write(f"Processed Dates: {', '.join(dt for dt, _ in final_updates)}\n")
    for zone in zones:
        file.write(f"{zone}\n")
    file.write("\n")

    # Write evacuation warnings to a separate file
    with open(f"temp_warnings_{year}.txt", "a") as warning_file:
        warning_file.write(f"Processed Dates: {', '.join(dt for dt, _ in final_updates)}\n")
        for warning in warningsList:
            warning_file.write(f"{warning}\n")
        warning_file.write("\n")

    print(f"Warnings extracted: {warningsList}")

    return {
        'start_date': final_updates[0][0] if final_updates else '',
        'incident_time': final_updates[-1][0] if final_updates else '',
        'incident_name': incident_name,
        'warning_zones': warningsList,
        'order_zones': zones
    }

def main():
    csv_file = input("Please enter the name of the CSV file to process (e.g. calFire2023.csv): ")
    year = csv_file.split("calFire")[-1].split(".")[0]  # Extract year from file name
    
    try:
        output_file = f'evac_zones_{year}.csv'
        output_df = pd.DataFrame(columns=["Start Date", "Incident Time", "Incident Name",
                                          "Evacuation Warning Zones", "Evacuation Order Zones"])
        
        # Read and group incidents by incident name to avoid parallel processing of the same fire
        df = pd.read_csv(csv_file)
        df_unique = df.drop_duplicates(subset=['incident_name'])
        
        session = requests.Session()  # Use a persistent session
        
        for idx, row in df_unique.iterrows():
            print(f"Processing: {row['incident_name']}")
            with open(f"temp_zones_{year}.txt", "a") as file:
                zones_data = updateExtraction(URL, row['incident_url'], year, file, session)
            
            if zones_data is None:
                print(f"Skipping {row['incident_name']} due to no valid updates or an error.")
                continue

            new_row = {
                'Start Date': zones_data['start_date'],
                'Incident Time': zones_data['incident_time'],
                'Incident Name': zones_data['incident_name'],
                'Evacuation Warning Zones': ','.join(zones_data['warning_zones']),
                'Evacuation Order Zones': ','.join(zones_data['order_zones'])
            }
            
            output_df = pd.concat([output_df, pd.DataFrame([new_row])], ignore_index=True)
        
        # Convert "Start Date" to datetime, sort the DataFrame, and then write the ordered output to CSV
        output_df['Start Date'] = pd.to_datetime(
            output_df['Start Date'], format='%B %d, %Y at %I:%M %p', errors='coerce'
        )
        output_df.sort_values('Start Date', inplace=True)
        output_df.to_csv(output_file, index=False)
        print(f"Ordered results saved to: {output_file}")

    except FileNotFoundError:
        print(f"Error: The file '{csv_file}' was not found.")
    except pd.errors.EmptyDataError:
        print(f"Error: The file '{csv_file}' is empty.")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == '__main__':
    main()
