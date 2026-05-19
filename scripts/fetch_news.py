#!/usr/bin/env python3
"""
每日新闻抓取脚本 - AI裁员追踪器
================================
从 GNews.io 免费API抓取最新的AI裁员相关新闻。

环境变量：
  GNEWS_API_KEY - GNews.io 的 API Key
"""

import requests
import json
import os

GNEWS_API_KEY = os.environ.get("GNEWS_API_KEY")
OUTPUT_FILE = "data/raw_news.json"


def fetch_ai_layoff_news():
    """抓取与AI裁员相关的最新新闻"""
    if not GNEWS_API_KEY:
        print("⚠️  GNEWS_API_KEY 未设置，跳过新闻抓取")
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []

    url = "https://gnews.io/api/v4/search"
    
    # 多组关键词搜索，提高命中率
    queries = [
        "layoffs AI jobs cut",
        "company cuts workers artificial intelligence",
        "tech layoffs automation AI replace",
    ]
    
    all_articles = []
    seen_urls = set()
    
    for q in queries:
        params = {
            "q": q,
            "lang": "en",
            "max": 10,
            "sortby": "publishedAt",
            "apikey": GNEWS_API_KEY
        }
        
        try:
            response = requests.get(url, params=params, timeout=15)
            
            if response.status_code == 200:
                articles = response.json().get("articles", [])
                for a in articles:
                    if a.get("url") not in seen_urls:
                        seen_urls.add(a["url"])
                        all_articles.append(a)
            else:
                print(f"  ⚠️  查询 '{q}' 返回状态码: {response.status_code}")
                # 免费版每天100次请求，如果超限就停止
                if response.status_code == 403:
                    print("  ❌ API 配额已用完，停止抓取")
                    break
        except requests.exceptions.RequestException as e:
            print(f"  ⚠️  请求失败: {e}")
            continue
    
    # 保存结果
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(all_articles, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 抓取到 {len(all_articles)} 篇不重复文章")
    return all_articles


if __name__ == "__main__":
    fetch_ai_layoff_news()
