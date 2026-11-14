#!/usr/bin/env python3
"""
K gauge - AI Layoff Tracker
===========================
One number for the thing the page is about: how far the K-shaped economy has
split into the people who own the gains and the people who work for a wage.

Six public series, all read straight from FRED (St. Louis Fed). Each is scored
from 0 (its best reading on record) to 100 (its worst reading on record). The
index is the plain average of the six. Nothing is weighted or modelled.

  Can you find work           U-6 underemployment
                              Unemployed people per job opening
                              Unemployment, ages 16 to 24
  Who gets the gains          Share of net worth held by the top 1%
                              Wages and salaries as a share of gross domestic income
  How people feel             University of Michigan consumer sentiment

100 would mean all six at their worst on record at the same time. It is a
scale, not a forecast, and the choice of six series is ours.

Writes data/k_gauge.json. If FRED cannot be reached the old file is kept.
"""

import csv
import io
import json
import sys
import time
import urllib.request
from datetime import datetime, timezone

OUT_FILE = "data/k_gauge.json"
FRED_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={id}"
FRED_PAGE = "https://fred.stlouisfed.org/series/{id}"
ARMS_START = 1990  # first full year of the Federal Reserve wealth-share series
HISTORY_START = "2001-01-01"  # first full year in which all six series exist

# key, group, label, FRED ids, worse_when, unit, decimals, source label
COMPONENTS = [
    ("u6", "work", "Underemployment (U-6)",
     "Unemployed, plus people who gave up looking for now, plus part-timers who want full-time work.",
     ["U6RATE"], "high", "%", 1, "BLS"),
    ("per_opening", "work", "Unemployed people per job opening",
     "Above 1.0 there are more people looking than jobs posted.",
     ["UNEMPLOY", "JTSJOL"], "high", "", 2, "BLS"),
    ("youth", "work", "Unemployment, ages 16 to 24",
     "The people trying to get on the first rung.",
     ["LNS14024887"], "high", "%", 1, "BLS"),
    ("top1", "gains", "Share of all net worth held by the top 1%",
     "Stocks and business equity sit here. So do the gains from AI so far.",
     ["WFRBST01134"], "high", "%", 1, "Federal Reserve"),
    ("wage_share", "gains", "Wages and salaries as a share of the economy's income",
     "The part of gross domestic income that is paid out as wages and salaries.",
     ["W270RE1A156NBEA"], "low", "%", 1, "BEA"),
    ("sentiment", "mood", "Consumer sentiment",
     "The University of Michigan survey of how households see their own finances and the economy.",
     ["UMCSENT"], "low", "", 1, "University of Michigan"),
]

GROUPS = {
    "work": "Can you find work",
    "gains": "Who gets the gains",
    "mood": "How people feel",
}


def fetch(series_id):
    req = urllib.request.Request(FRED_CSV.format(id=series_id), headers={"User-Agent": "curl/8.7.1", "Accept": "*/*"})  # FRED stalls other client names
    text = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                text = resp.read().decode("utf-8")
            break
        except Exception:
            if attempt == 3:
                raise
            time.sleep(2 * (attempt + 1))
    rows = []
    for row in list(csv.reader(io.StringIO(text)))[1:]:
        try:
            rows.append((row[0], float(row[1])))
        except (ValueError, IndexError):
            continue
    if len(rows) < 12:
        raise ValueError(f"{series_id}: unexpected response")
    return rows


def series_for(ids, raw):
    if len(ids) == 1:
        return raw[ids[0]]
    top, bottom = dict(raw[ids[0]]), dict(raw[ids[1]])
    return [(d, top[d] / bottom[d]) for d in sorted(bottom) if d in top and bottom[d]]


def score(value, best, worst):
    if worst == best:
        return 0.0
    return max(0.0, min(100.0, (value - best) / (worst - best) * 100))


def month_label(date):
    return datetime.strptime(date, "%Y-%m-%d").strftime("%b %Y")


def period_label(date, key):
    d = datetime.strptime(date, "%Y-%m-%d")
    if key == "wage_share":
        return str(d.year)
    if key == "top1":
        return f"Q{(d.month - 1) // 3 + 1} {d.year}"
    return d.strftime("%b %Y")


