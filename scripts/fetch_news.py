import requests
import json
import os
from datetime import datetime, timedelta

GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY")
OUTPUT_FILE = "data/raw_news.json"

def fetch_ai_layoff_news():
    """抓取过去24小时内与AI裁员相关的新闻"""
    url = "https://gnews.io/api/v4/search"
    params = {
        "q": '"layoffs" AND ("AI" OR "artificial intelligence" )',
        "lang": "en",
        "max": 10,
        "from": (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "apikey": GNEWS_API_KEY
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    articles = response.json().get("articles", [])
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    
    print(f"Fetched {len(articles)} articles")
    return articles

if __name__ == "__main__":
    fetch_ai_layoff_news()
