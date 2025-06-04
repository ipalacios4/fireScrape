import asyncio
import time
from datetime import datetime
from twscrape import API, gather
from twscrape.logger import set_log_level

# Set debug level for more information
set_log_level("DEBUG")

async def get_tweets_for_year(api, year, query, max_retries=3):
    year_query = f"{query} until:{year}-12-31 since:{year}-01-01"
    retries = 0
    
    while retries < max_retries:
        try:
            print(f"Fetching tweets for {year}...")
            tweets = await gather(api.search(year_query, limit=100))
            print(f"Successfully fetched {len(tweets)} tweets for {year}")
            return year, tweets
        except Exception as e:
            retries += 1
            print(f"Error fetching tweets for {year} (attempt {retries}/{max_retries}): {e}")
            if retries < max_retries:
                # Wait before retrying (exponential backoff)
                await asyncio.sleep(2 ** retries)
            else:
                print(f"Failed to fetch tweets for {year} after {max_retries} attempts")
                return year, []

async def save_tweets_to_file(year, tweets, output_dir="tweets"):
    if not tweets:
        return
    
    # Create output directories if they don't exist
    import os
    os.makedirs(os.path.join(output_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(output_dir, "text"), exist_ok=True)
    
    # Separate tweets into image and text categories
    image_tweets = []
    text_tweets = []
    
    for tweet in tweets:
        # Check if tweet has images
        if hasattr(tweet, 'media') and tweet.media and any(m.type == 'photo' for m in tweet.media):
            image_tweets.append(tweet)
        else:
            text_tweets.append(tweet)
    
    # Save image tweets
    if image_tweets:
        filename = os.path.join(output_dir, "images", f"calfire_tweets_{year}_images.txt")
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"Image Tweets from CAL_FIRE for {year}\n")
                f.write("=" * 50 + "\n\n")
                for tweet in image_tweets:
                    f.write(f"Date: {tweet.date}\n")
                    f.write(f"Content: {tweet.rawContent}\n")
                    f.write(f"Link: https://twitter.com/CAL_FIRE/status/{tweet.id}\n")
                    # Add image URLs if available
                    if hasattr(tweet, 'media'):
                        f.write("Images:\n")
                        for media in tweet.media:
                            if media.type == 'photo':
                                f.write(f"- {media.url}\n")
                    f.write("-" * 40 + "\n")
            print(f"Successfully saved {len(image_tweets)} image tweets to {filename}")
        except Exception as e:
            print(f"Error saving image tweets for {year}: {e}")
    
    # Save text tweets
    if text_tweets:
        filename = os.path.join(output_dir, "text", f"calfire_tweets_{year}_text.txt")
        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"Text Tweets from CAL_FIRE for {year}\n")
                f.write("=" * 50 + "\n\n")
                for tweet in text_tweets:
                    f.write(f"Date: {tweet.date}\n")
                    f.write(f"Content: {tweet.rawContent}\n")
                    f.write(f"Link: https://twitter.com/CAL_FIRE/status/{tweet.id}\n")
                    f.write("-" * 40 + "\n")
            print(f"Successfully saved {len(text_tweets)} text tweets to {filename}")
        except Exception as e:
            print(f"Error saving text tweets for {year}: {e}")

async def main():
    try:
        # Initialize API
        api = API()
        
        # Add your account with cookies
        cookies = "auth_token=ea932f8e3672a713cd61bbcde274c8474afac863; ct0=95e1f2aa985ba2504d922ed3dcb6e35e637378bc1370a0cd90c5c1b976836cd5481a5c8ca9bf2c845eb34e495ae29d8c3569ef6db3b4befca4215eb47057748e737e3deba5fda9d8cf5c85f0afa67e57; twid=u%3D1922701009643835392; guest_id=v1%3A174725757322191254;"
        await api.pool.add_account("hannahhween", "WuLab2025", "dummy@email.com", "dummy_password", cookies=cookies)
        
        # Verify account login
        print("Verifying account login...")
        calfire_user = await api.user_by_login("CAL_FIRE")
        if not calfire_user:
            raise Exception("Failed to verify CAL_FIRE account")
        print("Account verification successful")
        
        # Base query
        query = "from:CAL_FIRE evacuation"
        
        # Create tasks for each year
        current_year = datetime.now().year
        start_year = 2008  # CALFIRE account creation year
        years = range(start_year, current_year + 1)
        
        print(f"Starting tweet collection for years {start_year} to {current_year}")
        
        # Create and run tasks with rate limiting
        tasks = []
        for year in years:
            tasks.append(get_tweets_for_year(api, year, query))
            # Add a small delay between task creation to avoid rate limiting
            await asyncio.sleep(1)
        
        # Run tasks concurrently
        results = await asyncio.gather(*tasks)
        
        # Process results and save to files
        for year, tweets in results:
            await save_tweets_to_file(year, tweets)
        
        print("Tweet collection completed successfully")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Cleanup
        print("Cleaning up...")
        await api.close()

if __name__ == "__main__":
    asyncio.run(main())