def build():
    raw = {}
    for _, _, _, _, ids, *_ in COMPONENTS:
        for series_id in ids:
            if series_id not in raw:
                raw[series_id] = fetch(series_id)

    components = []
    scored_series = {}
    for key, group, label, blurb, ids, worse_when, unit, decimals, source in COMPONENTS:
        series = series_for(ids, raw)
        lo = min(series, key=lambda x: x[1])
        hi = max(series, key=lambda x: x[1])
        best, worst = (lo, hi) if worse_when == "high" else (hi, lo)
        date, value = series[-1]
        scored_series[key] = [(d, score(v, best[1], worst[1])) for d, v in series]
        components.append({
            "key": key,
            "group": group,
            "label": label,
            "blurb": blurb,
            "value": round(value, decimals),
            "unit": unit,
            "decimals": decimals,
            "period": period_label(date, key),
            "best": round(best[1], decimals),
            "best_period": period_label(best[0], key),
            "worst": round(worst[1], decimals),
            "worst_period": period_label(worst[0], key),
            "record_since": series[0][0][:4],
            "score": round(score(value, best[1], worst[1])),
            "at_record": abs(value - worst[1]) < 10 ** -decimals / 2,
            "source": source,
            "url": FRED_PAGE.format(id=ids[0]),
            "series": ids,
        })

    # Monthly history: each series carried forward until its next reading.
    months = sorted({d for s in scored_series.values() for d, _ in s if d >= HISTORY_START and d[8:] == "01"})
    history = []
    for month in months:
        scores = []
        for key in scored_series:
            past = [v for d, v in scored_series[key] if d <= month]
            if not past:
                break
            scores.append(past[-1])
        else:
            history.append((month, sum(scores) / len(scores)))

    # The two arms of the K, for the chart: last reading of each year since ARMS_START.
    top1_by_year, wage_by_year = {}, {}
    for d, v in raw["WFRBST01134"]:
        top1_by_year[int(d[:4])] = v  # later quarters overwrite earlier ones
    for d, v in raw["W270RE1A156NBEA"]:
        wage_by_year[int(d[:4])] = v
    arm_years = list(range(ARMS_START, max(max(top1_by_year), max(wage_by_year)) + 1))
    arms = {
        "start": ARMS_START,
        "years": arm_years,
        "top1": [round(top1_by_year[y], 1) if y in top1_by_year else None for y in arm_years],
        "wage": [round(wage_by_year[y], 1) if y in wage_by_year else None for y in arm_years],
    }

    now = sum(c["score"] for c in components) / len(components)
    peak = max(history, key=lambda x: x[1])
    recession = max((h for h in history if "2008-01-01" <= h[0] <= "2012-12-01"), key=lambda x: x[1])
    shutdown = max((h for h in history if "2020-03-01" <= h[0] <= "2020-12-01"), key=lambda x: x[1])
    calm = min(history, key=lambda x: x[1])

    return {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "index": round(now),
        "method": "Six public series from FRED. Each scored 0 (best reading on record) to 100 (worst reading on record). The index is their plain average.",
        "groups": GROUPS,
        "components": components,
        "reference": {
            "recession_peak": {"value": round(recession[1]), "period": month_label(recession[0])},
            "shutdown_peak": {"value": round(shutdown[1]), "period": month_label(shutdown[0])},
            "record_high": {"value": round(peak[1]), "period": month_label(peak[0])},
            "record_low": {"value": round(calm[1]), "period": month_label(calm[0])},
        },
        "arms": arms,
        "history_since": HISTORY_START[:4],
        "history": [[d[:7], round(v, 1)] for d, v in history],
    }


def main():
    try:
        result = build()
    except Exception as exc:  # network trouble must not break the daily page build
        print(f"K gauge not refreshed ({exc}). Keeping the existing {OUT_FILE}.")
        return 0
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    ref = result["reference"]
    print(f"K gauge: {result['index']} / 100")
    for c in result["components"]:
        print(f"  {c['score']:>3}  {c['label']}: {c['value']}{c['unit']} ({c['period']}), best {c['best']} {c['best_period']}, worst {c['worst']} {c['worst_period']}")
    print(f"  2008-12 peak {ref['recession_peak']}, 2020 peak {ref['shutdown_peak']}, record high {ref['record_high']}, low {ref['record_low']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
