import json
import os
from datetime import datetime
from openai import OpenAI

client = OpenAI()  # 自动读取 OPENAI_API_KEY 环境变量

def analyze_news():
    """使用LLM从新闻中提取结构化裁员数据"""
    with open("data/raw_news.json", "r") as f:
        articles = json.load(f)
    
    if not articles:
        print("No new articles to analyze")
        return
    
    # 构建提示词
    news_text = "\n\n".join([
        f"Title: {a['title']}\nDescription: {a.get('description', '')}\nSource: {a['source']['name']}\nURL: {a['url']}\nDate: {a['publishedAt']}"
        for a in articles
    ])
    
    prompt = f"""Analyze the following news articles about AI-related layoffs.
For each DISTINCT layoff event, extract:
- company: Company name
- headcount: Number of people laid off (integer, 0 if unknown)
- date: Date of announcement (YYYY-MM-DD)
- ai_attributed: "confirmed" if company explicitly cited AI, "likely" if AI is implied, "unclear" otherwise
- source_url: The news article URL

Rules:
- Merge duplicate reports about the same event
- Only include events where AI/automation is a factor
- Return valid JSON array

News articles:
{news_text}

Return ONLY a JSON array of objects, no other text."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    new_events = result if isinstance(result, list) else result.get("events", [])
    
    # 加载现有数据库并去重合并
    with open("data/events.json", "r") as f:
        db = json.load(f)
    
    existing_keys = {(e["company"], e["date"]) for e in db["events"]}
    added = 0
    
    for event in new_events:
        key = (event.get("company", ""), event.get("date", ""))
        if key not in existing_keys and event.get("headcount", 0) > 0:
            db["events"].append({
                "id": f"{event['company']}_{event['date']}".replace(" ", "_").lower(),
                "company": event["company"],
                "date": event["date"],
                "headcount": event["headcount"],
                "ai_attributed": event.get("ai_attributed", "unclear"),
                "source_urls": [event.get("source_url", "")],
                "last_updated": datetime.utcnow().strftime("%Y-%m-%d"),
                "locked": False
            })
            existing_keys.add(key)
            added += 1
    
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
    
    print(f"Added {added} new events. Total: {len(db['events'])} events.")

if __name__ == "__main__":
    analyze_news()
