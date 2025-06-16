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

## Project Structure and Files

### Core Files
- `main.py` - Main script for processing CalFIRE data and extracting zone information
- `main1.py` - Alternative version of the main script with different processing logic
- `twitter.py` - Script to scrape CalFIRE tweets, categorizing them by year and type (image/text)
- `visualize_zones.py` - Creates visualizations of evacuation zones
- `SDC_mapping.py` - Handles San Diego County specific zone mappings
- `reproject_geojson.py` - Utility script to reproject GeoJSON files to different coordinate systems

### Data Files
- `mapdataall.csv` - Complete dataset of all incidents
- `mapdataallClean.xlsx` - Cleaned version of mapdataall.csv with unwanted columns removed
- `calFire2024.csv` - 2024-specific incident data for testing
- `zone_to_fire_mapping_2020_2025.csv` - Mapping between zones and fires for 2020-2025
- `SDC_evac_zones.csv` - San Diego County specific evacuation zones
- `Evacuation_Zones.geojson` - GeoJSON file containing all evacuation zones
- `Evacuation_Zones_WGS84.geojson` - WGS84 projected version of evacuation zones
- `2025_fires.geojson` - 2025-specific fire data in GeoJSON format
- `2025-ArcGIS.csv` - 2025 fire data in ArcGIS format

### Output Files
- `2025_map.html` - Interactive map visualization for 2025 data
- `sdc_zones_map.html` - Interactive map of San Diego County zones

## Setup and Installation

1. Create and activate the virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Unix/macOS
# or
.\venv\Scripts\activate  # On Windows
```

2. Install required packages:
```bash
pip install requests pandas beautifulsoup4 twscrape
```

## How to Run

### Twitter Scraper
To scrape CalFIRE tweets:
```bash
python twitter.py
```
This will:
- Create a `tweets` directory with subdirectories for images and text
- Scrape tweets from 2008 to present
- Categorize tweets as image or text
- Save tweets in separate files by year and type

### Main Data Processing
To process CalFIRE data:
```bash
python main.py
```
This will process the main dataset and extract zone information.

### Visualization
To create zone visualizations:
```bash
python visualize_zones.py
```
This will generate interactive maps of evacuation zones.

### San Diego County Mapping
To process SDC-specific data:
```bash
python SDC_mapping.py
```
This will handle San Diego County specific zone mappings.

## Current Issues and TODOs

1. Data Separation
- Need to break mapdataall.csv into separate years
- Concern about code separation for each year due to non-uniform text data

2. Text Data Uniformity
- Zone status dates are inconsistently formatted
- Some are in paragraphs, others in lists
- Need to develop robust parsing strategy

3. Zone Update Status Edge Cases
- Handle cases where zones change status multiple times
- Need to decide between:
  - Overriding previous end dates
  - Creating new rows for status changes

## Dependencies
- requests
- pandas
- time
- re
- BeautifulSoup
- Path
- twscrape (for Twitter scraping)
- asyncio (for async operations)