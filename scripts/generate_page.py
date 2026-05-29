#!/usr/bin/env python3
"""
Page Generator - AI Layoff Tracker
====================================
Generates a static HTML warning page from data/events.json.
"""

import json
import os
from datetime import datetime


def generate_html():
    """Generate static HTML warning page from data."""
    
    db_file = "data/events.json"
    if not os.path.exists(db_file):
        print("data/events.json not found. Run import_historical_data.py first.")
        return
    
    with open(db_file, "r", encoding="utf-8") as f:
        db = json.load(f)
    
    total_confirmed = db["metadata"]["total_confirmed"]
    total_estimated = db["metadata"]["total_estimated"]
    total_likely = db["metadata"].get("total_likely", total_estimated - total_confirmed)
    last_updated = db["metadata"]["last_updated"]
    event_count = len(db["events"])
    challenger_total = db["metadata"].get("challenger_cumulative_ai_cuts", 99470)
    
    # Days since GPT-4 launch
    start = datetime(2023, 3, 14)
    days_since = (datetime.utcnow() - start).days
    avg_per_day = total_estimated // max(days_since, 1)
    
    # Recent 20 events
    recent_events = sorted(db["events"], key=lambda x: x["date"], reverse=True)[:20]
    
    import json as _json
    all_events_json = _json.dumps(db["events"])

    # Ticker — all events sorted by date desc, confirmed first
    ticker_events = sorted(db["events"], key=lambda x: (x["date"], x["ai_attributed"] == "confirmed"), reverse=True)
    ticker_items = ""
    for e in ticker_events:
        count_str = f'{e["headcount"]:,}' if e["headcount"] > 0 else "?"
        month = e["date"][:7]
        ticker_items += f'<span class="ticker-item"><span class="ticker-company">{e["company"]}</span><span class="ticker-count">▼ {count_str} jobs</span><span class="ticker-date">{month}</span></span><span class="ticker-sep">|</span>'

    recent_html = ""
    for e in recent_events:
        badge_class = {
            "confirmed": "badge-confirmed",
            "likely": "badge-likely",
            "unclear": "badge-unclear"
        }.get(e["ai_attributed"], "badge-unclear")
        
        source_link = ""
        if e.get("source_urls") and e["source_urls"][0]:
            url = e["source_urls"][0]
            ls = (e.get("link_status") or {}).get(url, {})
            if ls.get("alive") is False and ls.get("last_alive"):
                source_link = (
                    f'<a href="{url}" target="_blank" rel="noopener" style="color:#999">source</a>'
                    f' <span style="color:#888;font-size:0.7rem" title="Link may be unavailable">⚠ last live: {ls["last_alive"]}</span>'
                )
            else:
                source_link = f'<a href="{url}" target="_blank" rel="noopener">source</a>'
        
        headcount_str = f'{e["headcount"]:,}' if e["headcount"] > 0 else "N/A"
        
        recent_html += f"""
            <tr>
                <td class="date-col">{e['date']}</td>
                <td class="company-col">{e['company']}</td>
                <td class="number-col">{headcount_str}</td>
                <td><span class="badge {badge_class}">{e['ai_attributed']}</span></td>
                <td>{source_link}</td>
            </tr>"""
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Layoff Tracker - Global Warning</title>
    <meta name="description" content="Tracking job losses directly attributed to AI since GPT-4 launched. The iceberg behind the 2.9M total announced U.S. cuts. Updated daily.">
    <meta property="og:title" content="AI Layoff Tracker - Global Warning">
    <meta property="og:description" content="Since GPT-4 launched {days_since} days ago, {total_estimated:,} jobs have been directly attributed to AI. Behind that: 2.9M total announced U.S. cuts. The iceberg is real.">
    <meta property="og:type" content="website">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="AI Layoff Tracker - {total_estimated:,} jobs lost directly to AI">
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-C8VV4PTKJ5"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', 'G-C8VV4PTKJ5');
    </script>
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
        .dual-stat {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
            margin-bottom: 1.5rem;
        }}
        @media (max-width: 600px) {{
            .dual-stat {{ grid-template-columns: 1fr; }}
        }}
        .stat-block {{
            padding: 1.5rem;
            border-radius: 10px;
            text-align: center;
        }}
        .stat-fear {{
            background: linear-gradient(135deg, #1a0a00 0%, #0a0a0a 100%);
            border: 1px solid #3d2211;
            position: relative;
        }}
        .stat-jobs {{
            background: linear-gradient(135deg, #1a0000 0%, #0a0a0a 100%);
            border: 1px solid #3d1111;
        }}
        .stat-label {{
            font-size: 0.65rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            color: #666;
            margin-bottom: 0.4rem;
        }}
        .stat-fear .stat-value {{
            font-size: 3rem;
            font-weight: 800;
            color: #ff8844;
            line-height: 1;
        }}
        .stat-jobs .stat-value {{
            font-size: 2.2rem;
            font-weight: 800;
            color: #ff4444;
            line-height: 1;
            font-variant-numeric: tabular-nums;
        }}
        .stat-sub {{
            font-size: 0.75rem;
            color: #555;
            margin-top: 0.3rem;
        }}
        .stat-context {{
            font-size: 0.7rem;
            color: #444;
            margin-top: 0.5rem;
            line-height: 1.5;
        }}
        .fear-compare {{
            display: flex;
            justify-content: center;
            flex-wrap: wrap;
            gap: 0.35rem;
            margin-top: 0.75rem;
        }}
        .fc-item {{
            font-size: 0.65rem;
            padding: 2px 7px;
            border-radius: 3px;
            white-space: nowrap;
        }}
        .fc-worse {{ background: #1a1a1a; color: #555; }}
        .fc-ai {{ background: #3d2211; color: #ff8844; font-weight: 700; }}
        .fc-better {{ background: #111; color: #444; }}
        .stat-jobs2 {{
            background: linear-gradient(135deg, #001a0a 0%, #0a0a0a 100%);
            border: 1px solid #113d22;
        }}
        .stat-jobs2 .stat-value {{
            font-size: 3rem;
            font-weight: 800;
            color: #44aa66;
            line-height: 1;
            font-variant-numeric: tabular-nums;
        }}
        .stat-gig {{
            background: linear-gradient(135deg, #1a001a 0%, #0a0a0a 100%);
            border: 1px solid #3d113d;
        }}
        .stat-gig .stat-value {{
            font-size: 3rem;
            font-weight: 800;
            color: #cc66ff;
            line-height: 1;
            font-variant-numeric: tabular-nums;
        }}
        .expand-hint {{
            display: inline-block;
            color: #333;
            font-size: 0.65rem;
            margin-left: 0.35rem;
            transition: transform 0.2s;
            user-select: none;
        }}
        .event-row.expanded .expand-hint {{ transform: rotate(90deg); color: #666; }}
        .evisceration-section {{
            margin-top: 3rem;
            padding: 2rem;
            background: linear-gradient(135deg, #100a00 0%, #0a0a0a 100%);
            border: 1px solid #2a1800;
            border-radius: 12px;
        }}
        .evisceration-section h2 {{
            font-size: 1.3rem;
            color: #ff8844;
            margin-bottom: 0.4rem;
        }}
        .evis-sub {{
            color: #555;
            font-size: 0.82rem;
            margin-bottom: 1.25rem;
            line-height: 1.6;
        }}
        .evis-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 0.75rem;
            margin-bottom: 1rem;
        }}
        @media (max-width: 750px) {{
            .evis-grid {{ grid-template-columns: 1fr 1fr; }}
        }}
        @media (max-width: 500px) {{
            .evis-grid {{ grid-template-columns: 1fr; }}
        }}
        .evis-stat {{
            padding: 1rem;
            background: #0d0d0d;
            border: 1px solid #1a1a1a;
            border-radius: 8px;
        }}
        .evis-stat-value {{
            font-size: 2.2rem;
            font-weight: 800;
            color: #ff8844;
            line-height: 1;
            margin-bottom: 0.3rem;
            font-variant-numeric: tabular-nums;
        }}
        .evis-stat-label {{
            font-size: 0.73rem;
            color: #666;
            line-height: 1.5;
        }}
        .evis-quote {{
            padding: 0.9rem 1.1rem;
            border-left: 3px solid #3d2211;
            background: #0d0d0d;
            border-radius: 0 8px 8px 0;
            margin-top: 1rem;
        }}
        .evis-quote p {{
            color: #aaa;
            font-size: 0.83rem;
            line-height: 1.7;
            font-style: italic;
        }}
        .evis-quote cite {{
            display: block;
            color: #555;
            font-size: 0.72rem;
            margin-top: 0.4rem;
            font-style: normal;
        }}
        @media (max-width: 600px) {{
            .stat-fear .stat-value {{ font-size: 2.2rem; }}
            .stat-jobs .stat-value {{ font-size: 1.8rem; }}
            .stat-jobs2 .stat-value {{ font-size: 2.2rem; }}
            .stat-gig .stat-value {{ font-size: 2.2rem; }}
        }}
        .doomsday-hero {{
            text-align: center;
            padding: 3rem 1rem 2.5rem;
            margin-bottom: 2rem;
            border-bottom: 1px solid #1a0000;
        }}
        .dd-label {{
            font-size: 0.7rem;
            letter-spacing: 0.18em;
            text-transform: uppercase;
            color: #ff4444;
            font-weight: 700;
            margin-bottom: 0.5rem;
        }}
        .dd-number {{
            font-size: 6rem;
            font-weight: 900;
            color: #ff2222;
            line-height: 1;
            font-variant-numeric: tabular-nums;
            letter-spacing: -0.02em;
            animation: dd-breathe 3s ease-in-out infinite;
        }}
        @keyframes dd-breathe {{
            0%, 100% {{ text-shadow: 0 0 20px rgba(255,34,34,0.2), 0 0 60px rgba(255,34,34,0.05); }}
            50% {{ text-shadow: 0 0 40px rgba(255,34,34,0.6), 0 0 100px rgba(255,34,34,0.2); }}
        }}
        .dd-number.dd-tick {{
            animation: dd-flash 0.6s ease-out forwards;
        }}
        @keyframes dd-flash {{
            0% {{ color: #ff2222; text-shadow: 0 0 20px rgba(255,34,34,0.3); }}
            30% {{ color: #ffffff; text-shadow: 0 0 60px rgba(255,255,255,0.9), 0 0 120px rgba(255,34,34,0.8); }}
            100% {{ color: #ff2222; animation: dd-breathe 3s ease-in-out infinite; }}
        }}
        .dd-live-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: #ff2222;
            color: #fff;
            font-size: 0.68rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            padding: 3px 10px 3px 8px;
            border-radius: 3px;
            margin-bottom: 0.75rem;
        }}
        .dd-live-dot {{
            width: 6px;
            height: 6px;
            background: #fff;
            border-radius: 50%;
            animation: blink 1s infinite;
        }}
        .dd-sublabel {{
            margin-top: 0.6rem;
            font-size: 0.9rem;
            color: #555;
        }}
        .dd-since {{
            margin-top: 0.4rem;
            font-size: 0.72rem;
            color: #333;
        }}
        .dd-progress-wrap {{
            margin-top: 1.5rem;
            max-width: 500px;
            margin-left: auto;
            margin-right: auto;
        }}
        .dd-progress-label {{
            display: flex;
            justify-content: space-between;
            font-size: 0.68rem;
            color: #555;
            margin-bottom: 0.35rem;
        }}
        .dd-progress-label strong {{ color: #ff8844; }}
        .dd-progress-track {{
            background: #111;
            border-radius: 4px;
            height: 10px;
            overflow: hidden;
            border: 1px solid #1a1a1a;
        }}
        .dd-progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #3d1111, #ff8844);
            border-radius: 4px;
            transition: width 1s ease-out;
        }}
        .dd-progress-note {{
            font-size: 0.65rem;
            color: #333;
            margin-top: 0.3rem;
            text-align: center;
        }}
        .voices-section {{
            margin-top: 3rem;
        }}
        .voices-section h2 {{
            font-size: 1.3rem;
            color: #ccc;
            margin-bottom: 0.25rem;
        }}
        .voices-sub {{
            font-size: 0.78rem;
            color: #555;
            margin-bottom: 1.25rem;
        }}
        .voice-row {{
            padding: 1.1rem 1.25rem;
            border-left: 3px solid #2a1800;
            background: #0d0d0d;
            border-radius: 0 8px 8px 0;
            margin-bottom: 0.75rem;
        }}
        .voice-row.papal {{ border-left-color: #1a2a1a; }}
        .voice-row.yang {{ border-left-color: #1a1a2a; }}
        .voice-quote {{
            font-size: 0.88rem;
            color: #bbb;
            line-height: 1.7;
            font-style: italic;
            margin-bottom: 0.4rem;
        }}
        .voice-attr {{
            font-size: 0.7rem;
            color: #555;
            font-style: normal;
        }}
        .voice-attr strong {{ color: #777; }}
        @media (max-width: 600px) {{
            .dd-number {{ font-size: 3.5rem; }}
        }}
        .projection-hero {{
            text-align: center;
            margin: 2rem 0;
            padding: 3rem 2rem 2.5rem;
            background: linear-gradient(180deg, #1a0000 0%, #0a0000 60%, #0a0a0a 100%);
            border: 1px solid #3d1111;
            border-radius: 12px;
        }}
        .proj-eyebrow {{
            font-size: 0.7rem;
            letter-spacing: 0.15em;
            color: #ff4444;
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 0.75rem;
        }}
        .proj-number {{
            font-size: 5.5rem;
            font-weight: 900;
            color: #ff2222;
            line-height: 1;
            font-variant-numeric: tabular-nums;
            text-shadow: 0 0 50px rgba(255,34,34,0.35);
        }}
        .proj-label {{
            font-size: 1rem;
            color: #888;
            margin-top: 0.5rem;
        }}
        .proj-source {{
            font-size: 0.7rem;
            color: #3d1111;
            margin-top: 0.4rem;
            margin-bottom: 2rem;
        }}
        .proj-vs {{
            display: flex;
            justify-content: center;
            gap: 0;
            padding-top: 1.75rem;
            border-top: 1px solid #2a0000;
            flex-wrap: wrap;
        }}
        .proj-vs-item {{
            text-align: center;
            padding: 0 2rem;
            border-right: 1px solid #1a0000;
        }}
        .proj-vs-item:last-child {{ border-right: none; }}
        .proj-vs-value {{
            font-size: 1.8rem;
            font-weight: 800;
            color: #ff6633;
            font-variant-numeric: tabular-nums;
        }}
        .proj-vs-label {{
            font-size: 0.68rem;
            color: #555;
            margin-top: 0.25rem;
            line-height: 1.5;
        }}
        @media (max-width: 600px) {{
            .proj-number {{ font-size: clamp(1.8rem, 10vw, 3.5rem); }}
            .proj-vs-item {{ padding: 0.75rem 1rem; border-right: none; border-bottom: 1px solid #1a0000; width: 100%; }}
            .proj-vs-item:last-child {{ border-bottom: none; }}
        }}
        .pace-section {{
            margin-top: 3rem;
        }}
        .pace-section h2 {{
            font-size: 1.3rem;
            color: #ccc;
            margin-bottom: 0.3rem;
        }}
        .pace-sub {{
            font-size: 0.78rem;
            color: #555;
            margin-bottom: 1.25rem;
        }}
        .pace-row {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
            margin-bottom: 0.6rem;
        }}
        .pace-year-tag {{
            font-size: 0.78rem;
            color: #666;
            width: 3.5rem;
            flex-shrink: 0;
            text-align: right;
        }}
        .pace-bar-wrap {{
            flex: 1;
            background: #111;
            border-radius: 3px;
            height: 22px;
            overflow: hidden;
        }}
        .pace-bar {{
            height: 100%;
            background: linear-gradient(90deg, #3d1111, #ff4444);
            border-radius: 3px;
            transition: width 0.3s;
        }}
        .pace-bar.record {{ background: linear-gradient(90deg, #4a0000, #ff2222); }}
        .pace-val {{
            font-size: 0.8rem;
            color: #ff6666;
            font-weight: 600;
            font-variant-numeric: tabular-nums;
            width: 5.5rem;
            flex-shrink: 0;
        }}
        .pace-note {{
            font-size: 0.75rem;
            color: #555;
            margin-top: 0.75rem;
            padding: 0.6rem 1rem;
            background: #0d0d0d;
            border-left: 3px solid #3d1111;
            border-radius: 0 4px 4px 0;
        }}
        .pace-note strong {{ color: #ff4444; }}
        .jobs-section {{
            margin-top: 3rem;
            padding: 2rem;
            background: #0d0d0d;
            border: 1px solid #1a1a1a;
            border-radius: 12px;
        }}
        .jobs-section h2 {{
            font-size: 1.3rem;
            color: #ccc;
            margin-bottom: 0.3rem;
        }}
        .jobs-sub {{
            font-size: 0.8rem;
            color: #555;
            margin-bottom: 1.5rem;
            line-height: 1.6;
        }}
        .jobs-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.75rem;
            margin-bottom: 1rem;
        }}
        @media (max-width: 600px) {{ .jobs-grid {{ grid-template-columns: 1fr; }} }}
        .jobs-gaining {{
            padding: 1.25rem;
            background: #0d1a0d;
            border: 1px solid #1a3a1a;
            border-radius: 8px;
        }}
        .jobs-gaining h3 {{
            font-size: 0.7rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: #44aa66;
            margin-bottom: 0.75rem;
        }}
        .jobs-losing {{
            padding: 1.25rem;
            background: #1a0d0d;
            border: 1px solid #3a1a1a;
            border-radius: 8px;
        }}
        .jobs-losing h3 {{
            font-size: 0.7rem;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            color: #aa4444;
            margin-bottom: 0.75rem;
        }}
        .jobs-row {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin-bottom: 0.5rem;
            gap: 0.5rem;
        }}
        .jobs-row-label {{
            font-size: 0.8rem;
            color: #888;
        }}
        .jobs-row-val {{
            font-size: 0.85rem;
            font-weight: 700;
            font-variant-numeric: tabular-nums;
            white-space: nowrap;
        }}
        .val-green {{ color: #44aa66; }}
        .val-red {{ color: #cc4444; }}
        .val-grey {{ color: #666; }}
        .jobs-callout {{
            margin-top: 1rem;
            padding: 0.75rem 1rem;
            background: #0a0a0a;
            border-left: 3px solid #44aa66;
            border-radius: 0 6px 6px 0;
            font-size: 0.78rem;
            color: #666;
            line-height: 1.7;
        }}
        .jobs-callout strong {{ color: #888; }}
        .ticker-wrap {{
            width: 100%;
            background: #0f0000;
            border-top: 1px solid #3d1111;
            border-bottom: 1px solid #3d1111;
            padding: 0.6rem 0;
            overflow: hidden;
            margin-bottom: 2rem;
            position: relative;
            animation: ticker-border-pulse 3s ease-in-out infinite;
        }}
        @keyframes ticker-border-pulse {{
            0%, 100% {{ border-color: #3d1111; box-shadow: none; }}
            50% {{ border-color: #7a2222; box-shadow: 0 0 12px rgba(255,34,34,0.15); }}
        }}
        .ticker-live {{
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            display: flex;
            align-items: center;
            padding: 0 1rem;
            background: #ff4444;
            color: #fff;
            font-size: 0.75rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            z-index: 2;
            white-space: nowrap;
        }}
        .ticker-live::before {{
            content: '';
            display: inline-block;
            width: 7px;
            height: 7px;
            background: #fff;
            border-radius: 50%;
            margin-right: 6px;
            animation: blink 1s infinite;
        }}
        @keyframes blink {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.2; }}
        }}
        .ticker-track {{
            display: flex;
            white-space: nowrap;
            animation: ticker-scroll 60s linear infinite;
            padding-left: 90px;
        }}
        .ticker-track:hover {{ animation-play-state: paused; }}
        @keyframes ticker-scroll {{
            0% {{ transform: translateX(100vw); }}
            100% {{ transform: translateX(-100%); }}
        }}
        .ticker-item {{
            display: inline-flex;
            align-items: center;
            margin-right: 3rem;
            font-size: 0.85rem;
            color: #ff8888;
        }}
        .ticker-company {{ color: #ffcccc; font-weight: 600; margin-right: 0.4rem; }}
        .ticker-count {{ color: #ff4444; font-weight: 700; margin-right: 0.4rem; }}
        .ticker-date {{ color: #666; font-size: 0.75rem; }}
        .ticker-sep {{ color: #3d1111; margin: 0 1.5rem; }}
        .submit-section {{
            margin-top: 3rem;
            padding: 2rem;
            background: #0d0d0d;
            border: 1px solid #1a1a1a;
            border-radius: 8px;
        }}
        .submit-section h2 {{
            font-size: 1.3rem;
            color: #ccc;
            margin-bottom: 0.5rem;
        }}
        .submit-section > p {{
            color: #666;
            font-size: 0.85rem;
            margin-bottom: 1.5rem;
        }}
        .form-row {{
            display: flex;
            gap: 0.75rem;
            margin-bottom: 0.75rem;
            flex-wrap: wrap;
        }}
        .form-row input {{
            background: #111;
            border: 1px solid #2a2a2a;
            color: #e0e0e0;
            padding: 0.6rem 0.75rem;
            border-radius: 6px;
            font-size: 0.85rem;
            font-family: inherit;
            flex: 1;
            min-width: 140px;
        }}
        .form-row input:focus {{
            outline: none;
            border-color: #444;
        }}
        .submit-btn {{
            background: #ff4444;
            color: #fff;
            border: none;
            padding: 0.7rem 1.5rem;
            border-radius: 6px;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            margin-top: 0.25rem;
        }}
        .submit-btn:hover {{ background: #cc3333; }}
        .submit-btn:disabled {{ background: #555; cursor: not-allowed; }}
        .submit-success {{
            display: none;
            padding: 1.5rem;
            background: #0d1a0d;
            border: 1px solid #1a3a1a;
            border-radius: 8px;
            text-align: center;
        }}
        .submit-success h3 {{ color: #44aa44; margin-bottom: 0.5rem; font-size: 1.1rem; }}
        .submit-success p {{ color: #666; font-size: 0.85rem; margin-bottom: 1rem; }}
        .follow-cta {{
            display: flex;
            gap: 0.75rem;
            justify-content: center;
            flex-wrap: wrap;
            margin-top: 1rem;
        }}
        .follow-btn {{
            display: inline-block;
            padding: 0.5rem 1.1rem;
            border-radius: 6px;
            font-size: 0.85rem;
            font-weight: 500;
            text-decoration: none;
        }}
        .follow-btn.instagram {{ background: #2a1a2e; color: #cc88ff; }}
        .follow-btn.instagram:hover {{ background: #3a1a4e; text-decoration: none; }}
        .cta-section {{
            margin-top: 3rem;
            padding: 3rem 2rem;
            background: linear-gradient(135deg, #0a0f1a 0%, #0a0a0a 100%);
            border: 1px solid #1a2a3a;
            border-radius: 12px;
            text-align: center;
        }}
        .cta-pre {{
            font-size: 0.75rem;
            letter-spacing: 0.12em;
            color: #ff4444;
            font-weight: 700;
            text-transform: uppercase;
            margin-bottom: 0.75rem;
        }}
        .cta-headline {{
            font-size: 1.5rem;
            color: #e0e0e0;
            font-weight: 700;
            line-height: 1.4;
            margin-bottom: 1.25rem;
        }}
        .cta-body {{
            color: #666;
            font-size: 0.9rem;
            line-height: 1.8;
            margin-bottom: 1rem;
        }}
        .cta-body em {{ color: #aaa; font-style: normal; font-weight: 500; }}
        .cta-mission {{
            font-size: 0.85rem;
            color: #555;
            margin-bottom: 1.75rem;
        }}
        .cta-mission strong {{ color: #888; }}
        .cta-actions {{
            display: flex;
            gap: 0.75rem;
            justify-content: center;
            flex-wrap: wrap;
        }}
        .cta-btn {{
            display: inline-block;
            padding: 0.7rem 1.5rem;
            border-radius: 7px;
            font-size: 0.9rem;
            font-weight: 600;
            text-decoration: none;
            transition: opacity 0.15s;
        }}
        .cta-btn:hover {{ opacity: 0.85; text-decoration: none; }}
        .cta-primary {{ background: #1a3a5a; color: #66aaff; }}
        .cta-secondary {{ background: #111; border: 1px solid #2a2a2a; color: #666; }}
        @media (max-width: 600px) {{
            .cta-headline {{ font-size: 1.2rem; }}
        }}
        .controls {{
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 1rem;
            align-items: center;
        }}
        .controls-group {{
            display: flex;
            gap: 0.4rem;
            flex-wrap: wrap;
        }}
        .ctrl-btn {{
            background: #111;
            border: 1px solid #2a2a2a;
            color: #888;
            padding: 0.4rem 0.85rem;
            border-radius: 5px;
            font-size: 0.78rem;
            cursor: pointer;
            white-space: nowrap;
            transition: all 0.15s;
        }}
        .ctrl-btn:hover {{ border-color: #444; color: #ccc; }}
        .ctrl-btn.active {{ background: #1a1a1a; border-color: #ff4444; color: #ff6666; font-weight: 600; }}
        .ctrl-divider {{ width: 1px; background: #222; margin: 0 0.25rem; align-self: stretch; }}
        .search-input {{
            background: #111;
            border: 1px solid #2a2a2a;
            color: #e0e0e0;
            padding: 0.4rem 0.75rem;
            border-radius: 5px;
            font-size: 0.78rem;
            font-family: inherit;
            flex: 1;
            min-width: 140px;
            max-width: 220px;
        }}
        .search-input:focus {{ outline: none; border-color: #444; }}
        .search-input::placeholder {{ color: #444; }}
        .row-count {{ color: #555; font-size: 0.75rem; margin-left: auto; white-space: nowrap; }}
        .event-row:hover td {{ background: #111; }}
        .event-row td {{ transition: background 0.1s; }}
        .detail-cell {{
            padding: 0.75rem 1rem !important;
            background: #0d0d0d;
            border-bottom: 1px solid #222;
        }}
        .detail-note {{
            color: #aaa;
            font-size: 0.82rem;
            line-height: 1.6;
            margin-bottom: 0.4rem;
        }}
        .detail-sources {{
            font-size: 0.75rem;
            color: #555;
        }}
        .detail-sources a {{ color: #4488cc; }}
        .table-wrap {{ overflow-x: auto; -webkit-overflow-scrolling: touch; }}
        @media (max-width: 600px) {{
            .number {{ font-size: 3rem; }}
            .number.secondary {{ font-size: 1.8rem; }}
            h1 {{ font-size: 1.8rem; }}
            table {{ font-size: 0.75rem; }}
            .search-input {{ max-width: 100%; }}
            .row-count {{ display: none; }}
        }}
    </style>
</head>
<body>
    <main>
        <header>
            <h1>&#9888;&#65039; AI Layoff Warning</h1>
            <p class="subtitle">Community-verified &middot; sourced by public news announcements &middot; since GPT-4 launch (March 14, 2023)</p>
        </header>

        <section class="doomsday-hero">
            <div class="dd-live-badge"><span class="dd-live-dot"></span>LIVE</div>
            <div class="dd-label">JOBS LOST DIRECTLY TO AI</div>
            <div class="dd-number" id="dd-counter">{total_estimated:,}</div>
            <div class="dd-sublabel">and counting &nbsp;&middot;&nbsp; <span id="dd-rate"></span> &nbsp;&middot;&nbsp; <span style="color:#666">{total_confirmed:,} confirmed</span></div>
            <div class="dd-since">{days_since} days &nbsp;&middot;&nbsp; {event_count} events &nbsp;&middot;&nbsp; since March 14, 2023 &nbsp;&middot;&nbsp; scroll to see the full picture &darr;</div>
            <div class="dd-progress-wrap">
                <div class="dd-progress-label">
                    <span>est. true AI impact via 6.7&times; multiplier: ~3.2M</span>
                    <strong>10.7% toward 30M by 2028</strong>
                </div>
                <div class="dd-progress-track">
                    <div class="dd-progress-fill" style="width:10.7%"></div>
                </div>
                <div class="dd-progress-note">{total_estimated:,} documented &times; 6.7 unlabeled multiplier = ~3.2M estimated &nbsp;&middot;&nbsp; target: 30M by 2028</div>
            </div>
        </section>

        <section class="projection-hero">
            <div class="proj-eyebrow">&#9888; The Forecast &mdash; McKinsey Global Institute &middot; Goldman Sachs</div>
            <div class="proj-number">30,000,000</div>
            <p class="proj-label">U.S. jobs significantly disrupted by AI &mdash; by 2028</p>
            <p class="proj-source">McKinsey: 40&ndash;50M Americans forced to shift roles by 2030 &nbsp;&middot;&nbsp; Goldman Sachs: 2 in 3 U.S. jobs have meaningful AI exposure &nbsp;&middot;&nbsp; 160M total U.S. workers</p>
            <div class="proj-vs">
                <div class="proj-vs-item">
                    <div class="proj-vs-value">2 in 3</div>
                    <div class="proj-vs-label">U.S. jobs have meaningful<br>AI exposure (Goldman Sachs)</div>
                </div>
                <div class="proj-vs-item">
                    <div class="proj-vs-value">30%</div>
                    <div class="proj-vs-label">of all U.S. work hours<br>automatable by 2030 (McKinsey)</div>
                </div>
                <div class="proj-vs-item">
                    <div class="proj-vs-value">2028</div>
                    <div class="proj-vs-label">two years away &mdash;<br>the inflection point</div>
                </div>
            </div>
        </section>

        <div class="dual-stat">
            <div class="stat-block stat-fear">
                <div class="stat-label">PUBLIC FEAR SCORE</div>
                <div class="stat-value">-20</div>
                <div class="stat-sub">net favorability (NBC, Mar 2026)</div>
                <div class="stat-context">57% say risks outweigh benefits &nbsp;·&nbsp; scale: -100 to +100</div>
                <div class="fear-compare">
                    <span class="fc-item fc-worse">Iran &minus;53</span>
                    <span class="fc-item fc-worse">Dem. Party &minus;22</span>
                    <span class="fc-item fc-ai">&#9654; AI &minus;20</span>
                    <span class="fc-item fc-better">ICE &minus;18</span>
                    <span class="fc-item fc-better">Trump &minus;12</span>
                </div>
            </div>
            <div class="stat-block stat-jobs">
                <div class="stat-label">JOBS LOST DIRECTLY TO AI</div>
                <div class="stat-value">{total_estimated:,}</div>
                <div class="stat-sub">since GPT-4 launch · {days_since} days</div>
                <div class="stat-context">{total_confirmed:,} confirmed &nbsp;·&nbsp; ~{avg_per_day:,}/day</div>
            </div>
            <div class="stat-block stat-jobs2">
                <div class="stat-label">JOBS PER UNEMPLOYED PERSON</div>
                <div class="stat-value">0.9</div>
                <div class="stat-sub">first time below 1.0 since pandemic (BLS, 2026)</div>
                <div class="stat-context">6.9M openings &nbsp;·&nbsp; 7.6M unemployed &nbsp;·&nbsp; more seekers than jobs</div>
            </div>
            <div class="stat-block stat-gig">
                <div class="stat-label">WORKFORCE NOW FREELANCING</div>
                <div class="stat-value">36%</div>
                <div class="stat-sub">57M Americans in gig economy (2025) &mdash; up from 27% in 2016</div>
                <div class="stat-context">Projected 50%+ by 2027 &nbsp;·&nbsp; avg rideshare pay: $9.09/hr after costs</div>
            </div>
        </div>

        <div class="ticker-wrap">
            <div class="ticker-live">🔴 LIVE</div>
            <div class="ticker-track">{ticker_items}{ticker_items}</div>
        </div>


        <section style="margin: 2rem 0; padding: 1.5rem; background: #0d0d0d; border: 1px solid #1a1a1a; border-radius: 10px;">
            <div style="font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;color:#555;margin-bottom:1rem;">The Iceberg &mdash; Jan 2023 to Today</div>
            <div style="display:flex;flex-direction:column;gap:0.75rem;">
                <div>
                    <div style="display:flex;justify-content:space-between;margin-bottom:0.3rem;">
                        <span style="font-size:0.8rem;color:#ff4444;font-weight:600;">AI-attributed (our tracker)</span>
                        <span style="font-size:0.8rem;color:#ff4444;font-weight:700;font-variant-numeric:tabular-nums;">{total_estimated:,}</span>
                    </div>
                    <div style="background:#111;border-radius:3px;height:14px;overflow:hidden;">
                        <div style="width:{round(total_estimated/2906771*100)}%;height:100%;background:linear-gradient(90deg,#3d1111,#ff4444);border-radius:3px;"></div>
                    </div>
                </div>
                <div>
                    <div style="display:flex;justify-content:space-between;margin-bottom:0.3rem;">
                        <span style="font-size:0.8rem;color:#888;">All announced U.S. cuts, all reasons <span style="color:#555;font-weight:400;">(Challenger Gray)</span></span>
                        <span style="font-size:0.8rem;color:#888;font-weight:700;font-variant-numeric:tabular-nums;">2,906,771</span>
                    </div>
                    <div style="background:#111;border-radius:3px;height:14px;overflow:hidden;">
                        <div style="width:100%;height:100%;background:#222;border-radius:3px;"></div>
                    </div>
                </div>
                <div>
                    <div style="display:flex;justify-content:space-between;margin-bottom:0.3rem;">
                        <span style="font-size:0.8rem;color:#444;">Actual involuntary separations, BLS JOLTS <span style="color:#333;font-weight:400;">(all U.S. workers)</span></span>
                        <span style="font-size:0.8rem;color:#444;font-weight:700;">60,000,000+</span>
                    </div>
                    <div style="background:#111;border-radius:3px;height:14px;overflow:hidden;">
                        <div style="width:100%;height:100%;background:#1a1a1a;border-radius:3px;"></div>
                    </div>
                </div>
            </div>
            <div style="margin-top:1.25rem;padding:1rem 1.25rem;background:linear-gradient(135deg,#1a0000 0%,#0d0d0d 100%);border:1px solid #3d1111;border-radius:8px;">
                <div style="font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;color:#ff4444;font-weight:700;margin-bottom:0.5rem;">The 6.7x Inference</div>
                <p style="font-size:0.85rem;color:#ccc;line-height:1.8;margin-bottom:0.75rem;">
                    Companies officially attributed <strong>71,825</strong> U.S. job cuts to AI (Challenger Gray, 2023&ndash;Q1 2026).
                    Our tracker — aggregating global public reporting across the same period — documents <strong>{total_estimated:,}</strong>.
                    That&rsquo;s a <strong style="color:#ff6644;">6.7&times; gap.</strong>
                </p>
                <p style="font-size:0.85rem;color:#888;line-height:1.8;margin-bottom:0.75rem;">
                    For every job loss a company officially blamed on AI, public reporting finds <strong style="color:#ff6644;">6 more</strong> that went unlabeled.
                    Companies don&rsquo;t volunteer AI as the reason &mdash; restructuring, efficiency, and transformation are cleaner PR.
                    But the pattern is visible in the data.
                </p>
                <p style="font-size:0.82rem;color:#666;line-height:1.8;">
                    Applied to the 2.9M total announced U.S. cuts: companies admitted AI in only <strong>2.5%</strong> of cases.
                    If the true ratio holds, the real AI-driven share is closer to <strong style="color:#ff8844;">~17%</strong> &mdash; roughly 490,000&ndash;500,000 in the U.S. alone.
                    Almost exactly what our global tracker shows. Two different methodologies. Same answer.
                </p>
            </div>
        </section>

        <section class="pace-section">
            <h2>The Acceleration</h2>
            <p class="pace-sub">AI-attributed job losses by year &mdash; our tracker (global, all publicly documented events)</p>
            <div class="pace-row">
                <span class="pace-year-tag">2023</span>
                <div class="pace-bar-wrap"><div class="pace-bar" style="width:81.7%"></div></div>
                <span class="pace-val">115,006</span>
            </div>
            <div class="pace-row">
                <span class="pace-year-tag">2024</span>
                <div class="pace-bar-wrap"><div class="pace-bar" style="width:84.7%"></div></div>
                <span class="pace-val">119,260</span>
            </div>
            <div class="pace-row">
                <span class="pace-year-tag">2025</span>
                <div class="pace-bar-wrap"><div class="pace-bar record" style="width:100%"></div></div>
                <span class="pace-val" style="color:#ff2222">140,820 &#9650;</span>
            </div>
            <div class="pace-row">
                <span class="pace-year-tag">2026 <span style="font-size:0.65rem;color:#444">Jan&ndash;May</span></span>
                <div class="pace-bar-wrap"><div class="pace-bar record" style="width:76.2%"></div></div>
                <span class="pace-val" style="color:#ff2222">107,300 &#9650;</span>
            </div>
            <p class="pace-note"><strong>2026 is on pace for ~257,000</strong> &mdash; nearly 2&times; 2025, based on Jan&ndash;May alone. Challenger, Gray &amp; Christmas tracks a subset of these as U.S. employer-disclosed; our tracker aggregates global public reporting across all sources. The acceleration is real regardless of which lens you use.</p>
        </section>

        <section class="jobs-section">
            <h2>So Where Are the New Jobs?</h2>
            <div style="margin-bottom:1.25rem;padding:1rem 1.25rem;background:linear-gradient(135deg,#1a0a00 0%,#0d0d0d 100%);border:1px solid #2a1800;border-radius:8px;font-size:0.85rem;line-height:1.8;color:#888;">
                <strong style="color:#ff8844;display:block;margin-bottom:0.4rem;">The verdict no one said out loud:</strong>
                We&rsquo;ve been in a white-collar recession since the pandemic &mdash; with a brief reprieve in 2022.
                In 2025, if you strip out healthcare, the U.S. economy net lost jobs. That&rsquo;s the definition of a recession, just not one any official body called.
                In 2026, we&rsquo;re actively shedding jobs &mdash; and now it&rsquo;s visible even in the headline numbers.
                The AI displacement didn&rsquo;t start this. But it turned a slow leak into a flood.
            </div>
            <p class="jobs-sub">The U.S. added 181,000 net new jobs in all of 2025 &mdash; the worst non-recession year since 2003. Healthcare alone added 713,000. <strong style="color:#aaa;">Strip out healthcare, and the rest of the American economy net lost jobs.</strong> So when someone says &ldquo;AI will create new jobs&rdquo; &mdash; we actually know what those jobs are. They&rsquo;re nursing jobs.</p>
            <div class="jobs-grid">
                <div class="jobs-gaining">
                    <h3>&#9650; Gaining</h3>
                    <div class="jobs-row">
                        <span class="jobs-row-label">Healthcare &amp; Social Assistance</span>
                        <span class="jobs-row-val val-green">+713,000</span>
                    </div>
                    <div class="jobs-row">
                        <span class="jobs-row-label">Government</span>
                        <span class="jobs-row-val val-grey">+some</span>
                    </div>
                    <div class="jobs-row">
                        <span class="jobs-row-label">Leisure &amp; Hospitality</span>
                        <span class="jobs-row-val val-grey">marginal</span>
                    </div>
                </div>
                <div class="jobs-losing">
                    <h3>&#9660; Losing</h3>
                    <div class="jobs-row">
                        <span class="jobs-row-label">Tech / Information sector</span>
                        <span class="jobs-row-val val-red">&minus;342,000 from peak</span>
                    </div>
                    <div class="jobs-row">
                        <span class="jobs-row-label">Professional &amp; Business Services</span>
                        <span class="jobs-row-val val-red">net losses</span>
                    </div>
                    <div class="jobs-row">
                        <span class="jobs-row-label">Federal Government (DOGE)</span>
                        <span class="jobs-row-val val-red">&minus;277,000</span>
                    </div>
                    <div class="jobs-row">
                        <span class="jobs-row-label">Manufacturing</span>
                        <span class="jobs-row-val val-red">8+ months declining</span>
                    </div>
                    <div class="jobs-row">
                        <span class="jobs-row-label">Finance &amp; Admin Support</span>
                        <span class="jobs-row-val val-red">net losses</span>
                    </div>
                </div>
            </div>
            <div class="jobs-callout">
                <strong>&ldquo;In many ways, 2025 was both a white-collar and a blue-collar jobs recession.&rdquo;</strong> &mdash; Heather Long, economist, Fortune / BLS
                <br><br>
                The counterargument to AI displacement has always been: <em>&ldquo;new technology creates new jobs.&rdquo;</em>
                That&rsquo;s true. We know exactly what those jobs are.
                They&rsquo;re bedpan jobs. Nursing assistant jobs. Home health aide jobs.
                Jobs that exist because America is aging &mdash; not because AI opened a new frontier of human creativity.
                The white-collar career ladder &mdash; the one a college degree was supposed to unlock &mdash; is being sawed off from the bottom up.
                <a href="https://fortune.com/2026/01/09/jobs-report-december-health-care-federal-reserve/" target="_blank" rel="noopener" style="color:#444;font-size:0.72rem">&nbsp; Source: Fortune / BLS &rarr;</a>
            </div>
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:0.75rem;margin-top:0.75rem;">
                <div style="padding:1rem;background:#0d0d0d;border:1px solid #1a1a1a;border-radius:8px;text-align:center;">
                    <div style="font-size:1.8rem;font-weight:800;color:#ff6644;font-variant-numeric:tabular-nums;">4.4%</div>
                    <div style="font-size:0.72rem;color:#555;margin-top:0.25rem;line-height:1.5;">unemployment rate, Dec 2025<br><span style="color:#444">up from 4.0% in Jan 2025</span></div>
                </div>
                <div style="padding:1rem;background:#0d0d0d;border:1px solid #1a1a1a;border-radius:8px;text-align:center;">
                    <div style="font-size:1.8rem;font-weight:800;color:#ff6644;font-variant-numeric:tabular-nums;">+583K</div>
                    <div style="font-size:0.72rem;color:#555;margin-top:0.25rem;line-height:1.5;">more unemployed than<br>a year prior (Dec 2025)</div>
                </div>
                <div style="padding:1rem;background:#0d0d0d;border:1px solid #1a1a1a;border-radius:8px;text-align:center;">
                    <div style="font-size:1.8rem;font-weight:800;color:#ff6644;">&#8679;</div>
                    <div style="font-size:0.72rem;color:#555;margin-top:0.25rem;line-height:1.5;">long-term unemployment &amp;<br>involuntary part-time climbing</div>
                </div>
            </div>
            <div style="margin-top:0.75rem;padding:0.9rem 1.1rem;border-left:3px solid #2a1800;background:#0d0d0d;border-radius:0 6px 6px 0;font-size:0.82rem;color:#777;font-style:italic;line-height:1.7;">
                &ldquo;It&rsquo;s a slowly weakening job picture. Whatever metric you want to focus on, that story shows up.&rdquo;
                <span style="display:block;margin-top:0.3rem;font-size:0.72rem;font-style:normal;color:#555;">&mdash; Heather Long, economist</span>
            </div>
            <details style="margin-top:1rem;">
                <summary style="cursor:pointer;font-size:0.78rem;color:#555;padding:0.6rem 0;list-style:none;display:flex;align-items:center;gap:0.4rem;">
                    <span style="color:#333;font-size:0.65rem;">&#9654;</span>
                    Why the &ldquo;low unemployment&rdquo; argument doesn&rsquo;t hold up
                </summary>
                <div style="margin-top:0.75rem;padding:1rem;background:#0d0d0d;border:1px solid #1a1a1a;border-radius:8px;font-size:0.78rem;color:#666;line-height:1.9;">
                    <p style="margin-bottom:0.75rem;color:#888;font-weight:600;">The headline unemployment rate (U-3) only counts people who looked for work in the last 4 weeks and couldn&rsquo;t find it. It misses everyone else.</p>
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.5rem;margin-bottom:0.75rem;">
                        <div style="padding:0.6rem;background:#111;border-radius:6px;">
                            <div style="color:#ff6644;font-weight:700;font-size:0.82rem;">U-3: 4.4%</div>
                            <div style="color:#555;font-size:0.7rem;margin-top:0.2rem;">The number you see in headlines. Only counts active job seekers.</div>
                        </div>
                        <div style="padding:0.6rem;background:#111;border-radius:6px;">
                            <div style="color:#ff6644;font-weight:700;font-size:0.82rem;">U-6: ~8%+</div>
                            <div style="color:#555;font-size:0.7rem;margin-top:0.2rem;">Includes part-timers who want full-time work + marginally attached workers.</div>
                        </div>
                        <div style="padding:0.6rem;background:#111;border-radius:6px;">
                            <div style="color:#ff6644;font-weight:700;font-size:0.82rem;">Discouraged workers</div>
                            <div style="color:#555;font-size:0.7rem;margin-top:0.2rem;">People who stopped looking entirely &mdash; not counted as unemployed at all.</div>
                        </div>
                        <div style="padding:0.6rem;background:#111;border-radius:6px;">
                            <div style="color:#ff6644;font-weight:700;font-size:0.82rem;">Labor force participation</div>
                            <div style="color:#555;font-size:0.7rem;margin-top:0.2rem;">Still below pre-2020 levels. Millions have exited the labor force entirely.</div>
                        </div>
                    </div>
                    <p style="margin-bottom:0.75rem;">When AI eliminates a role through attrition &mdash; the position just isn&rsquo;t posted when someone leaves &mdash; no one becomes &ldquo;unemployed.&rdquo; The headcount shrinks. The work disappears. The unemployment rate doesn&rsquo;t move. That&rsquo;s the measurement gap. The economy can shed millions of white-collar roles without the headline number flinching, right up until it does &mdash; all at once.</p>
                    <p style="padding:0.75rem;background:#1a1000;border:1px solid #2a1800;border-radius:6px;color:#888;">
                        <strong style="color:#ff8844;">The immigration factor:</strong> The administration&rsquo;s crackdown has also artificially shrunk the labor supply &mdash; fewer people in the pool means the unemployment rate stays low even as private-sector hiring collapses. Fewer workers looking = lower U-3 rate, by definition. The &ldquo;jobless boom&rdquo; is partly a statistical artifact of a smaller denominator.
                    </p>
                </div>
            </details>
        </section>

        <section class="voices-section">
            <h2>They All See It</h2>
            <p class="voices-sub">World leaders, economists, and the people building it &mdash; all saying the same thing.</p>
            <div class="voice-row yang">
                <p class="voice-quote">&ldquo;We are in the third inning of a vast economic shift that is going to leave millions of Americans behind.&rdquo;</p>
                <p class="voice-attr"><strong>Andrew Yang</strong> &mdash; 2018 presidential campaign &nbsp;&middot;&nbsp; <em style="color:#888">He was right.</em></p>
            </div>
            <div class="voice-row papal">
                <p class="voice-quote">&ldquo;We would condemn humanity to a future without hope if we took away people&rsquo;s ability to make decisions about themselves and their lives by dooming them to depend on the choices of machines.&rdquo;</p>
                <p class="voice-attr"><strong>Pope Francis</strong> &mdash; G7 Summit, June 14, 2024 &nbsp;&middot;&nbsp; <em style="color:#555">his last G7 before his death on April 21, 2025</em></p>
            </div>
            <div class="voice-row papal">
                <p class="voice-quote">&ldquo;The pursuit of greater profits cannot justify choices that systematically sacrifice jobs, because the human person is an end, not a means.&rdquo;</p>
                <p class="voice-attr"><strong>Pope Leo XIV</strong> &mdash; <em>Magnifica Humanitas</em>, May 25, 2026 &nbsp;&middot;&nbsp; <em style="color:#555">the new pope&rsquo;s first encyclical &mdash; entirely about AI</em></p>
            </div>
            <div class="voice-row">
                <p class="voice-quote">&ldquo;Within the next one to five years, AI could handle tasks that represent 50% of entry-level white-collar work. The societal effects could be severe.&rdquo;</p>
                <p class="voice-attr"><strong>Dario Amodei</strong> &mdash; CEO, Anthropic &nbsp;&middot;&nbsp; 2025</p>
            </div>
        </section>

        <section class="evisceration-section" id="white-collar">
            <h2>The Invisible Flood: White-Collar Evisceration</h2>
            <p class="evis-sub">The numbers above only capture public layoff announcements. The quiet displacement &mdash; attrition, contracts not renewed, roles automated away &mdash; never makes the news.</p>
            <div class="evis-grid">
                <div class="evis-stat">
                    <div class="evis-stat-value">30%</div>
                    <div class="evis-stat-label">of 2025 college graduates found a full-time job in their field &mdash; down from 41% in 2024. An 11-point collapse in a single year. <span style="color:#555">(Cengage Group)</span></div>
                </div>
                <div class="evis-stat">
                    <div class="evis-stat-value">1 in 3</div>
                    <div class="evis-stat-label">of 2025 graduates are unemployed and actively searching. The degree did not open the door. <span style="color:#555">(Cengage Group, 2025)</span></div>
                </div>
                <div class="evis-stat">
                    <div class="evis-stat-value">42%</div>
                    <div class="evis-stat-label">of recent college graduates are working jobs that don&apos;t require their degree &mdash; near an all-time high. <span style="color:#555">(Federal Reserve Bank of NY, Q4 2025)</span></div>
                </div>
                <div class="evis-stat">
                    <div class="evis-stat-value">5.8%</div>
                    <div class="evis-stat-label">unemployment rate for recent college graduates &mdash; one of the worst in a decade. Overall college-educated rate: 3.1%. <span style="color:#555">(BLS / NY Fed, Q1 2026)</span></div>
                </div>
                <div class="evis-stat">
                    <div class="evis-stat-value">16%</div>
                    <div class="evis-stat-label">relative employment decline for workers ages 22&ndash;25 in AI-exposed occupations (2022&ndash;2025)</div>
                </div>
                <div class="evis-stat">
                    <div class="evis-stat-value">50%</div>
                    <div class="evis-stat-label">of entry-level white-collar jobs projected eliminated &mdash; Dario Amodei, CEO of Anthropic</div>
                </div>
            </div>
            <div class="evis-quote">
                <p>&ldquo;Within the next one to five years, AI could handle tasks that represent 50% of entry-level white-collar work. The societal effects could be severe.&rdquo;</p>
                <cite>&mdash; Dario Amodei, CEO of Anthropic (2025)</cite>
            </div>
            <p style="margin-top:0.85rem;font-size:0.76rem;color:#444;line-height:1.7;">
                The class of 2025 entered the worst entry-level job market in a decade. The class of 2024 wasn&apos;t much better: only 55% had full-time work within six months of graduation (NACE). The promise of the college degree &mdash; work hard, graduate, get a career &mdash; is colliding with an economy where AI is absorbing entry-level tasks faster than employers are creating new roles.
            </p>
        </section>

        <section class="cta-section">
            <div class="cta-inner">
                <p class="cta-pre">The data is in. The flood is real.</p>
                <h2 class="cta-headline">We don&apos;t have to argue about whether AI is taking jobs.<br>We can prove it. Now what?</h2>
                <p class="cta-body">
                    The question is no longer <em>if</em> — it&apos;s <em>what next.</em><br>
                    We believe the answer is redesigning work for human flourishing:<br>
                    not fighting the wave, but learning to navigate it.
                </p>
                <p class="cta-mission">
                    <strong>Eudy&apos;s mission:</strong> Standardize work for human flourishing in the age of AI.
                </p>
                <div class="cta-actions">
                    <a href="https://www.instagram.com/muhan.being/" target="_blank" rel="noopener" class="cta-btn cta-primary">Follow the journey &rarr;</a>
                    <a href="https://eudy.co" target="_blank" rel="noopener" class="cta-btn cta-secondary">Learn about Eudy</a>
                </div>
            </div>
        </section>

        <section class="recent">
            <h2>Events</h2>
            <div class="controls">
                <div class="controls-group">
                    <button class="ctrl-btn active" onclick="setSort('date')">Most Recent</button>
                    <button class="ctrl-btn" onclick="setSort('headcount')">Largest</button>
                </div>
                <div class="ctrl-divider"></div>
                <div class="controls-group">
                    <button class="ctrl-btn active" data-filter="all" onclick="setFilter('all')">All</button>
                    <button class="ctrl-btn" data-filter="confirmed" onclick="setFilter('confirmed')">Confirmed</button>
                    <button class="ctrl-btn" data-filter="likely" onclick="setFilter('likely')">Likely</button>
                </div>
                <div class="ctrl-divider"></div>
                <input class="search-input" type="text" placeholder="Search company..." oninput="setSearch(this.value)">
                <span class="row-count" id="row-count"></span>
            </div>
            <div class="table-wrap">
                <table>
                    <thead>
                        <tr>
                            <th>Date</th>
                            <th>Company</th>
                            <th>Headcount</th>
                            <th>Attribution</th>
                            <th>Source</th>
                        </tr>
                    </thead>
                    <tbody id="events-tbody"></tbody>
                </table>
            </div>
        </section>
        
        <section class="submit-section">
            <h2>Did we miss one?</h2>
            <p>Heard about a layoff we haven&apos;t tracked? Is your company about to cut jobs because of AI? Give us an early warning &mdash; submit it here. Every verified entry goes live within 24 hours. Or email us directly at <a href="mailto:hello@eudy.co">hello@eudy.co</a>.</p>
            <form id="submit-form">
                <div class="form-row">
                    <input type="text" name="company" placeholder="Company name *" required>
                    <input type="number" name="headcount" placeholder="Headcount *" min="1" required>
                    <input type="date" name="date" required>
                </div>
                <div class="form-row">
                    <input type="url" name="source" placeholder="Source URL *" required>
                </div>
                <div class="form-row">
                    <input type="text" name="notes" placeholder="Notes (optional — quote from company, context, etc.)">
                </div>
                <div class="form-row">
                    <input type="email" name="email" placeholder="Your email (optional — get notified as the flood rises)">
                </div>
                <button type="submit" class="submit-btn">Submit &rarr;</button>
            </form>
            <div class="submit-success" id="submit-success">
                <h3>Thanks &mdash; we&apos;ll verify it.</h3>
                <p>Verified submissions go live within 24 hours. While you wait &mdash; follow the mission.</p>
                <div class="follow-cta">
                    <a href="https://www.instagram.com/muhan.being/" target="_blank" rel="noopener" class="follow-btn instagram">Follow @muhan.being on Instagram</a>
                </div>
                <p style="margin-top:1rem;font-size:0.78rem;color:#555;">
                    <strong style="color:#666">Also coming soon:</strong> Armada Bridge &mdash; the AI transformation platform we&apos;re building to help teams navigate this shift.
                    If you&apos;re a company navigating AI-driven workforce changes, <a href="mailto:hello@eudy.co">reach out to Eudy &rarr;</a>
                </p>
            </div>
        </section>

        <section class="methodology" id="methodology">
            <h3>Methodology</h3>
            <p>
                <strong>confirmed</strong> = Company explicitly stated AI/automation as the reason for layoffs<br>
                <strong>likely</strong> = Company investing heavily in AI while cutting jobs, or media analysis attributes cuts to AI<br>
                <strong>unclear</strong> = Tech company layoffs that may be related to AI transformation but not explicitly stated
            </p>
            <p style="margin-top: 0.8rem;">
                This page is updated daily. US data calibrated monthly using the Challenger, Gray &amp; Christmas report.
                Last updated: {last_updated[:10]} &middot; Challenger cumulative AI cuts (US only): {challenger_total:,}
            </p>
            <p style="margin-top: 0.8rem; color: #555;">
                <strong style="color:#666">Why the real number is much higher:</strong>
                Our tracker captures only public announcements. The majority of AI displacement happens invisibly &mdash;
                through attrition, contract non-renewals, and quiet eliminations never reported in the press.
                Our {total_estimated:,} tracks what companies disclosed. The real number is far larger.
            </p>
            <p style="margin-top:0.5rem;font-size:0.78rem;color:#444;">
                Sources: <a href="https://www.challengergray.com/blog/2025-year-end-challenger-report-highest-q4-layoffs-since-2008-lowest-ytd-hiring-since-2010/" target="_blank" rel="noopener">Challenger, Gray &amp; Christmas</a> &middot;
                <a href="https://layoffs.fyi" target="_blank" rel="noopener">Layoffs.fyi</a> &middot;
                <a href="https://trueup.io/layoffs" target="_blank" rel="noopener">TrueUp.io</a> &middot;
                Public news reports
            </p>
        </section>

        <footer>
            <p>Updated daily &middot;
               <a href="https://github.com/muhanz/ai-layoff-tracker">GitHub source &amp; full dataset</a> &middot;
               <a href="https://www.instagram.com/muhan.being/" target="_blank" rel="noopener">@muhan.being</a></p>
            <p>Data is for informational purposes only. Not investment or employment advice.</p>
            <p style="margin-top:0.3rem;font-size:0.75rem;color:#777;">Source links are checked daily. A ⚠ "last live" date means the article was reachable then but has since moved or been removed — that's the internet, not us. All sources are also archived via the Wayback Machine (📦) for permanent access.</p>
        </footer>
    </main>
    <script>
        const ALL_EVENTS = {all_events_json};
        let currentSort = 'date';
        let currentFilter = 'all';
        let currentSearch = '';

        function setSort(s) {{
            currentSort = s;
            document.querySelectorAll('.controls-group:first-child .ctrl-btn').forEach(b => b.classList.remove('active'));
            event.target.classList.add('active');
            renderTable();
        }}
        function setFilter(f) {{
            currentFilter = f;
            document.querySelectorAll('[data-filter]').forEach(b => b.classList.remove('active'));
            document.querySelector('[data-filter="' + f + '"]').classList.add('active');
            renderTable();
        }}
        function setSearch(v) {{
            currentSearch = v.toLowerCase();
            renderTable();
        }}

        function renderTable() {{
            let events = ALL_EVENTS.slice();
            if (currentFilter !== 'all') events = events.filter(e => e.ai_attributed === currentFilter);
            if (currentSearch) events = events.filter(e => e.company.toLowerCase().includes(currentSearch));
            if (currentSort === 'date') events.sort((a, b) => b.date.localeCompare(a.date));
            if (currentSort === 'headcount') events.sort((a, b) => b.headcount - a.headcount);

            const badgeMap = {{ confirmed: 'badge-confirmed', likely: 'badge-likely', unclear: 'badge-unclear' }};
            let html = '';
            events.forEach(e => {{
                const srcs = (e.source_urls || []).filter(u => u);
                const ls = e.link_status || {{}};
                const srcLinks = srcs.map(u => {{
                    const st = ls[u] || {{}};
                    const dead = st.alive === false;
                    const lastAlive = (dead && st.last_alive)
                        ? ` <span style="color:#888;font-size:0.7rem" title="Link may be unavailable">⚠ last live: ${{st.last_alive}}</span>`
                        : '';
                    return `<a href="${{u}}" target="_blank" rel="noopener"${{dead ? ' style="color:#999"' : ''}}>source</a>${{lastAlive}} <a href="https://web.archive.org/web/${{u}}" target="_blank" rel="noopener" style="color:#555;font-size:0.7rem" title="Wayback Machine">📦</a>`;
                }}).join(' &nbsp;');
                const rowId = `row-${{e.company.replace(/\W/g,'').toLowerCase()}}-${{e.date}}`;
                html += `<tr class="event-row" onclick="toggleDetail('${{rowId}}')" style="cursor:pointer">
                    <td class="date-col">${{e.date}}</td>
                    <td class="company-col">${{e.company}}<span class="expand-hint">&#9654;</span></td>
                    <td class="number-col">${{e.headcount > 0 ? e.headcount.toLocaleString() : 'N/A'}}</td>
                    <td><span class="badge ${{badgeMap[e.ai_attributed] || 'badge-unclear'}}">${{e.ai_attributed}}</span></td>
                    <td>${{srcs.length ? srcLinks : '—'}}</td>
                </tr>
                <tr class="event-detail" id="${{rowId}}" style="display:none">
                    <td colspan="5" class="detail-cell">
                        ${{e.note ? `<p class="detail-note">${{e.note}}</p>` : ''}}
                        ${{srcs.length > 1 ? `<p class="detail-sources">All sources: ${{srcs.map(u => `<a href="${{u}}" target="_blank" rel="noopener">${{u.replace(/https?:\/\/(www\.)?/,'').slice(0,60)}}</a>`).join(' · ')}}</p>` : ''}}
                    </td>
                </tr>`;
            }});
            document.getElementById('events-tbody').innerHTML = html || '<tr><td colspan="5" style="color:#555;text-align:center;padding:2rem">No results</td></tr>';
            document.getElementById('row-count').textContent = events.length + ' events';
        }}

        function toggleDetail(id) {{
            const row = document.getElementById(id);
            if (!row) return;
            const isHidden = row.style.display === 'none';
            row.style.display = isHidden ? 'table-row' : 'none';
            const trigger = row.previousElementSibling;
            if (trigger) trigger.classList.toggle('expanded', isHidden);
        }}

        // Live counter — ticks up in real time based on avg daily rate
        (function() {{
            const BASE = {total_estimated};
            const BASE_CONFIRMED = {total_confirmed};
            const BASE_TS = new Date('{last_updated}').getTime();
            const PER_DAY = {avg_per_day};
            const PER_MS = PER_DAY / 86400000;
            const CONFIRMED_RATIO = BASE_CONFIRMED / BASE;
            let lastFloor = BASE;
            function fmt(n) {{ return Math.floor(n).toLocaleString('en-US'); }}
            function tick() {{
                const elapsed = Date.now() - BASE_TS;
                const current = BASE + elapsed * PER_MS;
                const currentFloor = Math.floor(current);
                ['live-counter','dd-counter'].forEach(id => {{
                    const el = document.getElementById(id);
                    if (el) el.textContent = fmt(current);
                }});
                const el2 = document.getElementById('live-confirmed');
                if (el2) el2.textContent = fmt(current * CONFIRMED_RATIO);
                const rate = document.getElementById('dd-rate');
                if (rate) rate.textContent = '~' + PER_DAY.toLocaleString() + ' per day';
                // Flash the doomsday counter when integer increments
                if (currentFloor > lastFloor) {{
                    const dd = document.getElementById('dd-counter');
                    if (dd) {{
                        dd.classList.remove('dd-tick');
                        void dd.offsetWidth; // force reflow to restart animation
                        dd.classList.add('dd-tick');
                        setTimeout(() => dd.classList.remove('dd-tick'), 700);
                    }}
                    lastFloor = currentFloor;
                }}
            }}
            tick();
            setInterval(tick, 1000);
        }})();

        renderTable();

        document.getElementById('submit-form').addEventListener('submit', async (e) => {{
            e.preventDefault();
            const btn = e.target.querySelector('.submit-btn');
            btn.disabled = true;
            btn.textContent = 'Submitting...';
            try {{
                const res = await fetch('/api/submit', {{
                    method: 'POST',
                    body: new FormData(e.target)
                }});
                if (res.ok) {{
                    e.target.style.display = 'none';
                    document.getElementById('submit-success').style.display = 'block';
                }} else {{
                    throw new Error('Server error');
                }}
            }} catch {{
                btn.disabled = false;
                btn.textContent = 'Submit →';
                alert('Something went wrong. Please try again.');
            }}
        }});
    </script>
</body>
</html>"""
    
    os.makedirs("public", exist_ok=True)
    
    with open("public/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"Page generated: public/index.html")
    print(f"  Numbers: {total_estimated:,} (broad) / {total_confirmed:,} (conservative)")


if __name__ == "__main__":
    generate_html()
