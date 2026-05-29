#!/usr/bin/env python3
"""Regenerate public/og-image.png with current totals from data/events.json."""

import asyncio
import json
from datetime import date
from pathlib import Path


GPT4_LAUNCH = date(2023, 3, 14)


def build_html(total: int, days: int) -> str:
    formatted = f"{total:,}"
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800;900&display=swap');
*{{margin:0;padding:0;box-sizing:border-box}}
body{{
  width:1200px;height:630px;
  background:#0a0a0a;
  font-family:'Inter','Ubuntu','DejaVu Sans',sans-serif;
  display:flex;flex-direction:column;justify-content:center;
  padding:60px 80px;overflow:hidden;
}}
.label{{font-size:15px;font-weight:700;letter-spacing:.15em;text-transform:uppercase;color:#444;margin-bottom:16px}}
.dot{{display:inline-block;width:8px;height:8px;background:#ef4444;border-radius:50%;margin-right:8px;vertical-align:middle}}
.number{{font-size:118px;font-weight:900;color:#ef4444;line-height:1;letter-spacing:-.02em;margin-bottom:20px}}
.headline{{font-size:28px;font-weight:700;color:#fff;line-height:1.3;margin-bottom:14px}}
.sub{{font-size:17px;color:#555;line-height:1.5}}
.domain{{position:absolute;bottom:40px;right:80px;font-size:13px;color:#2a2a2a;letter-spacing:.05em}}
</style>
</head>
<body>
<div class="label"><span class="dot"></span>AI Layoff Tracker &nbsp;&middot;&nbsp; {days} days since GPT-4</div>
<div class="number">{formatted}</div>
<div class="headline">jobs directly attributed to AI</div>
<div class="sub">Behind the 2.9M total announced U.S. cuts — the iceberg is real. Updated daily.</div>
<div class="domain">layoffs.eudy.co</div>
</body>
</html>"""


async def generate():
    from playwright.async_api import async_playwright

    data = json.loads(Path("data/events.json").read_text())
    total = data["metadata"]["total_estimated"]
    days = (date.today() - GPT4_LAUNCH).days
    html = build_html(total, days)

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page(viewport={"width": 1200, "height": 630})
        await page.set_content(html, wait_until="networkidle")
        await page.screenshot(
            path="public/og-image.png",
            clip={"x": 0, "y": 0, "width": 1200, "height": 630},
        )
        await browser.close()

    print(f"og-image.png generated: total={total:,}, days={days}")


if __name__ == "__main__":
    asyncio.run(generate())
