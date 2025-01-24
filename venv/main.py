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

def updateExtraction(masterURL, url, year):


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
        updateExtraction(URL, incident[i], "2024") #remember that year here is used just incase we need to develop this further into a solid db
    