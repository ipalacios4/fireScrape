import asyncio
from twscrape import API, gather
from twscrape.logger import set_log_level

async def main():
    api = API()  # or API("path-to.db") – default is `accounts.db`

    # ADD ACCOUNTS (for CLI usage see next readme section)

    # Option 1. Adding account with cookies (more stable)
    cookies = "auth_token=0ef9b9e8cc0f44e4907cb50dcae9c014e3ef7c6e; ct0=fb08a3bcc0bcc0aea795b5ecf70ffc18d23a6f33507a61c90256021a4e500232f9282b962671918ea1a4827674865daac2fc96c1413394119a8340cfff27f0f5020d8b2215f62be70dc9d6c4ddd9d30e"
    await api.pool.add_account("hannahhween", "WuLab2025", "dummy@email.com", "dummy_password", cookies=cookies)

    # API USAGE

    # search (latest tab)
    await gather(api.search("elon musk", limit=20))  # list[Tweet]
    # change search tab (product), can be: Top, Latest (default), Media
    await gather(api.search("elon musk", limit=20, kv={"product": "Top"}))

    # tweet info
    tweet_id = 20
    await api.tweet_details(tweet_id)  # Tweet
    await gather(api.retweeters(tweet_id, limit=20))  # list[User]

    # Note: this method have small pagination from X side, like 5 tweets per query
    await gather(api.tweet_replies(tweet_id, limit=20))  # list[Tweet]

    # get user by login
    user_login = "hannahhween"
    await api.user_by_login(user_login)  # User

    # user info
    user = await api.user_by_login("hannahhween")  # Replace with any username
    user_id = user.id
    await api.user_by_id(user_id)  # User
    await gather(api.following(user_id, limit=20))  # list[User]
    await gather(api.followers(user_id, limit=20))  # list[User]
    await gather(api.verified_followers(user_id, limit=20))  # list[User]
    await gather(api.subscriptions(user_id, limit=20))  # list[User]
    await gather(api.user_tweets(user_id, limit=20))  # list[Tweet]
    await gather(api.user_tweets_and_replies(user_id, limit=20))  # list[Tweet]
    await gather(api.user_media(user_id, limit=20))  # list[Tweet]

    

    # NOTE 1: gather is a helper function to receive all data as list, FOR can be used as well:
    async for tweet in api.search("elon musk"):
        print(tweet.id, tweet.user.username, tweet.rawContent)  # tweet is `Tweet` object

    # NOTE 2: all methods have `raw` version (returns `httpx.Response` object):
    async for rep in api.search_raw("elon musk"):
        print(rep.status_code, rep.json())  # rep is `httpx.Response` object

    # change log level, default info
    set_log_level("DEBUG")

    # Tweet & User model can be converted to regular dict or json, e.g.:
    doc = await api.user_by_id(user_id)  # User
    doc.dict()  # -> python dict
    doc.json()  # -> json string

    # Get CalFire user info
    calfire_user = await api.user_by_login("CAL_FIRE")
    calfire_id = calfire_user.id

    # Search for recent tweets from CalFire mentioning "evacuation"
    query = "from:CAL_FIRE evacuation"
    tweets = await gather(api.search(query, limit=20))
    for tweet in tweets:
        print(f"Date: {tweet.date}")
        print(f"Content: {tweet.rawContent}")
        print(f"Link: https://twitter.com/CAL_FIRE/status/{tweet.id}")
        print("-" * 40)

    # Optionally, get all recent tweets from CalFire and filter for evacuation info
    # tweets = await gather(api.user_tweets(calfire_id, limit=50))
    # for tweet in tweets:
    #     if "evacuation" in tweet.rawContent.lower():
    #         print(tweet.rawContent)

    # Get user ID from username


if __name__ == "__main__":
    asyncio.run(main())
