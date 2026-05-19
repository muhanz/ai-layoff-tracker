import requests
import json
import os

GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY")
OUTPUT_FILE = "data/raw_news.json"

def fetch_ai_layoff_news():
    """抓取与AI裁员相关的最新新闻"""
    url = "https://gnews.io/api/v4/search"
    params = {
        "q": "layoffs AI artificial intelligence",
        "lang": "en",
        "max": 10,
        "sortby": "publishedAt",
        "apikey": GNEWS_API_KEY
    }
    
    response = requests.get(url, params=params )
    
    if response.status_code != 200:
        print(f"API Error: {response.status_code}")
        print(f"Response: {response.text}")
        # 如果API失败，写入空列表而不是中断整个流程
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []
    
    articles = response.json().get("articles", [])
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
    
    print(f"Fetched {len(articles)} articles")
    return articles

if __name__ == "__main__":
    fetch_ai_layoff_news()
