#!pip install apify-client
from apify_client import ApifyClient
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()  # Loads the variables from .env
apify_key = os.getenv("apify")

client = ApifyClient(apify_key)

run_input = {
    "startUrls": [
        {"url": "https://www.facebook.com/OrkhonBOET"},
        {"url": "https://www.facebook.com/p/%D0%AD%D1%80%D0%B4%D1%8D%D0%BD%D1%8D%D1%82-%D2%AE%D0%B9%D0%BB%D0%B4%D0%B2%D1%8D%D1%80-%D0%A2%D3%A8%D2%AE%D0%93-%D0%A1%D0%BF%D0%BE%D1%80%D1%82-%D1%86%D0%BE%D0%B3%D1%86%D0%BE%D0%BB%D0%B1%D0%BE%D1%80-100063474191539/"},
        {"url": "https://www.facebook.com/emcyfederation"},
        {"url": "https://www.facebook.com/ErdenetUsXK"},
        {"url": "https://www.facebook.com/Erdenet.zar24.mn"},
    ],
    "resultsLimit": 30,   # total limit, keep small for free plan
}

run = client.actor("apify/facebook-posts-scraper").call(run_input=run_input)

dataset_id = run.default_dataset_id
items = list(client.dataset(dataset_id).iterate_items())

print("Total items:", len(items))
print(items[0].keys())

df = pd.DataFrame(items)
df.to_excel("apify_facebook_posts.xlsx", index=False)
df.to_csv("apify_facebook_posts.csv", index=False, encoding="utf-8-sig")



clean_posts = []

for item in items:
    clean_posts.append({
        "text": item["text"],
        "url": item["facebookUrl"],
        "time": item["time"]
    })

df = pd.DataFrame(clean_posts)

df.to_excel("apify_facebook_post.xlsx", index=False)
df.to_csv("apify_facebook_post.csv", index=False, encoding="utf-8-sig")