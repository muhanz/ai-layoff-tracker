#!/usr/bin/env python3
"""
历史数据导入脚本 - AI裁员追踪器
=================================
本脚本用于建立 GPT-4 发布（2023年3月14日）以来的 AI 裁员历史基线数据。

数据来源策略：
1. 硬编码权威数据（Challenger报告、公开报道中的重大事件）
2. 从 layoffs.fyi 页面抓取（需要浏览器环境）
3. 用 LLM 对抓取到的事件进行 AI 归因标注

使用方法：
  python scripts/import_historical_data.py

环境变量：
  OPENAI_API_KEY - 用于 LLM 归因标注（可选，不设置则跳过标注）
"""

import json
import os
import sys
from datetime import datetime

# ============================================================
# 第一部分：硬编码的权威历史数据
# 来源：公开新闻报道、Challenger报告、公司官方公告
# ============================================================

# 这些是自 GPT-4 发布以来，明确与 AI 相关的重大裁员事件
# ai_attributed: "confirmed" = 公司明确声明因AI
#                "likely" = 投资AI同时裁员，媒体分析为AI相关
#                "unclear" = 科技公司裁员，可能与AI有关但未明确

HISTORICAL_EVENTS = [
    # === 2023 ===
    {"company": "IBM", "headcount": 7800, "date": "2023-05-01", "ai_attributed": "confirmed",
     "source_urls": ["https://www.bloomberg.com/news/articles/2023-05-01/ibm-to-pause-hiring-for-back-office-jobs-that-ai-could-kill"],
     "note": "CEO Arvind Krishna stated AI could replace 7,800 back-office jobs over 5 years"},
    {"company": "Chegg", "headcount": 80, "date": "2023-06-05", "ai_attributed": "confirmed",
     "source_urls": ["https://www.wsj.com/articles/chegg-cuts-4-of-workforce-after-chatgpt-hurts-growth-c0b9a7cc"],
     "note": "Explicitly cited ChatGPT impact on business"},
    {"company": "BT Group", "headcount": 55000, "date": "2023-05-18", "ai_attributed": "confirmed",
     "source_urls": ["https://www.bbc.com/news/business-65631168"],
     "note": "Plan to cut 55,000 jobs by 2030, with up to 10,000 replaced by AI"},
    {"company": "Dropbox", "headcount": 500, "date": "2023-04-27", "ai_attributed": "confirmed",
     "source_urls": ["https://blog.dropbox.com/topics/company/a-message-from-drew"],
     "note": "CEO cited AI era requiring different skill mix"},
    {"company": "Meta", "headcount": 10000, "date": "2023-03-14", "ai_attributed": "likely",
     "source_urls": ["https://about.fb.com/news/2023/03/mark-zuckerberg-meta-year-of-efficiency/"],
     "note": "Year of Efficiency, shifting resources to AI"},
    {"company": "Google", "headcount": 12000, "date": "2023-01-20", "ai_attributed": "likely",
     "source_urls": ["https://blog.google/inside-google/message-ceo/january-update/"],
     "note": "Restructuring to focus on AI priorities (announced before GPT-4 but layoffs continued)"},
    {"company": "Microsoft", "headcount": 10000, "date": "2023-01-18", "ai_attributed": "likely",
     "source_urls": ["https://blogs.microsoft.com/blog/2023/01/18/subject-focusing-on-our-short-and-long-term-opportunity/"],
     "note": "Cut jobs while investing billions in OpenAI"},
    {"company": "Spotify", "headcount": 600, "date": "2023-06-05", "ai_attributed": "likely",
     "source_urls": ["https://newsroom.spotify.com/2023-06-05/an-update-on-spotifys-plans/"],
     "note": "Restructuring, later heavily invested in AI features"},
    {"company": "Duolingo", "headcount": 26, "date": "2023-12-05", "ai_attributed": "confirmed",
     "source_urls": ["https://www.businessinsider.com/duolingo-laid-off-workers-replaced-ai-2024-1"],
     "note": "Replaced contract translators with AI"},
    
    # === 2024 ===
    {"company": "Google", "headcount": 12000, "date": "2024-01-11", "ai_attributed": "likely",
     "source_urls": ["https://www.nytimes.com/2024/01/11/technology/google-layoffs.html"],
     "note": "Multiple rounds throughout 2024, restructuring for AI"},
    {"company": "SAP", "headcount": 8000, "date": "2024-01-23", "ai_attributed": "confirmed",
     "source_urls": ["https://www.reuters.com/technology/sap-restructure-8000-roles-ai-push-2024-01-23/"],
     "note": "Explicitly restructuring 8,000 roles in AI push"},
    {"company": "UPS", "headcount": 12000, "date": "2024-01-30", "ai_attributed": "likely",
     "source_urls": ["https://www.cnbc.com/2024/01/30/ups-to-cut-12000-jobs.html"],
     "note": "Cited technology and automation efficiencies"},
    {"company": "Duolingo", "headcount": 10, "date": "2024-01-08", "ai_attributed": "confirmed",
     "source_urls": ["https://www.businessinsider.com/duolingo-laid-off-workers-replaced-ai-2024-1"],
     "note": "Additional contractor cuts replaced by AI"},
    {"company": "Google", "headcount": 1000, "date": "2024-04-18", "ai_attributed": "confirmed",
     "source_urls": ["https://www.theverge.com/2024/4/18/24133814/google-cut-hundreds-core-teams"],
     "note": "Core team cuts, shifting to AI divisions"},
    {"company": "Tesla", "headcount": 14000, "date": "2024-04-15", "ai_attributed": "likely",
     "source_urls": ["https://www.reuters.com/business/autos-transportation/tesla-lay-off-more-than-10-its-workforce-2024-04-15/"],
     "note": "10% workforce cut while investing heavily in FSD/AI"},
    {"company": "Amazon", "headcount": 18000, "date": "2024-01-10", "ai_attributed": "likely",
     "source_urls": ["https://www.aboutamazon.com/news/company-news/andy-jassy-update-on-amazon-layoffs-2024"],
     "note": "Continued cuts, shifting to AI services"},
    {"company": "Klarna", "headcount": 700, "date": "2024-09-12", "ai_attributed": "confirmed",
     "source_urls": ["https://www.reuters.com/technology/klarna-says-ai-approach-warming-up-ipo-investors-2024-08-27/"],
     "note": "CEO explicitly stated AI doing work of 700 employees"},
    {"company": "Intuit", "headcount": 1800, "date": "2024-07-10", "ai_attributed": "confirmed",
     "source_urls": ["https://www.intuit.com/blog/news-social/intuit-ceo-sasan-goodarzi-shares-strategic-decisions/"],
     "note": "Cut 10% to reinvest in AI"},
    {"company": "Cisco", "headcount": 4250, "date": "2024-02-14", "ai_attributed": "likely",
     "source_urls": ["https://www.reuters.com/technology/cisco-cut-thousands-jobs-shift-focus-ai-2024-02-14/"],
     "note": "Shift focus to AI and cybersecurity"},
    {"company": "Dell", "headcount": 12500, "date": "2024-02-05", "ai_attributed": "likely",
     "source_urls": ["https://www.reuters.com/technology/dell-cut-about-6650-jobs-2024-02-05/"],
     "note": "Multiple rounds, reorganizing for AI-driven products"},
    
    # === 2025 ===
    {"company": "Microsoft", "headcount": 1900, "date": "2025-01-09", "ai_attributed": "likely",
     "source_urls": ["https://www.cnbc.com/2025/01/09/microsoft-lays-off-1900-activision-blizzard-xbox-employees.html"],
     "note": "Gaming division cuts while investing in AI"},
    {"company": "Google", "headcount": 1000, "date": "2025-01-21", "ai_attributed": "confirmed",
     "source_urls": ["https://www.theverge.com/2025/1/21/google-layoffs-2025"],
     "note": "Continued restructuring for AI-first strategy"},
    {"company": "Amazon", "headcount": 30000, "date": "2025-10-27", "ai_attributed": "likely",
     "source_urls": ["https://www.statista.com/statistics/1127080/worldwide-tech-layoffs-covid-19-biggest/"],
     "note": "Largest single layoff wave, efficiency and AI investment"},
    {"company": "Meta", "headcount": 3600, "date": "2025-02-10", "ai_attributed": "confirmed",
     "source_urls": ["https://about.fb.com/news/2025/02/performance-based-exits/"],
     "note": "Performance-based cuts, redirecting to AI teams"},
    {"company": "Salesforce", "headcount": 1000, "date": "2025-01-28", "ai_attributed": "confirmed",
     "source_urls": ["https://www.bloomberg.com/news/articles/2025-01-28/salesforce-cuts-1000-jobs"],
     "note": "Cuts while launching Agentforce AI platform"},
    {"company": "Workday", "headcount": 1750, "date": "2025-02-04", "ai_attributed": "confirmed",
     "source_urls": ["https://www.workday.com/en-us/company/latest/newsroom/press-releases/press-release-details.html"],
     "note": "8.5% cut to invest in AI"},
    {"company": "Spotify", "headcount": 1500, "date": "2025-01-15", "ai_attributed": "likely",
     "source_urls": ["https://newsroom.spotify.com/"],
     "note": "Continued efficiency cuts, AI-driven personalization"},
    
    # === 2026 (截至5月) ===
    {"company": "Cloudflare", "headcount": 1100, "date": "2026-05-07", "ai_attributed": "confirmed",
     "source_urls": ["https://www.wsj.com/business/earnings/cloudflare-to-slash-1-100-jobs-due-to-ai-driven-restructuring-plan-640f7b52"],
     "note": "Explicitly AI-Driven Restructuring Plan"},
    {"company": "LinkedIn", "headcount": 875, "date": "2026-05-13", "ai_attributed": "confirmed",
     "source_urls": ["https://www.reuters.com/business/world-at-work/linkedin-is-planning-lay-off-5-staff-latest-tech-sector-cuts-source-says-2026-05-13/"],
     "note": "5% staff cut in AI-driven restructuring"},
    {"company": "Cisco", "headcount": 4000, "date": "2026-05-13", "ai_attributed": "confirmed",
     "source_urls": ["https://www.cnbc.com/2026/05/13/cisco-csco-q3-earnings-report-2026.html"],
     "note": "Cutting jobs amid surging AI orders"},
    {"company": "Upwork", "headcount": 150, "date": "2026-05-07", "ai_attributed": "confirmed",
     "source_urls": ["https://www.marketwatch.com/story/upwork-to-cut-24-of-staff-in-restructuring-citing-evolving-nature-of-work-ab064f91"],
     "note": "Citing evolving 'Nature of Work' (AI)"},
    {"company": "DeepL", "headcount": 250, "date": "2026-05-07", "ai_attributed": "confirmed",
     "source_urls": ["https://www.bloomberg.com/news/articles/2026-05-07/google-translate-rival-deepl-announces-plans-to-cut-25-of-staff"],
     "note": "AI translation company restructuring"},
    {"company": "Bill Holdings", "headcount": 709, "date": "2026-05-07", "ai_attributed": "likely",
     "source_urls": ["https://www.marketwatch.com/story/bill-holdings-to-cut-workforce-by-up-to-30-2e977878"],
     "note": "30% workforce cut"},
    {"company": "ZoomInfo", "headcount": 600, "date": "2026-05-11", "ai_attributed": "confirmed",
     "source_urls": ["https://thenextweb.com/news/zoominfo-beat-earnings-cut-600-jobs-and-lost-29-per-cent-of-its-stock-price-its-database-is-being-repriced-by-ai"],
     "note": "Database being repriced by AI"},
    {"company": "Walmart Tech", "headcount": 1000, "date": "2026-05-12", "ai_attributed": "likely",
     "source_urls": ["https://www.wsj.com/business/retail/walmart-layoffs-relocates-technology-jobs-23bbf322"],
     "note": "Combining global-tech and product teams"},
    {"company": "AI21", "headcount": 110, "date": "2026-05-18", "ai_attributed": "confirmed",
     "source_urls": ["https://www.calcalistech.com/ctechnews/article/rjwumhukfx"],
     "note": "60% workforce cut in strategic overhaul"},
    {"company": "Kraken", "headcount": 150, "date": "2026-05-15", "ai_attributed": "confirmed",
     "source_urls": ["https://www.bloomberg.com/news/articles/2026-05-15/kraken-cuts-150-workers-after-deploying-ai-ipo-may-slip-to-2027"],
     "note": "Cuts after deploying AI"},
    {"company": "Dune Analytics", "headcount": 50, "date": "2026-05-14", "ai_attributed": "confirmed",
     "source_urls": ["https://www.theblock.co/post/401322/crypto-data-firm-dune-cuts-25-of-staff-citing-ai-efficiencies"],
     "note": "Citing AI efficiencies"},
    {"company": "Gambling.com", "headcount": 140, "date": "2026-05-15", "ai_attributed": "confirmed",
     "source_urls": ["https://www.gamblinginsider.com/news/160339/gambling-com-to-cut-25-of-jobs-in-ai-first-shift-as-q1-earnings-hurt-by-rising-costs"],
     "note": "AI-First Shift"},
    {"company": "Truecaller", "headcount": 70, "date": "2026-05-08", "ai_attributed": "likely",
     "source_urls": ["https://techcrunch.com/2026/05/08/truecaller-slashes-70-jobs-amid-declining-ad-sales/"],
     "note": "Slashes jobs amid market changes"},
    {"company": "Staffbase", "headcount": 176, "date": "2026-05-08", "ai_attributed": "likely",
     "source_urls": ["https://www.saechsische.de/wirtschaft/regional/staffbase-streicht-jede-fuenfte-stelle-harter-einschnitt-bei-saechsischem-einhorn-FKVL5SIOTNCWXJMUEUFAGQUAHY.html"],
     "note": "22% workforce cut"},
    {"company": "Phreesia", "headcount": 220, "date": "2026-05-11", "ai_attributed": "likely",
     "source_urls": ["https://www.streetinsider.com/Corporate+News/Phreesia+eliminates+220+positions+in+restructuring+plan/26468756.html"],
     "note": "Restructuring plan"},
    {"company": "GitLab", "headcount": 100, "date": "2026-05-11", "ai_attributed": "confirmed",
     "source_urls": ["https://www.bloomberg.com/news/articles/2026-05-11/gitlab-says-will-cut-jobs-to-spend-on-growth-in-agentic-era"],
     "note": "Cut jobs to spend on growth in 'Agentic Era'"},
    {"company": "Block (Square/Cash App)", "headcount": 4000, "date": "2026-04-01", "ai_attributed": "confirmed",
     "source_urls": ["https://block.xyz/inside/from-hierarchy-to-intelligence",
                     "https://fortune.com/2026/04/17/twitter-cofounder-block-ceo-jack-dorsey-thought-process-laid-off-40-staff-ai/"],
     "note": "CEO Jack Dorsey explicitly replaced middle management with AI intelligence layer; ~40% of staff. Co-published manifesto with Sequoia's Roelof Botha."},
    {"company": "Oracle", "headcount": 3000, "date": "2025-09-01", "ai_attributed": "likely",
     "source_urls": ["https://www.businessinsider.com/oracle-layoffs-2025"],
     "note": "Ongoing restructuring as Oracle pivots to AI cloud services; multiple rounds through 2025"},
]

