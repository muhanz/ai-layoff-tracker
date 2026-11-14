#!/usr/bin/env python3
"""
Event de-duplication - AI Layoff Tracker
=========================================
The daily job used to treat (company, exact date) as the identity of an event.
One layoff round is usually reported by several outlets on different days, so
the same round was being added again and again and summed into the headline.

This script folds repeat reports into the first report of the round. Nothing is
deleted: every folded row is kept under "merged_duplicates" in data/events.json
with the rule that folded it, and its source link is added to the kept event.

Rules (deliberately conservative: when in doubt, count once):
  A. Same company, same non-zero headcount, reported within 120 days of any
     report already in the round.
  B. Same company, reported within 14 days of any report already in the round,
     whatever the headcount (follow-up coverage of the same announcement).
  M. Manual folds, listed below with a reason.

Hand-curated rows ("locked": true) are never folded away automatically.
Safe to run every day; running it twice changes nothing.
"""

import json
import re
from datetime import datetime

DB_FILE = "data/events.json"
SAME_NUMBER_WINDOW_DAYS = 120
FOLLOW_UP_WINDOW_DAYS = 14

# event id -> (id of the event it repeats, reason)
MANUAL_FOLDS = {
    "oracle_2026-08-30": (
        "oracle_2026-06-23",
        "Speculative preview ('could') published one day before the 21,000 report of the same round.",
    ),
}

# Tier labels that mean the same thing as an existing tier.
TIER_ALIASES = {"yes": "confirmed"}


def company_key(name):
    """Normalise a company name so 'Meta', 'Meta Platforms' style variants match."""
    name = re.sub(r"\(.*?\)", "", name or "").lower()
    name = re.sub(r"[^a-z0-9 ]", " ", name)
    name = re.sub(r"\b(inc|corp|corporation|plc|ltd|llc|group|holdings|platforms)\b", " ", name)
    return " ".join(name.split())


def _days(a, b):
    return abs((datetime.strptime(a, "%Y-%m-%d") - datetime.strptime(b, "%Y-%m-%d")).days)


def find_round(event, rounds):
    """Return (kept_event, rule) if `event` repeats a round already kept, else (None, None)."""
    key = company_key(event.get("company"))
    date = event.get("date", "")
    headcount = event.get("headcount") or 0
    for kept in rounds:
        if company_key(kept["company"]) != key:
            continue
        member_dates = kept.get("_member_dates", [kept["date"]])
        try:
            gap = min(_days(date, d) for d in member_dates)
        except ValueError:
            continue
        if headcount > 0 and headcount == (kept.get("headcount") or 0) and gap <= SAME_NUMBER_WINDOW_DAYS:
            return kept, "A: same company and headcount within %d days" % SAME_NUMBER_WINDOW_DAYS
        if gap <= FOLLOW_UP_WINDOW_DAYS:
            return kept, "B: same company within %d days" % FOLLOW_UP_WINDOW_DAYS
    return None, None


def extends_window(rule):
    """A repeat of the round's own number (or a manual fold) is another report of the
    round, so later reports are measured from it too. A rule-B follow-up is not: letting
    follow-ups extend the window would chain unrelated rounds together."""
    return (rule or "")[:1] in ("A", "M")


def fold(event, kept, rule, merged):
    """Fold `event` into `kept`, keeping its sources and a record of the fold."""
    for url in event.get("source_urls") or []:
        if url and url not in kept.setdefault("source_urls", []):
            kept["source_urls"].append(url)
    for url, status in (event.get("link_status") or {}).items():
        kept.setdefault("link_status", {}).setdefault(url, status)
    if not (kept.get("headcount") or 0) and (event.get("headcount") or 0) and not kept.get("locked"):
        kept["headcount"] = event["headcount"]
    if extends_window(rule):
        kept.setdefault("_member_dates", [kept["date"]]).append(event["date"])
    merged.append({
        "id": event.get("id"),
        "company": event.get("company"),
        "date": event.get("date"),
        "headcount": event.get("headcount") or 0,
        "ai_attributed": event.get("ai_attributed"),
        "source_urls": event.get("source_urls") or [],
        "merged_into": kept.get("id"),
        "rule": rule,
    })


def recompute_totals(db):
    events = db["events"]
    meta = db["metadata"]

    def tier_sum(tier):
        return sum(e.get("headcount") or 0 for e in events if e.get("ai_attributed") == tier)

    meta["total_confirmed"] = tier_sum("confirmed")
    meta["total_likely"] = tier_sum("likely")
    meta["total_unclear"] = tier_sum("unclear")
    meta["total_estimated"] = sum(e.get("headcount") or 0 for e in events)


def dedupe(db):
    """De-duplicate db in place. Returns the number of rows folded this run."""
    merged = db.setdefault("merged_duplicates", [])
    already = {m["id"] for m in merged}
    by_id = {}
    rounds = []
    folded = 0

    for event in sorted(db["events"], key=lambda e: (e.get("date", ""), not e.get("locked"))):
        event["ai_attributed"] = TIER_ALIASES.get(event.get("ai_attributed"), event.get("ai_attributed"))
        kept, rule = None, None
        if not event.get("locked"):
            manual = MANUAL_FOLDS.get(event.get("id"))
            if manual and manual[0] in by_id:
                kept, rule = by_id[manual[0]], "M: " + manual[1]
            else:
                kept, rule = find_round(event, rounds)
        if kept is not None and event.get("id") not in already:
            fold(event, kept, rule, merged)
            folded += 1
            continue
        rounds.append(event)
        by_id[event.get("id")] = event

    # Earlier folds stay recorded; their dates still define each round's window.
    for m in merged:
        kept = by_id.get(m.get("merged_into"))
        if kept is not None and extends_window(m.get("rule")) and m["date"] not in kept.setdefault("_member_dates", [kept["date"]]):
            kept["_member_dates"].append(m["date"])

    db["events"] = rounds
    return folded


def strip_working_fields(db):
    for event in db["events"]:
        event.pop("_member_dates", None)


def is_repeat(candidate, db):
    """Used by the daily job: would this new event repeat a round we already have?"""
    rounds = [dict(e) for e in db["events"]]
    by_id = {e.get("id"): e for e in rounds}
    for m in db.get("merged_duplicates", []):
        kept = by_id.get(m.get("merged_into"))
        if kept is not None and extends_window(m.get("rule")):
            kept.setdefault("_member_dates", [kept["date"]]).append(m["date"])
    kept, _ = find_round(candidate, rounds)
    return kept is not None


def main():
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
    before = sum(e.get("headcount") or 0 for e in db["events"])
    folded = dedupe(db)
    strip_working_fields(db)
    recompute_totals(db)
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)
    meta = db["metadata"]
    print(f"Folded {folded} repeat report(s). Events kept: {len(db['events'])}.")
    print(f"Total tracked: {before:,} -> {meta['total_estimated']:,}")
    print(f"  confirmed {meta['total_confirmed']:,} | likely {meta['total_likely']:,} | unclear {meta['total_unclear']:,}")


if __name__ == "__main__":
    main()
