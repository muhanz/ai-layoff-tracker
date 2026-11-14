#!/usr/bin/env python3
"""
Data-series refresh - AI Layoff Tracker
========================================
Keeps the facts that come straight from a government data series current,
with no model involved. Each one is re-read from the published series and
written back to data/facts.json with its new period.

Only the facts listed in SERIES are touched. Everything that comes from a
report (Challenger, the New York Fed, McKinsey, Goldman, WEF, construction
spending, capex guidance) is left alone: those need a person or the weekly
report check to read the new edition.

Guards:
  - A series that cannot be read is skipped. Its fact keeps its old value.
  - A value that moves further than its limit in one refresh is not written.
    It is printed as HELD so someone looks at it first.
  - A fact whose value and period are unchanged is not rewritten.

Run with --check to print what would change without writing.
"""

import json
import sys
import urllib.request
from datetime import datetime, timezone

from k_gauge import fetch as fetch_fred

FACTS_FILE = "data/facts.json"
BLS_API = "https://api.bls.gov/publicAPI/v1/timeseries/data/{id}"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fetch_bls(series_id):
    """Monthly values for one BLS series, oldest first, as (YYYY-MM-01, value)."""
    req = urllib.request.Request(BLS_API.format(id=series_id), headers={"User-Agent": "curl/8.7.1", "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        body = json.load(resp)
    if body.get("status") != "REQUEST_SUCCEEDED":
        raise ValueError(f"{series_id}: {body.get('message')}")
    rows = []
    for item in body["Results"]["series"][0]["data"]:
        if item["period"].startswith("M") and item["period"] != "M13":
            try:  # BLS publishes "-" for a month it did not collect
                rows.append((f"{item['year']}-{item['period'][1:]}-01", float(item["value"])))
            except ValueError:
                continue
    if not rows:
        raise ValueError(f"{series_id}: no monthly data")
    return sorted(rows)


def month(date):
    d = datetime.strptime(date, "%Y-%m-%d")
    return f"{MONTHS[d.month - 1]} {d.year}"


def at(series, date):
    for d, v in series:
        if d == date:
            return v
    raise ValueError(f"no reading for {date}")


def minus(text):
    return text.replace("-", "&minus;")


# ---- one function per fact: returns the fields to write ----------------------

def latest_rate(series_id, source=fetch_fred):
    def build(_facts):
        date, value = source(series_id)[-1]
        return {"value": f"{value:.1f}%", "period": month(date), "number": round(value, 1)}
    return build


def prime_men_out(_facts):
    date, rate = fetch_bls("LNS11300061")[-1]
    out = round(100 - rate, 1)
    return {
        "value": f"{out:.1f}%",
        "period": month(date),
        "number": out,
        "note": f"100 minus the {rate:.1f}% participation rate of men aged 25 to 54",
    }


def insurance_jobs(_facts):
    date, thousands = fetch_fred("CES5552400001")[-1]
    return {
        "value": f"{thousands / 1000:.1f}M",
        "period": month(date),
        "number": round(thousands * 1000),
        "note": f"{thousands * 1000:,.0f}, preliminary",
    }


def business_applications(_facts):
    series = fetch_fred("BABATOTALSAUS")
    date, value = series[-1]
    avg_2019 = sum(v for d, v in series if d.startswith("2019")) / 12
    rounded = round(value / 10000) * 10000
    return {
        "value": f"about {rounded:,.0f}",
        "period": month(date),
        "number": round(value),
        "note": f"{value:,.0f}; 2019 average {avg_2019:,.0f} ({(value / avg_2019 - 1) * 100:+.0f}%)",
    }


def december_change(series_id, year):
    series = fetch_fred(series_id)
    return at(series, f"{year}-12-01") - at(series, f"{year - 1}-12-01")  # thousands of jobs


def jobs_year(series_id, year):
    def build(_facts):
        change = december_change(series_id, year)
        return {"value": minus(f"{round(change) * 1000:,.0f}"), "number": round(change * 1000)}
    return build


def jobs_ex_health(year):
    def build(_facts):
        total = december_change("PAYEMS", year)
        health = december_change("CES6562000101", year)
        rest = round(total) - round(health)
        return {
            "value": minus(f"{rest * 1000:,.0f}"),
            "number": rest * 1000,
            "note": f"{round(total) * 1000:,.0f} total minus {health * 1000:,.0f} in health care",
        }
    return build


# fact key -> (builder, the furthest "number" may move in one refresh, label)
SERIES = {
    "u3": (latest_rate("UNRATE"), 1.5, "BLS unemployment rate (UNRATE)"),
    "u6": (latest_rate("U6RATE"), 2.5, "BLS U-6 (U6RATE)"),
    "lfpr": (latest_rate("CIVPART"), 1.0, "BLS participation rate (CIVPART)"),
    "prime_men_out": (prime_men_out, 1.0, "BLS LNS11300061"),
    "insurance_jobs": (insurance_jobs, 150_000, "BLS CES5552400001"),
    "bfs_apps": (business_applications, 150_000, "Census BABATOTALSAUS"),
    "jobs_2025": (jobs_year("PAYEMS", 2025), 400_000, "BLS PAYEMS, Dec to Dec"),
    "health_2025": (jobs_year("CES6562000101", 2025), 150_000, "BLS CES6562000101, Dec to Dec"),
    "health_social_2025": (jobs_year("CES6562000001", 2025), 200_000, "BLS CES6562000001, Dec to Dec"),
    "jobs_ex_health_2025": (jobs_ex_health(2025), 400_000, "BLS PAYEMS minus health care"),
}


def old_number(fact):
    if isinstance(fact.get("number"), (int, float)):
        return fact["number"]
    text = fact.get("value", "").replace("&minus;", "-").replace(",", "").replace("about ", "")
    try:
        if text.endswith("%"):
            return float(text[:-1])
        if text.endswith("M"):
            return float(text[:-1]) * 1_000_000
        return float(text)
    except ValueError:
        return None


def refresh(facts, today):
    changed, held, skipped = [], [], []
    for key, (build, limit, label) in SERIES.items():
        fact = facts.get(key)
        if fact is None:
            continue
        try:
            new = build(facts)
        except Exception as exc:
            skipped.append(f"{key}: could not read {label} ({exc})")
            continue
        same_value = new["value"] == fact.get("value")
        same_period = new.get("period", fact.get("period")) == fact.get("period")
        if same_value and same_period:
            continue
        before = old_number(fact)
        if before is not None and abs(new["number"] - before) > limit:
            held.append(f"{key}: {fact.get('value')} -> {new['value']} moves more than the limit; not written")
            continue
        changed.append(f"{key}: {fact.get('value')} ({fact.get('period')}) -> {new['value']} ({new.get('period', fact.get('period'))})")
        if "number" in fact:
            fact["number"] = new["number"]
        for field in ("value", "period", "note"):
            if field in new:
                fact[field] = new[field]
        fact["checked"] = f"data series ({label}), refreshed automatically {today}"
    return changed, held, skipped


def main():
    check_only = "--check" in sys.argv
    with open(FACTS_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    changed, held, skipped = refresh(db["facts"], today)
    for line in changed:
        print("CHANGED", line)
    for line in held:
        print("HELD   ", line)
    for line in skipped:
        print("SKIPPED", line)
    if not (changed or held or skipped):
        print(f"All {len(SERIES)} data-series facts are current.")
    if changed and not check_only:
        db["as_of"] = today
        with open(FACTS_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
