import json
from datetime import datetime

def generate_html():
    """根据数据生成静态HTML警告页面"""
    with open("data/events.json", "r") as f:
        db = json.load(f)
    
    total_confirmed = db["metadata"]["total_confirmed"]
    total_estimated = db["metadata"]["total_estimated"]
    last_updated = db["metadata"]["last_updated"]
    event_count = len(db["events"])
    
    # 最近10条事件
    recent_events = sorted(db["events"], key=lambda x: x["date"], reverse=True)[:10]
    
    recent_html = ""
    for e in recent_events:
        badge = {"confirmed": "🔴", "likely": "🟡", "unclear": "⚪"}.get(e["ai_attributed"], "⚪")
        recent_html += f"""
        <tr>
            <td>{e['date']}</td>
            <td>{e['company']}</td>
            <td>{e['headcount']:,}</td>
            <td>{badge} {e['ai_attributed']}</td>
            <td><a href="{e['source_urls'][0] if e['source_urls'] else '#'}" target="_blank">来源</a></td>
        </tr>"""
    
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI裁员追踪 - 全球警告</title>
    <meta name="description" content="自GPT-4发布以来，全球因AI被裁员的人数实时追踪。数据每日更新，来源可查。">
    <meta property="og:title" content="AI裁员追踪 - 全球警告">
    <meta property="og:description" content="自GPT-4发布以来，已有{total_estimated:,}人在AI相关裁员中失去工作。">
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <main>
        <header>
            <h1>⚠️ AI 裁员警告</h1>
            <p class="subtitle">自 GPT-4 发布（2023年3月14日）以来</p>
        </header>
        
        <section class="counter">
            <div class="number">{total_estimated:,}</div>
            <p class="label">人在AI相关裁员中失去工作（宽泛口径）</p>
            <div class="number secondary">{total_confirmed:,}</div>
            <p class="label">人被公司明确因AI裁员（保守口径）</p>
        </section>
        
        <section class="meta">
            <p>覆盖 {event_count} 起裁员事件 · 最后更新：{last_updated[:10]}</p>
            <p class="sources">数据来源：Challenger, Gray & Christmas · Layoffs.fyi · TrueUp.io · 公开新闻报道</p>
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
        
        <footer>
            <p>🔴 confirmed = 公司明确声明因AI裁员 · 🟡 likely = 媒体分析与AI高度相关 · ⚪ unclear = 可能相关但未确认</p>
            <p>本页面数据每日自动更新。<a href="https://github.com/YOUR_USERNAME/ai-layoff-tracker">GitHub 源码与数据</a></p>
        </footer>
    </main>
</body>
</html>"""
    
    with open("public/index.html", "w", encoding="utf-8" ) as f:
        f.write(html)
    
    print("Page generated successfully.")

if __name__ == "__main__":
    generate_html()
