#!/usr/bin/env python3
"""
Submit all source URLs to the Wayback Machine save API.
Run this once now, then optionally add to GitHub Actions for new events.
"""
import json
import time
import urllib.request
import urllib.error

with open("data/events.json", "r") as f:
    db = json.load(f)

urls = set()
for event in db["events"]:
    for url in event.get("source_urls", []):
        if url:
            urls.add(url)

print(f"Archiving {len(urls)} URLs to Wayback Machine...\n")

success, failed = [], []
for url in sorted(urls):
    try:
        req = urllib.request.Request(
            f"https://web.archive.org/save/{url}",
            headers={"User-Agent": "Mozilla/5.0 (archive-bot)"}
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            location = resp.url
            print(f"✅ {url[:70]}")
            success.append(url)
    except Exception as e:
        print(f"⚠️  {url[:70]} — {e}")
        failed.append(url)
    time.sleep(2)

print(f"\nDone. {len(success)} archived, {len(failed)} failed.")
