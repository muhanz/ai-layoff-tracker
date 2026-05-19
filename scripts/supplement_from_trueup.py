#!/usr/bin/env python3
"""
补充数据抓取脚本 - 从 TrueUp.io 页面提取裁员数据
==================================================
由于 TrueUp.io 有 Cloudflare 保护，此脚本需要在有浏览器的环境中运行，
或者你可以手动从 TrueUp.io 复制数据后粘贴到此脚本中处理。

使用方法：
  方式1（推荐）：手动从 TrueUp.io 复制数据到 data/trueup_raw.txt，然后运行本脚本
  方式2：设置 OPENAI_API_KEY 后运行，用 LLM 从粘贴的文本中提取结构化数据

环境变量：
  OPENAI_API_KEY - 用于从非结构化文本中提取数据
"""

import json
import os
import sys
from datetime import datetime

def parse_trueup_text(input_file="data/trueup_raw.txt"):
    """
    从 TrueUp.io 复制的文本中提取裁员事件。
    
    预期格式（从网页复制粘贴）：
    CompanyName
    Description
    XXX people
    XX% of company
    Month DD, YYYY
    [news link]
    """
    if not os.path.exists(input_file):
        print(f"❌ 文件不存在: {input_file}")
        print(f"   请先从 https://www.trueup.io/layoffs 复制裁员列表数据到此文件")
        print(f"   提示：在TrueUp页面上全选裁员列表区域，Ctrl+C复制，粘贴到文件中")
        return []
    
    with open(input_file, "r", encoding="utf-8") as f:
        text = f.read()
    
    if not text.strip():
        print("❌ 文件为空")
        return []
    
    # 使用 LLM 提取
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ 需要设置 OPENAI_API_KEY 来解析非结构化文本")
        return []
    
    from openai import OpenAI
    client = OpenAI()
    
    # 分块处理（避免超出token限制）
    chunk_size = 4000  # 字符
    chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    
    all_events = []
    
    for i, chunk in enumerate(chunks):
        print(f"  处理第 {i+1}/{len(chunks)} 块...")
        
        prompt = f"""Extract layoff events from this text copied from TrueUp.io layoffs tracker.

For each event, extract:
- company: Company name
- headcount: Number of people laid off (integer, 0 if only percentage given)
- date: Date (YYYY-MM-DD format)
- ai_attributed: "confirmed" if AI/automation explicitly mentioned, "likely" if tech company restructuring, "unclear" otherwise
- source_url: News article URL if present

Return JSON: {{"events": [...]}}

Text:
{chunk}"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        events = result.get("events", [])
        all_events.extend(events)
    
    print(f"  从文本中提取了 {len(all_events)} 个事件")
    return all_events


def merge_into_database(new_events, db_path="data/events.json"):
    """将新事件合并到现有数据库中（去重）"""
    with open(db_path, "r", encoding="utf-8") as f:
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
                "source_urls": [event.get("source_url", "")] if event.get("source_url") else [],
                "note": event.get("note", "Imported from TrueUp.io"),
                "last_updated": datetime.utcnow().strftime("%Y-%m-%d"),
                "locked": True
            })
            existing_keys.add(key)
            added += 1
    
    # 更新统计
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
    
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 新增 {added} 个事件，总计 {len(db['events'])} 个事件")
    print(f"   总影响人数: {db['metadata']['total_estimated']:,}")
    return db


if __name__ == "__main__":
    input_file = sys.argv[1] if len(sys.argv) > 1 else "data/trueup_raw.txt"
    
    print(f"📥 从 {input_file} 解析数据...")
    events = parse_trueup_text(input_file)
    
    if events:
        print(f"\n🔄 合并到数据库...")
        merge_into_database(events)
    else:
        print("\n⚠️  没有提取到事件。请确保:")
        print(f"   1. 文件 {input_file} 存在且包含从 TrueUp.io 复制的文本")
        print(f"   2. 环境变量 OPENAI_API_KEY 已设置")
