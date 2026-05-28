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
    
    recent_html = ""
    for e in recent_events:
        badge_class = {
            "confirmed": "badge-confirmed",
            "likely": "badge-likely",
            "unclear": "badge-unclear"
        }.get(e["ai_attributed"], "badge-unclear")
        
        source_link = ""
        if e.get("source_urls") and e["source_urls"][0]:
            source_link = f'<a href="{e["source_urls"][0]}" target="_blank" rel="noopener">source</a>'
        
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
    <meta name="description" content="Tracking global job losses attributed to AI since the launch of GPT-4. Updated daily with verified sources.">
    <meta property="og:title" content="AI Layoff Tracker - Global Warning">
    <meta property="og:description" content="Since GPT-4 launched {days_since} days ago, {total_estimated:,} people have lost their jobs in AI-related layoffs.">
    <meta property="og:type" content="website">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="AI Layoff Tracker - {total_estimated:,} jobs lost">
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
            <h1>&#9888;&#65039; AI Layoff Warning</h1>
            <p class="subtitle">Global tracking since GPT-4 launch (March 14, 2023)</p>
        </header>
        
        <section class="counter">
            <div class="number">{total_estimated:,}</div>
            <p class="label">people lost jobs in AI-related layoffs (broad estimate)</p>
            
            <div class="number secondary">{total_confirmed:,}</div>
            <p class="label">people explicitly laid off due to AI (conservative estimate)</p>
            
            <div class="days-counter">
                {days_since} days &middot; {event_count} events &middot; 
                ~{avg_per_day:,} people per day
            </div>
        </section>
        
        <section class="meta">
            <p>Last updated: {last_updated[:10]} &middot; 
               Challenger Report cumulative (US only): {challenger_total:,}</p>
            <p class="sources">
                Sources: Challenger, Gray &amp; Christmas &middot; Layoffs.fyi &middot; 
                TrueUp.io &middot; Public news reports
            </p>
        </section>
        
        <section class="recent">
            <h2>Recent Events</h2>
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Company</th>
                        <th>Headcount</th>
                        <th>AI Attribution</th>
                        <th>Source</th>
                    </tr>
                </thead>
                <tbody>{recent_html}
                </tbody>
            </table>
        </section>
        
        <section class="methodology">
            <h3>Methodology</h3>
            <p>
                <strong>confirmed</strong> = Company explicitly stated AI/automation as the reason for layoffs<br>
                <strong>likely</strong> = Company investing heavily in AI while cutting jobs, or media analysis attributes cuts to AI<br>
                <strong>unclear</strong> = Tech company layoffs that may be related to AI transformation but not explicitly stated
            </p>
            <p style="margin-top: 0.8rem;">
                This page is updated daily via automated scripts. US data is calibrated monthly using 
                the official Challenger, Gray &amp; Christmas report. Global data is aggregated from multiple 
                public sources. Due to differences in methodology, numbers may differ from any single source.
            </p>
        </section>
        
        <footer>
            <p>Updated daily &middot; 
               <a href="https://github.com/muhanz/ai-layoff-tracker">GitHub source &amp; full dataset</a></p>
            <p>Data is for informational purposes only. Not investment or employment advice.</p>
        </footer>
    </main>
</body>
</html>"""
    
    os.makedirs("public", exist_ok=True)
    
    with open("public/index.html", "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"Page generated: public/index.html")
    print(f"  Numbers: {total_estimated:,} (broad) / {total_confirmed:,} (conservative)")


if __name__ == "__main__":
    generate_html()