# ============================================================
# 第二部分：Challenger 报告月度校准数据（仅美国）
# 来源：Challenger, Gray & Christmas 官方报告
# ============================================================

CHALLENGER_AI_DATA = {
    # 格式: "YYYY-MM": AI导致的裁员人数（仅美国）
    # 来源: Challenger月度报告中 "AI" 作为裁员原因的数字
    "2023-05": 3900,   # 首次追踪，CBS News报道
    "2023-06": 0,
    "2023-07": 0,
    "2023-08": 0,
    "2023-09": 0,
    "2023-10": 0,
    "2023-11": 0,
    "2023-12": 0,
    # 2024年数据（Challenger未逐月公开AI细分，年度总计约4,600）
    "2024-total": 4600,
    # 2025年度总计
    "2025-total": 54836,
    # 2026年逐月
    "2026-01": 7624,   # CME Group报告
    "2026-02": 4680,   # Challenger 2月报告
    "2026-03": 15341,  # Challenger 3月报告 - AI首次成为第一大裁员原因
}

# ============================================================
# 第三部分：构建 events.json
# ============================================================

def build_events_json():
    """从硬编码数据构建初始 events.json"""
    
    events = []
    for event in HISTORICAL_EVENTS:
        events.append({
            "id": f"{event['company']}_{event['date']}".replace(" ", "_").lower(),
            "company": event["company"],
            "date": event["date"],
            "headcount": event["headcount"],
            "ai_attributed": event["ai_attributed"],
            "source_urls": event.get("source_urls", []),
            "note": event.get("note", ""),
            "last_updated": datetime.utcnow().strftime("%Y-%m-%d"),
            "locked": True  # 历史数据锁定，不再修改
        })
    
    # 计算统计
    total_confirmed = sum(e["headcount"] for e in events if e["ai_attributed"] == "confirmed")
    total_likely = sum(e["headcount"] for e in events if e["ai_attributed"] == "likely")
    total_all = sum(e["headcount"] for e in events)
    
    db = {
        "metadata": {
            "start_date": "2023-03-14",
            "last_updated": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "total_confirmed": total_confirmed,
            "total_estimated": total_all,
            "total_likely": total_likely,
            "last_calibration_date": "2026-04-02",
            "calibration_source": "Challenger, Gray & Christmas March 2026 Report",
            "challenger_cumulative_ai_cuts": 99470,
            "note": "Challenger data is US-only. Our dataset includes global events."
        },
        "challenger_monthly": CHALLENGER_AI_DATA,
        "events": events
    }
    
    return db


