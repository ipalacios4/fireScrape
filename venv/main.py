import aiohttp
import asyncio
import pandas as pd
import re
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.2903.86'
}

BASE_URL = "https://www.fire.ca.gov"
UPDATE_TEXT = "Update as of "
SEMAPHORE = asyncio.Semaphore(20)  # Limit concurrent requests to 20

# Regular Expression to Match Zone Codes
ZONE_PATTERN = re.compile(r'\b(?:[A-Z]{2,}-[A-Z0-9]+|PIN\d{2}|WWD\d{2}|BLD\d{2})\b')

async def fetch(session, url):
    """Asynchronously fetches a webpage with a timeout and retries."""
    for attempt in range(2):  # Retry up to 2 times
        try:
            async with SEMAPHORE:
                async with session.get(url, headers=HEADERS, timeout=10) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        print(f"⚠️ Error {response.status} for {url}")
        except asyncio.TimeoutError:
            print(f"Timeout fetching {url}, retrying... ({attempt+1}/2)")
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
        await asyncio.sleep(1)  # Short delay before retrying
    return None

async def get_update_urls(session, incident_url):
    """Gets all update URLs for a given fire incident."""
    updates_page = await fetch(session, f"{incident_url}updates")
    if not updates_page:
        return []

    soup = BeautifulSoup(updates_page, 'html5lib')
    table = soup.find(class_="detail-page")
    if not table or "No updates were found for this incident" in table.text:
        return []

    updates = []
    for item in table.find_all('li'):
        date_string = item.find('a').string.replace(UPDATE_TEXT, '').strip()
        update_url = BASE_URL + item.find('a')['href']
        updates.append((date_string, update_url))

    # Sort updates chronologically (earliest first)
    return sorted(updates, key=lambda x: pd.to_datetime(x[0], format='%B %d, %Y at %I:%M %p'))

async def extract_evac_zones(session, update_url):
    """Extracts evacuation order and warning zones from a single update."""
    page = await fetch(session, update_url)
    if not page:
        return set(), set()

    soup = BeautifulSoup(page, 'html5lib')
    order_zones, warning_zones = set(), set()

    evac_boxes = soup.find_all(class_="border border-danger-dark mt-4")
    for parent in evac_boxes:
        h3_element = parent.find('h3', string=re.compile("Evacuation Information", re.IGNORECASE))

        if h3_element:
            h4_orders = h3_element.find_next_sibling('h4', string=re.compile("Evacuation Orders", re.IGNORECASE))
            h4_warnings = h3_element.find_next_sibling('h4', string=re.compile("Evacuation Warnings", re.IGNORECASE))

            if h4_orders:
                print(f"Found Evacuation Orders in {update_url}")
                for tag in h4_orders.find_all_next(['p', 'ul', 'li']):
                    if tag.name in ['p', 'ul', 'li']:
                        matches = ZONE_PATTERN.findall(tag.get_text(strip=True))
                        order_zones.update(matches)

            if h4_warnings:
                print(f"Found Evacuation Warnings in {update_url}")
                for tag in h4_warnings.find_all_next(['p', 'ul', 'li']):
                    if tag.name in ['p', 'ul', 'li']:
                        matches = ZONE_PATTERN.findall(tag.get_text(strip=True))
                        warning_zones.update(matches)

    return order_zones, warning_zones

async def process_fire(session, incident_url, incident_name):
    """Processes a single fire, fetching all updates and accumulating evacuation zones."""
    print(f"🔥 Processing {incident_name} ({incident_url})...")

    update_urls = await get_update_urls(session, incident_url)
    if not update_urls:
        print(f"No updates found for {incident_name}")
        return None

    # Extract start date (first update) and incident time (last update)
    start_date = update_urls[0][0] if update_urls else ''
    incident_time = update_urls[-1][0] if update_urls else ''

    # Process all updates asynchronously
    tasks = [extract_evac_zones(session, url) for _, url in update_urls]
    results = await asyncio.gather(*tasks)

    # Combine all evacuation orders and warnings across updates
    all_order_zones = set().union(*[r[0] for r in results])
    all_warning_zones = set().union(*[r[1] for r in results])

    return {
        'Incident Name': incident_name,
        'Start Date': start_date,
        'Incident Time': incident_time,
        'Evacuation Order Zones': ', '.join(sorted(all_order_zones)),
        'Evacuation Warning Zones': ', '.join(sorted(all_warning_zones))
    }

async def main():
    """Main function to process a limited number of fire incidents concurrently."""
    csv_file = input("Please enter the name of the CSV file to process (e.g. calFire2023.csv): ")
    year = csv_file.split("calFire")[-1].split(".")[0]
    output_file = f'evac_zones_{year}.csv'

    try:
        df = pd.read_csv(csv_file)
        total_fires = len(df)

        # Define the range for testing (e.g., process only 50 fires)
        start_index = 500
        end_index = min(start_index + 10, total_fires)  # Ensure it doesn't go out of bounds

        print(f"Processing fires from index {start_index} to {end_index} (total: {end_index - start_index})...")

        incident_urls = df['incident_url'][start_index:end_index].tolist()
        incident_names = df['incident_name'][start_index:end_index].tolist()

        results = []
        async with aiohttp.ClientSession() as session:
            tasks = [process_fire(session, incident_urls[i], incident_names[i]) for i in range(len(incident_urls))]
            results = await asyncio.gather(*tasks)

        # Filter out None values (failed requests)
        results = [r for r in results if r]

        # Save to CSV
        output_df = pd.DataFrame(results)
        output_df.to_csv(output_file, index=False)
        print(f"Final cleaned CSV saved as: {output_file}")

    except FileNotFoundError:
        print(f"Error: The file '{csv_file}' was not found.")
    except pd.errors.EmptyDataError:
        print(f"Error: The file '{csv_file}' is empty.")
    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")

if __name__ == '__main__':
    asyncio.run(main())
