import json
import os
from datetime import datetime
from openai import OpenAI

client = OpenAI()

def analyze_news():
    """使用LLM从新闻中提取结构化裁员数据"""
    with open("data/raw_news.json", "r") as f:
        articles = json.load(f)
    
    if not articles:
        print("No new articles to analyze")
        return
    
    print(f"Analyzing {len(articles)} articles...")
    
    # 构建提示词
    news_text = "\n\n".join([
        f"Title: {a['title']}\nDescription: {a.get('description', '') or ''}\nSource: {a.get('source', {}).get('name', 'Unknown')}\nURL: {a.get('url', '')}\nDate: {a.get('publishedAt', '')}"
        for a in articles
    ])
    
    prompt = f"""You are analyzing news articles about AI-related layoffs.

For each DISTINCT layoff event mentioned in the articles below, extract the following information.

IMPORTANT RULES:
- Only include events where AI, automation, or "efficiency through technology" is mentioned as a factor
- If the exact number of layoffs is not stated, estimate from percentage + company size if possible, otherwise use 0
- If a company says it's "cutting jobs to invest in AI" or "restructuring for AI", that counts
- Merge duplicate reports about the same company/event
- Date format must be YYYY-MM-DD

Return a JSON object with this exact structure:
{{"layoff_events": [
  {{
    "company": "Company Name",
    "headcount": 100,
    "date": "2026-05-18",
    "ai_attributed": "confirmed",
    "source_url": "https://..."
  }}
]}}

ai_attributed values:
- "confirmed": company explicitly stated AI/automation as reason
- "likely": company investing in AI while cutting jobs, or media analysis says AI-related
- "unclear": layoffs happened at tech/AI company but reason not clearly AI

If NO valid layoff events are found, return: {{"layoff_events": []}}

NEWS ARTICLES:
{news_text}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"}
     )
    
    raw_response = response.choices[0].message.content
    print(f"LLM response: {raw_response[:500]}")
    
    result = json.loads(raw_response)
    new_events = result.get("layoff_events", [])
    
    print(f"Extracted {len(new_events)} events from LLM")
    
    # 加载现有数据库并去重合并
    with open("data/events.json", "r") as f:
        db = json.load(f)
    
    existing_keys = {(e["company"].lower(), e["date"]) for e in db["events"]}
    added = 0
    
    for event in new_events:
        company = event.get("company", "").strip()
        date = event.get("date", "")
        headcount = event.get("headcount", 0)
        
        if not company or not date:
            continue
            
        key = (company.lower(), date)
        if key not in existing_keys:
            db["events"].append({
                "id": f"{company}_{date}".replace(" ", "_").lower(),
                "company": company,
                "date": date,
                "headcount": headcount,
                "ai_attributed": event.get("ai_attributed", "unclear"),
                "source_urls": [event.get("source_url", "")],
                "last_updated": datetime.utcnow().strftime("%Y-%m-%d"),
                "locked": False
            })
            existing_keys.add(key)
            added += 1
            print(f"  Added: {company} - {headcount} people on {date}")
    
    # 更新元数据
    db["metadata"]["last_updated"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    db["metadata"]["total_confirmed"] = sum(
        e["headcount"] for e in db["events"] if e["ai_attributed"] == "confirmed"
    )
    db["metadata"]["total_estimated"] = sum(
        e["headcount"] for e in db["events"]
    )
    
    with open("data/events.json", "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    
    print(f"Added {added} new events. Total events: {len(db['events'])}. Total estimated: {db['metadata']['total_estimated']:,}")

if __name__ == "__main__":
    analyze_news()