def print_summary(db):
    """打印数据摘要"""
    events = db["events"]
    
    print("=" * 60)
    print("AI裁员追踪器 - 历史数据导入摘要")
    print("=" * 60)
    print(f"总事件数: {len(events)}")
    print(f"总影响人数（宽泛口径）: {db['metadata']['total_estimated']:,}")
    print(f"  - confirmed（公司明确因AI）: {db['metadata']['total_confirmed']:,}")
    print(f"  - likely（高度相关）: {db['metadata']['total_likely']:,}")
    print()
    
    # 按年份统计
    by_year = {}
    for e in events:
        year = e["date"][:4]
        by_year.setdefault(year, {"count": 0, "headcount": 0})
        by_year[year]["count"] += 1
        by_year[year]["headcount"] += e["headcount"]
    
    print("按年份统计:")
    print(f"{'年份':<8} {'事件数':<10} {'影响人数':<15}")
    print("-" * 35)
    for year in sorted(by_year.keys()):
        d = by_year[year]
        print(f"{year:<8} {d['count']:<10} {d['headcount']:>12,}")
    
    print()
    print("Challenger 报告校准数据（仅美国）:")
    print(f"  2023年5月至今累计: {db['metadata']['challenger_cumulative_ai_cuts']:,} 人")
    print()
    print("⚠️  注意事项:")
    print("  1. BT Group的55,000是到2030年的计划数字，实际已执行的可能远少于此")
    print("  2. 部分'likely'事件可能与AI无直接关系")
    print("  3. 此数据集不包含所有事件，仅为重大公开事件")
    print("  4. 建议在页面上使用 confirmed 口径作为主数字")
    print("=" * 60)


