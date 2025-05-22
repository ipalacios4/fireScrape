import asyncio
from datetime import datetime, timedelta
from twscrape import API, gather
from twscrape.logger import set_log_level

async def main():
    set_log_level("DEBUG")
    api = API()

    # Add account
    cookies = "auth_token=ea932f8e3672a713cd61bbcde274c8474afac863; ct0=95e1f2aa985ba2504d922ed3dcb6e35e637378bc1370a0cd90c5c1b976836cd5481a5c8ca9bf2c845eb34e495ae29d8c3569ef6db3b4befca4215eb47057748e737e3deba5fda9d8cf5c85f0afa67e57; twid=u%3D1922701009643835392; guest_id=v1%3A174725757322191254;"
    await api.pool.add_account("hannahhween", "WuLab2025", "dummy@email.com", "dummy_password", cookies=cookies)

    keywords = ["evacuation", "order", "warning", "fire", "containment", "red flag"]
    limit = 100
    total = 0

    with open("calfire_2024_tweets.txt", "a", encoding="utf-8") as f:
        # Loop over each month in 2024
        for month in range(1, 13):
            start = datetime(2024, month, 1)
            end = datetime(2024, month + 1, 1) if month < 12 else datetime(2025, 1, 1)

            query = f"from:CAL_FIRE since:{start.date()} until:{end.date()}"
            print(f"Searching: {query}")

            try:
                tweets = await gather(api.search(query, limit=limit))
                if not tweets:
                    print(f"No tweets found for {start.strftime('%B %Y')}")
                    continue

                for tweet in tweets:
                    content = tweet.rawContent.lower()
                    if any(k in content for k in keywords):
                        f.write(f"Date: {tweet.date}\n")
                        f.write(f"Content: {tweet.rawContent}\n")
                        f.write(f"Link: https://twitter.com/CAL_FIRE/status/{tweet.id}\n")
                        f.write("-" * 40 + "\n")
                        total += 1

                print(f"Saved {len(tweets)} tweets for {start.strftime('%B %Y')}")
                await asyncio.sleep(5)

            except Exception as e:
                print(f"Error during search for {start.date()}: {e}")
                break

    print(f"Done. Total tweets written: {total}")

if __name__ == "__main__":
    asyncio.run(main())