import pandas as pd
import json


datas = pd.read_excel(
    "/datas/apify_facebook_posts (1).xlsx"
)

print(datas.columns)
# Result were:
#Index(['facebookUrl', 'postId', 'pageName', 'url', 'time', 'timestamp', 'user',
#    'collaborators', 'text', 'textReferences', 'likes', 'shares',
#    'topReactionsCount', 'feedbackId', 'sharedPost', 'paidPartnership',
#    'topLevelUrl', 'facebookId', 'pageAdLibrary', 'inputUrl',
#    'reactionLikeCount', 'comments', 'media', 'reactionAngryCount',
#    'reactionSadCount', 'isVideo', 'viewsCount', 'reactionLoveCount',
#    'reactionCareCount', 'reactionWowCount', 'reactionHahaCount', 'link',
#    'musicInfo'],
#   dtype='object')

all_data =[]
for index, row in datas.iterrows():
    texts = str(row["text"]).strip()
    
    if len(texts) > 20:
        times=row["time"].split("T")[0]
        
        clean_data={
            "page_name":row["pageName"],
            "post_id": row["postId"],
            "post_url": row["facebookUrl"],
            "post_content": row["text"],
            "post_date": times
        }
        all_data.append(clean_data)

with open("facebook_posts.json", "w", encoding="utf-8") as f:
    json.dump(all_data, f, ensure_ascii=False, indent=2)

print(f"Saved {len(all_data)} posts")