def save_to_file(db, output_path="data/events.json"):
    """保存到文件"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    print(f"\n✅ 数据已保存到: {output_path}")


# ============================================================
# 第四部分（可选）：使用 LLM 补充标注
# 如果设置了 OPENAI_API_KEY，可以对 "unclear" 事件进行重新评估
# ============================================================

def llm_review_events(db):
    """使用LLM对unclear事件进行重新评估（可选）"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("\n⏭️  未设置 OPENAI_API_KEY，跳过 LLM 归因审查")
        return db
    
    from openai import OpenAI
    client = OpenAI()
    
    unclear_events = [e for e in db["events"] if e["ai_attributed"] == "unclear"]
    if not unclear_events:
        print("\n✅ 没有需要审查的 unclear 事件")
        return db
    
    print(f"\n🤖 使用 LLM 审查 {len(unclear_events)} 个 unclear 事件...")
    
    events_text = "\n".join([
        f"- {e['company']}, {e['headcount']} people, {e['date']}, note: {e.get('note', 'N/A')}"
        for e in unclear_events
    ])
    
    prompt = f"""Review these layoff events and classify each as:
- "confirmed": if the company explicitly stated AI/automation as a reason
- "likely": if the company was investing in AI while cutting jobs, or restructuring for AI
- "unclear": if there's no clear AI connection

Events:
{events_text}

Return a JSON object: {{"classifications": [{{"company": "...", "ai_attributed": "confirmed|likely|unclear"}}]}}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    classifications = {c["company"]: c["ai_attributed"] for c in result.get("classifications", [])}
    
    updated = 0
    for event in db["events"]:
        if event["company"] in classifications:
            new_attr = classifications[event["company"]]
            if new_attr != event["ai_attributed"]:
                event["ai_attributed"] = new_attr
                updated += 1
    
    print(f"  更新了 {updated} 个事件的归因标注")
    
    # 重新计算统计
    db["metadata"]["total_confirmed"] = sum(
        e["headcount"] for e in db["events"] if e["ai_attributed"] == "confirmed"
    )
    db["metadata"]["total_likely"] = sum(
        e["headcount"] for e in db["events"] if e["ai_attributed"] == "likely"
    )
    db["metadata"]["total_estimated"] = sum(
        e["headcount"] for e in db["events"]
    )
    
    return db


# ============================================================
# 主程序
# ============================================================

if __name__ == "__main__":
    print("🚀 开始导入历史数据...\n")
    
    # 构建数据
    db = build_events_json()
    
    # 可选：LLM审查
    if "--review" in sys.argv:
        db = llm_review_events(db)
    
    # 打印摘要
    print_summary(db)
    
    # 保存
    output_path = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "data/events.json"
    save_to_file(db, output_path)
    
    print("\n📋 后续步骤:")
    print("  1. 检查 data/events.json 中的数据是否合理")
    print("  2. 根据需要手动添加更多历史事件")
    print("  3. 运行 python scripts/generate_page.py 生成页面")
    print("  4. git add && git commit && git push 触发部署")
