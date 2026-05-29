import json
import os
import requests
from datetime import datetime, timezone

DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'events.json')
TIMEOUT = 10
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; AI-Layoff-Tracker/1.0; link-check)'}


def check_url(url):
    try:
        r = requests.head(url, timeout=TIMEOUT, headers=HEADERS, allow_redirects=True)
        if r.status_code < 400:
            return True
        # Some servers reject HEAD — fall back to GET
        r = requests.get(url, timeout=TIMEOUT, headers=HEADERS, stream=True)
        return r.status_code < 400
    except Exception:
        return False


def main():
    with open(DATA_FILE) as f:
        data = json.load(f)

    today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
    changed = False

    for event in data.get('events', []):
        for url in event.get('source_urls', []):
            if not url:
                continue

            link_status = event.setdefault('link_status', {})
            existing = link_status.get(url, {})

            alive = check_url(url)
            entry = {'alive': alive, 'last_checked': today}

            if alive:
                entry['last_alive'] = today
            elif existing.get('last_alive'):
                entry['last_alive'] = existing['last_alive']

            if link_status.get(url) != entry:
                link_status[url] = entry
                changed = True

            print(f"  {'✓' if alive else '✗'} {url}")

    if changed:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("Updated events.json with link statuses.")
    else:
        print("No link status changes.")


if __name__ == '__main__':
    main()
