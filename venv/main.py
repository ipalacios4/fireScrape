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


"""
Flow of this function
    - find updates list
    - collect all the update links
    - collect dates(lowkey kinda extra)
    - go through update link


Key issues
1.) Data is structured in a time series 
- The main solution is just to collect all the data points. The way the data is going to look is.
  we will have two columns per timestamp. Each of these columns will contain the codes for areas that were issued
  an evacuation order or a warning. The interesting thing about this is that we will be able to see how zones
  change from warnings to orders and maybe back to warnings or disappear. 

  Remember that once the zone is out of either of the list then it is considered safe or end date. 

Main flow of end dates
- Given update A and update B where A is a timestamp prior to B
  First we will make and store a list of all evacuation orders and warnings for A
  - different list just to be safe
  Then we make a list for B
  We will then compare list B to A and check to see if any A zones have been removed from 
  B
  If something has been removed then we will have an end date for that zone
  Columns will be labeled as Evac Order Start, Evac Order End, Evac Warning Start, Evac Warning End
  Where each of these columns will store the zone names

There are test cases where the web page will have no update reports. For these cases we just have
to check if the <div> of the Evac list exist then just leave. 
Make sure to make a boolean data point for this (will be good for sorting data)

"""
# masterURL: https://www.fire.ca.gov
# url: lives within csv datasheet (2024-2016)
# year also found within datasheet (is hardcoded to 2024 for testing purposes)

def updateExtraction(masterURL, url, year):

    '''
        Arr is what holds all the dates of an incident. The question is this...
        
        Should I be using the bucket to be able to check when a zone is offically cleared? How would this work...
        - Date is put into bucket as a key. 
        - all values of that key are then put into bucket if they are found in that date.
        - everytime we go through an update we check the date... when we do we are also check the
          zones that are pulled from new update (same date)
            - IF the zone no longer exist in that same date update then we give that zone an end date.

        - a zone has these attributes 
            - Start date evac
            - End date evac
            - location

            i will have one table that holds all zone

            one zone can have many incidents

            an incident is a seperate table 

            relationship between zone and incident is 1 to many

            incident A can have many zone
            - on incident table have 1 row to many zones

        Update table
            - Update ID
            - date of update
            - update text
            - incident ID
            - 

        Update Zones
            - zone 
            - status
            - update date
            - incident ID




Now that I have the ability to access things on the website what I have to do is these things
1. Learn to be able to curl and grab the csv file so that it's always updated.
    - make it an option that if they want to curl or not
2. start making my tables for my db. There should be 3 tables
    - Incident table (this one is repeating mutliple zones)
        - incident ID
        - zone
        - start date
        - end date
        - location
    - Update table
        - Update ID (key)
        - date of update
        - update text
        - incident ID 
    - Update Zones
        - zone
        - status
        - update date
        - incident ID

        

WHERE IS EVERYTHING LOCATED

- CSV:
    - Incident Name
    - Start of Incident 
    - End of Incident
    - County of Incident

- HTML:
    - Update's date
    - Incident Zones
    - Zone label (Warning or Order)   
    - 

What we want to do is just collect all these things and make a csv for this. Every update will be a new row for each incident.
We want to just do this to have something to show in the next meeting.

Phase 2 will to make a small db with the scheme above to make sorting things easier and extracting data for data visualizations
    '''


    arr = [] #This holds the dates for the updates
    # These are dictionaries that will create the 1 to many relationship for updates
    zones = []
    evacOrders = {}
    ordersList = []
    evacWarnings = {}
    warningsList = []

    # This shows up twice can be made into a small method to just call to be able to run this.
    r = requests.get(url+'/updates', headers=headers)
    if r.status_code != 200: 
        print("ERROR\nExit code {}".format(r.status_code))
        exit
    else:
        soup = BeautifulSoup(r.content, 'html5lib')
        table = soup.find(class_ = "detail-page") 
        table = table.find_all('li')


        for i in range(len(table)): # We go through the whole <ul> in this for-loop

            date = table[i].find('a').string.replace(replace, '')
            date = date[0:date.find(year) - 2]

            if(date not in arr): # this just gets the dates for each update NOT individual hour updates
                arr.append(date)


            time.sleep(1)
            r = requests.get(masterURL+table[i].find('a').get('href'), headers=headers)
            if r.status_code != 200: 
                print("ERROR\nExit code {}".format(r.status_code))
                exit
            else:
                soup = BeautifulSoup(r.content, 'html5lib')
                
                # Remember that these updates are in a FILO format (oldest at the bottom, Newest update up top)
                
                # So this pattern does work for what i need but there are edge cases where they list KRN-719, 720, and 724-A 
                # sequentially that it doesn't pick up the other 2 zones. Need to make it so that we can somehow detect this 
                # series of zones and extract that from the paragraph
                pattern = r'\b[A-Za-z]{3}-\d{3}\b' 
                evacBox = soup.find_all(class_="border border-danger-dark mt-4")
                for parent in evacBox:
                    if parent.find('h2').string == 'Evacuation Zones':

                        # Access to Evac Orders/Warning Text. Need to do some text processing to divide orders and warning
                        evacOrders = list(parent.find('div', {"class":'p-3'}).strings) 

                        # evacOrders is being cleaned from unwanted character. * \xa0 still shows up not a big issue.

                        c = 0
                        # I think somewhere in here I have to look for the zones
                        # The next issue after that is to determine if it is an order or warning. (hard part)
                        while(c < len(evacOrders)):
                            if '\n' in evacOrders[c]:
                                evacOrders.pop(c)
                                continue
                            else:
                                extractedZones = re.findall(pattern, evacOrders[c]) 
                                if len(extractedZones) > 0:
                                    zones.extend(extractedZones)
                            c = c + 1


            print(zones)

def main():
    print("Hello World")

if __name__ == '__main__':

    #somewhere here we are going to use wget to download the latest version of the csv

    df = pd.read_csv('calFire2024.csv')
    incident = df['incident_url']
    incidentName = df['incident_name']
    # some for-loop that goes through and collects incident links 
    # we are using csv file to be able to find links
    # file = open('output.txt', 'w')
    for i in range(90,95):
        print(incidentName[i])
        # file.write(incidentName[i] + '\n')
        updateExtraction(URL, incident[i], "2024") #remeber that year here is used just incase we need to develop this further into a solid db
    