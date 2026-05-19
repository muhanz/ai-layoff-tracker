#!/usr/bin/env python3
"""
LLM 分析脚本 - AI裁员追踪器
============================
使用 GPT-4o-mini 从抓取的新闻中提取结构化的裁员事件数据。

环境变量：
  OPENAI_API_KEY - OpenAI API Key
"""

import json
import os
from datetime import datetime
from openai import OpenAI


def analyze_news():
    """使用LLM从新闻中提取结构化裁员数据"""
    
    # 检查API Key
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY 未设置，跳过分析")
        return
    
    client = OpenAI()
    
    # 读取抓取的新闻
    raw_file = "data/raw_news.json"
    if not os.path.exists(raw_file):
        print("⚠️  raw_news.json 不存在，跳过分析")
        return
    
    with open(raw_file, "r", encoding="utf-8") as f:
        articles = json.load(f)
    
    if not articles:
        print("⚠️  没有新文章需要分析")
        return
    
    print(f"🤖 分析 {len(articles)} 篇文章...")
    
    # 构建提示词
    news_text = "\n\n".join([
        f"Title: {a.get('title', 'N/A')}\n"
        f"Description: {a.get('description', '') or 'N/A'}\n"
        f"Source: {a.get('source', {}).get('name', 'Unknown')}\n"
        f"URL: {a.get('url', '')}\n"
        f"Date: {a.get('publishedAt', '')}"
        for a in articles
    ])
    
    prompt = f"""You are analyzing news articles to find AI-related layoff events.

TASK: Extract each DISTINCT layoff event where AI, automation, or technology replacement is a factor.

RULES:
1. Only include actual layoff announcements (not predictions or opinion pieces)
2. Each event must have a specific company name
3. If exact headcount is not stated but percentage is given, estimate if possible, otherwise set to 0
4. "AI-related" includes: company explicitly cites AI, company invests in AI while cutting, restructuring for automation
5. Merge duplicate reports about the same company/event
6. Use the article's publication date if the actual layoff date is unclear

CLASSIFICATION:
- "confirmed": Company explicitly stated AI/automation as reason for cuts
- "likely": Company investing in AI while cutting jobs, or media analysis says AI-related
- "unclear": Layoffs at tech company but AI connection not clearly stated

RETURN FORMAT (strict JSON):
{{"layoff_events": [
  {{
    "company": "Company Name",
    "headcount": 100,
    "date": "2026-05-19",
    "ai_attributed": "confirmed",
    "source_url": "https://example.com/article",
    "reason": "Brief explanation of why this is AI-related"
  }}
]}}

If NO valid AI-related layoff events are found, return: {{"layoff_events": []}}

NEWS ARTICLES TO ANALYZE:
{news_text}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        raw_response = response.choices[0].message.content
        print(f"  LLM 返回 {len(raw_response)} 字符")
        
        result = json.loads(raw_response)
        new_events = result.get("layoff_events", [])
        
        print(f"  提取到 {len(new_events)} 个事件")
        for e in new_events:
            print(f"    - {e.get('company')}: {e.get('headcount', '?')} 人 [{e.get('ai_attributed')}]")
        
    except Exception as e:
        print(f"  ❌ LLM 调用失败: {e}")
        return
    
    # 加载现有数据库并去重合并
    db_file = "data/events.json"
    if not os.path.exists(db_file):
        print(f"  ❌ {db_file} 不存在，请先运行 import_historical_data.py")
        return
    
    with open(db_file, "r", encoding="utf-8") as f:
        db = json.load(f)
    
    existing_keys = {(e["company"].lower().strip(), e["date"]) for e in db["events"]}
    added = 0
    
    for event in new_events:
        company = event.get("company", "").strip()
        date = event.get("date", "")
        headcount = event.get("headcount", 0)
        
        if not company or not date:
            continue
        
        # 去重检查
        key = (company.lower(), date)
        if key in existing_keys:
            print(f"    ⏭️  跳过重复: {company} ({date})")
            continue
        
        # 添加新事件
        db["events"].append({
            "id": f"{company}_{date}".replace(" ", "_").lower(),
            "company": company,
            "date": date,
            "headcount": headcount,
            "ai_attributed": event.get("ai_attributed", "unclear"),
            "source_urls": [event.get("source_url", "")] if event.get("source_url") else [],
            "note": event.get("reason", ""),
            "last_updated": datetime.utcnow().strftime("%Y-%m-%d"),
            "locked": False
        })
        existing_keys.add(key)
        added += 1
        print(f"    ✅ 新增: {company} - {headcount} 人 ({date})")
    
    # 更新元数据
    db["metadata"]["last_updated"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    db["metadata"]["total_confirmed"] = sum(
        e["headcount"] for e in db["events"] if e["ai_attributed"] == "confirmed"
    )
    db["metadata"]["total_likely"] = sum(
        e["headcount"] for e in db["events"] if e["ai_attributed"] == "likely"
    )
    db["metadata"]["total_estimated"] = sum(
        e["headcount"] for e in db["events"]
    )
    
    with open(db_file, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    
    print(f"\n📊 结果: 新增 {added} 个事件")
    print(f"   总事件数: {len(db['events'])}")
    print(f"   总影响人数: {db['metadata']['total_estimated']:,}")
    print(f"   其中 confirmed: {db['metadata']['total_confirmed']:,}")


if __name__ == "__main__":
    analyze_news()
