#!/usr/bin/env python3
"""
页面生成脚本 - AI裁员追踪器
============================
从 data/events.json 生成静态 HTML 警告页面。
"""

import json
import os
from datetime import datetime


def generate_html():
    """根据数据生成静态HTML警告页面"""
    
    db_file = "data/events.json"
    if not os.path.exists(db_file):
        print("❌ data/events.json 不存在，请先运行 import_historical_data.py")
        return
    
    with open(db_file, "r", encoding="utf-8") as f:
        db = json.load(f)
    
    total_confirmed = db["metadata"]["total_confirmed"]
    total_estimated = db["metadata"]["total_estimated"]
    total_likely = db["metadata"].get("total_likely", 0)
    last_updated = db["metadata"]["last_updated"]
    event_count = len(db["events"])
    challenger_total = db["metadata"].get("challenger_cumulative_ai_cuts", 0)
    
    # 计算天数
    start = datetime(2023, 3, 14)
    days_since = (datetime.utcnow() - start).days
    
    # 最近20条事件
    recent_events = sorted(db["events"], key=lambda x: x["date"], reverse=True)[:20]
    
    recent_html = ""
    for e in recent_events:
        badge_class = {
            "confirmed": "badge-confirmed",
            "likely": "badge-likely",
            "unclear": "badge-unclear"
        }.get(e["ai_attributed"], "badge-unclear")
        
        source_link = ""
        if e.get("source_urls") and e["source_urls"][0]:
            source_link = f'<a href="{e["source_urls"][0]}" target="_blank" rel="noopener">来源</a>'
        
        headcount_str = f'{e["headcount"]:,}' if e["headcount"] > 0 else "未知"
        
        recent_html += f"""
            <tr>
                <td class="date-col">{e['date']}</td>
                <td class="company-col">{e['company']}</td>
                <td class="number-col">{headcount_str}</td>
                <td><span class="badge {badge_class}">{e['ai_attributed']}</span></td>
                <td>{source_link}</td>
            </tr>"""
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI裁员追踪 - 全球实时警告</title>
    <meta name="description" content="自GPT-4发布以来，全球因AI被裁员的人数实时追踪。数据每日更新，来源可查。">
    <meta property="og:title" content="⚠️ AI裁员追踪 - 全球实时警告">
    <meta property="og:description" content="自GPT-4发布以来的{days_since}天内，已有{total_estimated:,}人在AI相关裁员中失去工作。">
    <meta property="og:type" content="website">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="⚠️ AI裁员追踪 - {total_estimated:,}人已受影响">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0a0a;
            color: #e0e0e0;
            min-height: 100vh;
        }}
        
        main {{
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem 1.5rem;
        }}
        
        header {{
            text-align: center;
            margin-bottom: 3rem;
            padding-top: 2rem;
        }}
        
        h1 {{
            font-size: 2.5rem;
            color: #ff4444;
            margin-bottom: 0.5rem;
            text-shadow: 0 0 20px rgba(255, 68, 68, 0.3);
        }}
        
        .subtitle {{
            color: #888;
            font-size: 1.1rem;
        }}
        
        .counter {{
            text-align: center;
            margin: 3rem 0;
            padding: 2.5rem;
            background: linear-gradient(135deg, #1a0000 0%, #0a0a0a 100%);
            border: 1px solid #331111;
            border-radius: 12px;
        }}
        
        .number {{
            font-size: 4.5rem;
            font-weight: 800;
            color: #ff4444;
            line-height: 1.1;
            font-variant-numeric: tabular-nums;
        }}
        
        .number.secondary {{
            font-size: 2.5rem;
            color: #ff8844;
            margin-top: 1.5rem;
        }}
        
        .label {{
            color: #999;
            font-size: 0.95rem;
            margin-top: 0.3rem;
        }}
        
        .days-counter {{
            margin-top: 1.5rem;
            padding-top: 1.5rem;
            border-top: 1px solid #222;
            color: #666;
            font-size: 0.9rem;
        }}
        
        .meta {{
            text-align: center;
            margin: 2rem 0;
            color: #666;
            font-size: 0.85rem;
            line-height: 1.8;
        }}
        
        .sources {{
            color: #555;
        }}
        
        .recent {{
            margin-top: 3rem;
        }}
        
        .recent h2 {{
            font-size: 1.3rem;
            margin-bottom: 1rem;
            color: #ccc;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }}
        
        thead {{
            background: #111;
        }}
        
        th {{
            padding: 0.75rem 0.5rem;
            text-align: left;
            color: #888;
            font-weight: 600;
            border-bottom: 1px solid #222;
        }}
        
        td {{
            padding: 0.6rem 0.5rem;
            border-bottom: 1px solid #1a1a1a;
        }}
        
        tr:hover {{
            background: #111;
        }}
        
        .date-col {{ color: #666; white-space: nowrap; }}
        .company-col {{ font-weight: 500; color: #ddd; }}
        .number-col {{ font-variant-numeric: tabular-nums; color: #ff6666; font-weight: 600; }}
        
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75rem;
            font-weight: 500;
        }}
        
        .badge-confirmed {{ background: #3d1111; color: #ff6666; }}
        .badge-likely {{ background: #3d2e11; color: #ffaa44; }}
        .badge-unclear {{ background: #1a1a2e; color: #8888cc; }}
        
        a {{ color: #4488cc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        
        footer {{
            margin-top: 3rem;
            padding-top: 2rem;
            border-top: 1px solid #1a1a1a;
            font-size: 0.8rem;
            color: #555;
            line-height: 2;
            text-align: center;
        }}
        
        .methodology {{
            margin-top: 2rem;
            padding: 1.5rem;
            background: #0d0d0d;
            border: 1px solid #1a1a1a;
            border-radius: 8px;
            font-size: 0.8rem;
            color: #777;
            line-height: 1.8;
        }}
        
        .methodology h3 {{
            color: #999;
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
        }}
        
        @media (max-width: 600px) {{
            .number {{ font-size: 3rem; }}
            .number.secondary {{ font-size: 1.8rem; }}
            h1 {{ font-size: 1.8rem; }}
            table {{ font-size: 0.75rem; }}
        }}
    </style>
</head>
<body>
    <main>
        <header>
            <h1>&#9888;&#65039; AI 裁员警告</h1>
            <p class="subtitle">自 GPT-4 发布（2023年3月14日）以来的全球追踪</p>
        </header>
        
        <section class="counter">
            <div class="number">{total_estimated:,}</div>
            <p class="label">人在AI相关裁员中失去工作（综合口径）</p>
            
            <div class="number secondary">{total_confirmed:,}</div>
            <p class="label">人被公司明确因AI裁员（保守口径）</p>
            
            <div class="days-counter">
                {days_since} 天 &middot; {event_count} 起事件 &middot; 
                平均每天 {total_estimated // max(days_since, 1):,} 人
            </div>
        </section>
        
        <section class="meta">
            <p>最后更新：{last_updated[:10]} &middot; 
               Challenger报告累计（仅美国）：{challenger_total:,} 人</p>
            <p class="sources">
                数据来源：Challenger, Gray & Christmas &middot; Layoffs.fyi &middot; 
                TrueUp.io &middot; 公开新闻报道
            </p>
        </section>
        
        <section class="recent">
            <h2>最近事件</h2>
            <table>
                <thead>
                    <tr>
                        <th>日期</th>
                        <th>公司</th>
                        <th>人数</th>
                        <th>AI归因</th>
                        <th>来源</th>
                    </tr>
                </thead>
                <tbody>{recent_html}
                </tbody>
            </table>
        </section>
        
        <section class="methodology">
            <h3>统计方法说明</h3>
            <p>
                <strong>confirmed</strong>（红色）= 公司在官方声明中明确提到AI/自动化是裁员原因<br>
                <strong>likely</strong>（橙色）= 公司在大规模投资AI的同时裁员，或媒体分析认为与AI高度相关<br>
                <strong>unclear</strong>（蓝色）= 科技公司裁员，可能与AI转型有关但未明确声明
            </p>
            <p style="margin-top: 0.8rem;">
                本页面数据每日通过自动化脚本更新。美国数据每月使用 Challenger, Gray & Christmas 
                官方报告进行校准。全球数据综合多个公开来源。由于统计口径差异，数字可能与单一来源有出入。
            </p>
        </section>
        
        <footer>
            <p>本页面数据每日自动更新 &middot; 
               <a href="https://github.com/YOUR_USERNAME/ai-layoff-tracker">GitHub 源码与完整数据</a></p>
            <p>数据仅供参考，不构成任何投资或就业建议</p>
        </footer>
    </main>
</body>
</html>"""
    
    # 确保输出目录存在
    os.makedirs("public", exist_ok=True)
    
    with open("public/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"✅ 页面已生成: public/index.html")
    print(f"   显示数字: {total_estimated:,}（综合）/ {total_confirmed:,}（保守）")


if __name__ == "__main__":
    generate_html()
