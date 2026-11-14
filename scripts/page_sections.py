#!/usr/bin/env python3
"""
Argument sections - AI Layoff Tracker
======================================
The sections of the page that make the case rather than list the events:
the tier-honest hero, the K gauge, the one-minute summary and chapter
heads, the attribution gap, the unemployment ladder, follow the money, the
forecast bars, the best objections, and what would change our mind.

Every outside statistic comes from data/facts.json, where each figure carries
its period and source link. A figure with no entry there cannot be rendered,
so nothing unsourced reaches the page. Update the number and its date there.
"""

import json
import os
from collections import defaultdict
from datetime import datetime

FACTS_FILE = "data/facts.json"
INDEX_FILE = "data/k_gauge.json"


class Facts:
    def __init__(self, path=FACTS_FILE):
        with open(path, "r", encoding="utf-8") as f:
            self._facts = json.load(f)["facts"]

    def __getitem__(self, key):
        return self._facts[key]

    def v(self, key):
        """The figure itself."""
        return self._facts[key]["value"]

    def n(self, key, field="number"):
        """The figure as a number, for drawing bars to scale."""
        return self._facts[key][field]

    def src(self, key):
        """A small source link with the period the figure refers to."""
        fact = self._facts[key]
        label = fact["source"]
        if fact.get("period"):
            label += ", " + fact["period"]
        return (
            f'<a class="fact-src" href="{fact["url"]}" target="_blank" rel="noopener">{label}</a>'
        )


EXTRA_CSS = """
        .fact-src { color: #555; font-size: 0.7rem; text-decoration: underline; text-decoration-color: #333; }
        .fact-src:hover { color: #888; }
        .tier-bar { display: flex; height: 10px; border-radius: 3px; overflow: hidden; background: #111; margin: 0.6rem 0 0.5rem; }
        .tier-bar span { display: block; height: 100%; }
        .tier-confirmed { background: #ff4444; }
        .tier-likely { background: #8a3a22; }
        .tier-unclear { background: #3a3a3a; }
        .tier-legend { display: flex; flex-wrap: wrap; gap: 0.4rem 1.1rem; justify-content: center; font-size: 0.78rem; color: #888; }
        .tier-legend strong { color: #ddd; font-variant-numeric: tabular-nums; }
        .tier-dot { display: inline-block; width: 8px; height: 8px; border-radius: 2px; margin-right: 0.35rem; }
        html { scroll-behavior: smooth; }
        .chapter, .tldr, #k-gauge, #depth-gauge { scroll-margin-top: 1.25rem; }
        .tldr { margin: 0 0 2rem; padding: 1.5rem 1.5rem 1.1rem; background: #0d0d0d; border: 1px solid #2a0000; border-radius: 10px; }
        .tldr-title { font-size: 0.7rem; letter-spacing: 0.16em; text-transform: uppercase; color: #ff4444; font-weight: 700; margin-bottom: 0.6rem; }
        .tldr-list { list-style: none; margin: 0; padding: 0; }
        .tldr-list li { border-top: 1px solid #1a1a1a; }
        .tldr-list li:first-child { border-top: none; }
        .tldr-list a { display: grid; grid-template-columns: 2.2rem 1fr auto; gap: 0.6rem; align-items: baseline; padding: 0.75rem 0; text-decoration: none; color: #999; font-size: 0.9rem; line-height: 1.6; }
        .tldr-list a:hover .tldr-go { color: #ff4444; }
        .tldr-n { color: #ff4444; font-weight: 800; font-size: 0.8rem; font-variant-numeric: tabular-nums; }
        .tldr-text strong { color: #eee; }
        .tldr-go { color: #444; font-size: 0.9rem; }
        .chapter { margin: 4.5rem 0 1.75rem; padding-top: 2rem; border-top: 2px solid #3d1111; }
        .chapter-num { font-size: 0.72rem; letter-spacing: 0.18em; text-transform: uppercase; color: #ff4444; font-weight: 700; }
        .chapter .chapter-title { font-size: clamp(1.6rem, 5vw, 2.4rem); color: #fff; line-height: 1.15; margin: 0.45rem 0 0.6rem; font-weight: 800; }
        .chapter-take { font-size: 1.02rem; color: #aaa; line-height: 1.65; max-width: 42rem; margin: 0; }
        .ahead-hero { margin: 1.75rem auto 0; width: 100%; max-width: 560px; box-sizing: border-box; padding-top: 1.5rem; border-top: 1px solid #1a0000; }
        .ahead-hero .depth-head { text-align: left; }
        .ahead-marks { display: flex; flex-wrap: wrap; gap: 0.3rem 1.1rem; justify-content: center; font-size: 0.78rem; color: #999; margin-top: 0.6rem; line-height: 1.5; }
        .ahead-marks strong { color: #eee; font-size: 0.95rem; font-variant-numeric: tabular-nums; }
        .ahead-more { display: block; margin-top: 0.6rem; font-size: 0.78rem; color: #ff8844; }
        .kg-hero { margin: 2rem auto 0; width: 100%; max-width: 560px; box-sizing: border-box; padding-top: 1.5rem; border-top: 1px solid #1a0000; }
        .kg-label { font-size: 0.7rem; letter-spacing: 0.18em; text-transform: uppercase; color: #ff8844; font-weight: 700; }
        .kg-score { margin: 0.2rem 0 0.7rem; color: #666; font-size: 1rem; }
        .kg-score strong { font-size: 3.2rem; font-weight: 900; color: #ff8844; font-variant-numeric: tabular-nums; margin-right: 0.3rem; }
        .kg-track { height: 16px; }
        .kg-marks { display: flex; flex-wrap: wrap; gap: 0.3rem 1.1rem; justify-content: center; font-size: 0.74rem; color: #888; margin-top: 0.5rem; }
        .kg-marks strong { color: #ddd; }
        .zone-swatch { display: inline-block; width: 14px; height: 8px; margin-right: 0.35rem; border-radius: 2px; background: repeating-linear-gradient(135deg, #5a1a14 0 3px, #2a0d0d 3px 6px); }
        .kg-caption { font-size: 0.84rem; color: #999; line-height: 1.7; margin: 0.9rem 0 0; }
        .kg-caption a { color: #ff8844; white-space: nowrap; }
        .kg-sub { font-size: 0.82rem; color: #999; margin-top: 0.25rem; }
        .k-legend { display: flex; flex-wrap: wrap; gap: 0.35rem 1.25rem; font-size: 0.78rem; color: #aaa; margin-bottom: 0.9rem; }
        .k-legend i { display: inline-block; width: 14px; height: 3px; border-radius: 2px; margin-right: 0.45rem; vertical-align: middle; }
        .k-plot, .k-axis { display: grid; grid-template-columns: minmax(0, 1fr) 8.6rem; column-gap: 0.75rem; }
        .k-plot { height: 240px; }
        .k-area { position: relative; touch-action: pan-y; cursor: crosshair; }
        .k-area svg { position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible; }
        .k-base { stroke: #2a2a2a; stroke-width: 1; vector-effect: non-scaling-stroke; }
        .k-line { fill: none; stroke-width: 2; vector-effect: non-scaling-stroke; stroke-linejoin: round; stroke-linecap: round; }
        .k-dot { position: absolute; width: 9px; height: 9px; border-radius: 50%; transform: translate(-50%, -50%); box-shadow: 0 0 0 2px #0d0d0d; pointer-events: none; }
        .k-base-label { position: absolute; right: 3%; font-size: 0.66rem; color: #666; transform: translateY(-130%); pointer-events: none; }
        .k-ends { position: relative; }
        .k-end { position: absolute; left: 0; right: 0; transform: translateY(-50%); font-size: 0.74rem; color: #999; line-height: 1.4; }
        .k-end strong { display: block; font-size: 1.25rem; color: #eee; font-variant-numeric: tabular-nums; line-height: 1.1; }
        .k-end small { display: block; font-size: 0.68rem; color: #666; }
        .k-years { position: relative; height: 1.2rem; margin-top: 0.35rem; font-size: 0.66rem; color: #777; font-variant-numeric: tabular-nums; }
        .k-years span { position: absolute; transform: translateX(-50%); }
        .k-years span:first-child { transform: none; }
        .k-cross { position: absolute; top: 0; bottom: 0; width: 1px; background: #444; pointer-events: none; }
        .k-tip { position: absolute; top: 4px; z-index: 2; background: #161616; border: 1px solid #2a2a2a; border-radius: 6px; padding: 0.45rem 0.6rem; font-size: 0.72rem; color: #bbb; line-height: 1.55; white-space: nowrap; pointer-events: none; font-variant-numeric: tabular-nums; }
        .k-tip b { color: #eee; }
        .k-tip i { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 0.4rem; }
        .k-table { margin-top: 0.9rem; font-size: 0.78rem; color: #888; }
        .k-table summary { cursor: pointer; color: #999; }
        .k-table table { margin-top: 0.6rem; border-collapse: collapse; width: 100%; max-width: 26rem; font-variant-numeric: tabular-nums; }
        .k-table th, .k-table td { text-align: right; padding: 0.3rem 0.6rem; border-bottom: 1px solid #1a1a1a; }
        .k-table th:first-child, .k-table td:first-child { text-align: left; }
        .k-table th { color: #aaa; font-weight: 600; }
        .di-group { margin-top: 1.5rem; }
        .di-group-head { display: flex; justify-content: space-between; align-items: baseline; gap: 1rem; padding-bottom: 0.4rem; border-bottom: 1px solid #1f1f1f; }
        .di-group-name { font-size: 0.72rem; letter-spacing: 0.14em; text-transform: uppercase; color: #ccc; font-weight: 700; }
        .di-group-score { font-size: 0.8rem; color: #888; white-space: nowrap; }
        .di-group-score strong { font-size: 1.3rem; color: #ff8844; font-variant-numeric: tabular-nums; }
        .di-row { padding: 0.9rem 0 0.2rem; }
        .di-head { display: flex; justify-content: space-between; gap: 1rem; align-items: baseline; font-size: 0.88rem; color: #ddd; }
        .di-val { font-weight: 800; color: #ff6644; font-variant-numeric: tabular-nums; white-space: nowrap; }
        .di-val em { font-style: normal; font-weight: 400; color: #777; font-size: 0.72rem; margin-left: 0.3rem; }
        .di-track { position: relative; height: 8px; background: #151515; border-radius: 4px; margin: 0.45rem 0 0.3rem; overflow: hidden; }
        .di-fill { position: absolute; left: 0; top: 0; bottom: 0; min-width: 3px; border-radius: 4px; background: linear-gradient(90deg, #7d2418, #ff4444); }
        .di-foot { display: flex; justify-content: space-between; gap: 0.75rem; font-size: 0.68rem; color: #666; font-variant-numeric: tabular-nums; }
        .di-badge { color: #ff4444; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; }
        .di-blurb { font-size: 0.78rem; color: #888; line-height: 1.6; margin-top: 0.3rem; }
        details.objection > summary { cursor: pointer; list-style: none; display: grid; grid-template-columns: 1fr auto; gap: 0.75rem; align-items: start; margin-bottom: 0; }
        details.objection > summary::-webkit-details-marker { display: none; }
        details.objection > summary::after { content: "+"; color: #ff8844; font-weight: 700; font-size: 1.1rem; line-height: 1.3; }
        details.objection[open] > summary::after { content: "−"; }
        details.objection[open] > summary { margin-bottom: 0.5rem; }
        @media (max-width: 600px) {
            .tldr-list a { grid-template-columns: 1.8rem 1fr; }
            .tldr-go { display: none; }
            .kg-score strong { font-size: 2.6rem; }
            .k-plot, .k-axis { grid-template-columns: minmax(0, 1fr) 6.6rem; column-gap: 0.5rem; }
            .k-end strong { font-size: 1.05rem; }
        }
        .depth-gauge { margin: 1.75rem auto 0; width: 100%; max-width: 560px; text-align: left; box-sizing: border-box; }
        .depth-title { font-size: 0.68rem; letter-spacing: 0.14em; text-transform: uppercase; color: #ff8844; font-weight: 700; text-align: center; margin-bottom: 0.9rem; }
        .depth-row { margin-bottom: 1.4rem; }
        .depth-head { display: flex; justify-content: space-between; gap: 0.75rem; font-size: 0.74rem; color: #888; margin-bottom: 0.35rem; }
        .depth-head strong { color: #ff8844; font-variant-numeric: tabular-nums; white-space: nowrap; }
        .depth-track { position: relative; height: 12px; background: #111; border: 1px solid #1f1f1f; border-radius: 4px; }
        .depth-fill { position: absolute; left: 0; top: 0; bottom: 0; min-width: 3px; background: linear-gradient(90deg, #7d2418, #ff4444); border-radius: 3px 0 0 3px; }
        .depth-zone { position: absolute; top: 0; bottom: 0; background: repeating-linear-gradient(135deg, #2a0d0d 0 5px, #180808 5px 10px); }
        .depth-tick { position: absolute; top: -3px; bottom: -3px; width: 2px; background: #ff8844; }
        .depth-scale { position: relative; height: 1.1rem; margin-top: 0.3rem; font-size: 0.66rem; color: #777; font-variant-numeric: tabular-nums; }
        .depth-scale span { position: absolute; top: 0; transform: translateX(-50%); white-space: nowrap; }
        .depth-scale span:first-child { transform: none; left: 0; }
        .depth-scale span:last-child { transform: none; left: auto; right: 0; }
        .depth-key { list-style: none; margin: 0.5rem 0 0; padding: 0; font-size: 0.76rem; color: #888; line-height: 1.6; }
        .depth-key li { padding: 0.15rem 0; }
        .depth-key strong { color: #ddd; font-variant-numeric: tabular-nums; }
        .depth-note { font-size: 0.72rem; color: #777; line-height: 1.65; border-top: 1px solid #1a1a1a; padding-top: 0.7rem; }
        .argument-section { margin: 2.5rem 0; padding: 1.75rem 1.5rem; background: #0d0d0d; border: 1px solid #1a1a1a; border-radius: 10px; }
        .argument-section h2 { font-size: 1.35rem; color: #eee; margin-bottom: 0.4rem; }
        .argument-sub { font-size: 0.88rem; color: #888; line-height: 1.7; margin-bottom: 1.25rem; }
        .ladder { display: flex; flex-direction: column; gap: 0.5rem; }
        .ladder-step { display: grid; grid-template-columns: 5.5rem 1fr; gap: 0.9rem; align-items: center; padding: 0.8rem 1rem; background: #111; border-radius: 8px; border-left: 3px solid #3d1111; }
        .ladder-step:nth-child(2) { margin-left: 0.6rem; border-left-color: #5a1a14; }
        .ladder-step:nth-child(3) { margin-left: 1.2rem; border-left-color: #7d2418; }
        .ladder-step:nth-child(4) { margin-left: 1.8rem; border-left-color: #a8301c; }
        .ladder-step:nth-child(5) { margin-left: 2.4rem; border-left-color: #ff4444; }
        .ladder-value { font-size: 1.5rem; font-weight: 800; color: #ff6644; font-variant-numeric: tabular-nums; }
        .ladder-text { font-size: 0.82rem; color: #999; line-height: 1.6; }
        .ladder-text strong { color: #ddd; }
        .argument-note { margin-top: 1rem; padding: 0.9rem 1.1rem; border-left: 3px solid #2a1800; background: #0a0a0a; border-radius: 0 6px 6px 0; font-size: 0.84rem; color: #999; line-height: 1.75; }
        .argument-note strong { color: #ff8844; }
        .argument-quote { margin-top: 1rem; font-size: 1rem; color: #ddd; font-style: italic; line-height: 1.6; }
        .argument-quote cite { display: block; margin-top: 0.3rem; font-size: 0.72rem; font-style: normal; color: #666; }
        .money-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.75rem; }
        .money-card { padding: 1rem; background: #111; border-radius: 8px; }
        .money-value { font-size: 1.5rem; font-weight: 800; color: #ff6644; font-variant-numeric: tabular-nums; }
        .money-label { font-size: 0.8rem; color: #999; line-height: 1.6; margin-top: 0.25rem; }
        .said-list { margin-top: 1rem; display: flex; flex-direction: column; gap: 0.5rem; }
        .said-row { font-size: 0.82rem; color: #999; line-height: 1.65; padding: 0.6rem 0.9rem; background: #111; border-radius: 6px; }
        .said-row strong { color: #ddd; }
        .objection { padding: 1rem 0; border-top: 1px solid #1a1a1a; }
        .objection:first-of-type { border-top: none; padding-top: 0; }
        .objection-claim { font-size: 0.98rem; color: #eee; font-weight: 600; line-height: 1.5; margin-bottom: 0.5rem; }
        .objection-part { font-size: 0.84rem; color: #999; line-height: 1.75; margin-top: 0.35rem; }
        .objection-tag { display: inline-block; font-size: 0.62rem; letter-spacing: 0.1em; text-transform: uppercase; font-weight: 700; margin-right: 0.5rem; }
        .tag-true { color: #6fbf73; }
        .tag-miss { color: #ff8844; }
        .mind-row { display: grid; grid-template-columns: 1fr auto; gap: 1rem; align-items: baseline; padding: 0.8rem 0; border-top: 1px solid #1a1a1a; }
        .mind-row:first-of-type { border-top: none; }
        .mind-test { font-size: 0.86rem; color: #ccc; line-height: 1.6; }
        .mind-now { font-size: 0.78rem; color: #888; text-align: right; white-space: nowrap; }
        .mind-now strong { color: #ff6644; font-size: 1rem; }
        @media (max-width: 600px) {
            .ladder-step { grid-template-columns: 4.5rem 1fr; margin-left: 0 !important; }
            .mind-row { grid-template-columns: 1fr; }
            .mind-now { text-align: left; white-space: normal; }
        }
"""


def tier_split(db):
    meta = db["metadata"]
    total = max(meta["total_estimated"], 1)
    unclear = meta.get("total_unclear", total - meta["total_confirmed"] - meta.get("total_likely", 0))
    return {
        "confirmed": meta["total_confirmed"],
        "likely": meta.get("total_likely", 0),
        "unclear": unclear,
        "pct_confirmed": round(meta["total_confirmed"] / total * 100),
        "pct_likely": round(meta.get("total_likely", 0) / total * 100),
        "pct_unclear": round(unclear / total * 100),
        "folded": len(db.get("merged_duplicates", [])),
    }


def hero_tiers_html(db):
    """Sits under the big number: what is inside it, by how sure we are."""
    t = tier_split(db)
    return f"""
            <div class="dd-progress-wrap">
                <div class="tier-bar" role="img" aria-label="{t['pct_confirmed']} percent confirmed, {t['pct_likely']} percent likely, {t['pct_unclear']} percent unclear">
                    <span class="tier-confirmed" style="width:{t['pct_confirmed']}%"></span>
                    <span class="tier-likely" style="width:{t['pct_likely']}%"></span>
                    <span class="tier-unclear" style="width:{t['pct_unclear']}%"></span>
                </div>
                <div class="tier-legend">
                    <span><span class="tier-dot tier-confirmed"></span><strong>{t['confirmed']:,}</strong> the company named AI</span>
                    <span><span class="tier-dot tier-likely"></span><strong>{t['likely']:,}</strong> likely</span>
                    <span><span class="tier-dot tier-unclear"></span><strong>{t['unclear']:,}</strong> unclear</span>
                </div>
                <div class="dd-progress-note">Each layoff round is counted once. {t['folded']} repeat reports are folded into the round they describe. Some of this is AI washing. Some AI cuts are never announced. Both are covered below.</div>
            </div>"""


def depth_gauge_html(db, facts):
    """How far the sourced count is into what the forecasters expect, and how far
    unemployment is from the levels people warn about. Drawn to scale."""
    total = db["metadata"]["total_estimated"]
    top = facts.n("mck35_demand")
    switch = facts.n("mck35_switch")
    gs = facts.n("gs_displaced")
    pct_jobs = total / top * 100
    pct_jobs_label = f"{pct_jobs:.1f}"

    scale_max = 25.0
    now = facts.n("u3")
    warn_low = facts.n("warn_unemp", "low")
    warn_high = facts.n("warn_unemp", "high")
    peak09 = facts.n("unrate_2009")
    peak20 = facts.n("unrate_2020")

    def at(value, maximum):
        return f"{value / maximum * 100:.1f}"

    def short(n):
        return f"{n / 1_000_000:.0f}M"

    return f"""
        <section class="argument-section" id="depth-gauge">
            <h2>How deep could this go?</h2>
            <p class="argument-sub">Two bars, both drawn to scale. The first is jobs. The second is the unemployment rate.</p>
            <div class="depth-gauge" style="max-width:none;margin-top:0;">
                <div class="depth-row">
                    <div class="depth-head"><span>Job cuts we can source, against the forecasts</span><strong>{pct_jobs_label}% of {facts.v('mck35_demand')}</strong></div>
                    <div class="depth-track" role="img" aria-label="{total:,} sourced job cuts is {pct_jobs_label} percent of the {facts.v('mck35_demand')} jobs McKinsey expects automation to cut {facts['mck35_demand']['horizon']}">
                        <div class="depth-fill" style="width:{pct_jobs:.2f}%"></div>
                        <span class="depth-tick" style="left:{at(switch, top)}%"></span>
                        <span class="depth-tick" style="left:{at(gs, top)}%"></span>
                    </div>
                    <div class="depth-scale">
                        <span>0</span>
                        <span style="left:{at(switch, top)}%">{short(switch)}</span>
                        <span style="left:{at(gs, top)}%">{short(gs)}</span>
                        <span>{short(top)}</span>
                    </div>
                    <ul class="depth-key">
                        <li><strong>{total:,}</strong> AI-linked cuts sourced so far, worldwide</li>
                        <li><strong>{facts.v('mck35_switch')}</strong> U.S. workers who will have to change occupations {facts['mck35_switch']['horizon']}, in a range of {facts['mck35_switch']['range']} {facts.src('mck35_switch')}</li>
                        <li><strong>{facts.v('gs_displaced')}</strong> U.S. workers displaced {facts['gs_displaced']['horizon']}, {facts['gs_displaced']['share']} of the workforce {facts.src('gs_displaced')}</li>
                        <li><strong>{facts.v('mck35_demand')}</strong> U.S. jobs&rsquo; worth of work automation removes {facts['mck35_demand']['horizon']} {facts.src('mck35_demand')}</li>
                    </ul>
                </div>

                <div class="depth-row">
                    <div class="depth-head"><span>U.S. unemployment rate, against the warning range</span><strong>{facts.v('u3')} now</strong></div>
                    <div class="depth-track" role="img" aria-label="Unemployment is {facts.v('u3')}. The warning range is {facts.v('warn_unemp')}. In 1933 it was {facts.v('unrate_1933')}.">
                        <div class="depth-zone" style="left:{at(warn_low, scale_max)}%; width:{at(warn_high - warn_low, scale_max)}%"></div>
                        <div class="depth-fill" style="width:{at(now, scale_max)}%"></div>
                        <span class="depth-tick" style="left:{at(peak09, scale_max)}%"></span>
                        <span class="depth-tick" style="left:{at(peak20, scale_max)}%"></span>
                    </div>
                    <div class="depth-scale">
                        <span>0%</span>
                        <span style="left:{at(peak09, scale_max)}%">{facts.v('unrate_2009')}</span>
                        <span style="left:{at(peak20, scale_max)}%">{facts.v('unrate_2020')}</span>
                        <span style="left:{at(warn_high, scale_max)}%">{warn_high:.0f}%</span>
                        <span>{scale_max:.0f}%</span>
                    </div>
                    <ul class="depth-key">
                        <li><strong>{facts.v('u3')}</strong> today {facts.src('u3')}</li>
                        <li><strong>{facts.v('unrate_2009')}</strong> the peak after the 2008 financial crisis {facts.src('unrate_2009')}</li>
                        <li><strong>{facts.v('unrate_2020')}</strong> the peak of the 2020 shutdown {facts.src('unrate_2020')}</li>
                        <li><strong>{facts.v('warn_unemp')}</strong> the shaded range: where the head of one AI lab said unemployment could go {facts['warn_unemp']['horizon']} {facts.src('warn_unemp')}</li>
                        <li><strong>{facts.v('unrate_1933')}</strong> the end of the bar: the worst year of the Great Depression {facts.src('unrate_1933')}</li>
                    </ul>
                </div>

                <div class="depth-note">These are forecasts, and they are not layoff counts. Goldman expects most displaced workers to find other work. McKinsey expects {facts.v('mck35_created')} new jobs over the same years ({facts.src('mck35_created')}). Our count is announced cuts only. The bars are here for scale: how much of this is still ahead.</div>
            </div>
        </section>"""


def exposure_html(facts):
    """Replaces the single top-down forecast with the pools of work it would come from."""
    return f"""
        <section class="projection-hero">
            <div class="proj-eyebrow">Where the exposure is</div>
            <div class="proj-number">{facts.v('office_admin_jobs')}</div>
            <p class="proj-label">Americans work in office and administrative support: the work AI does first</p>
            <p class="proj-source">{facts.src('office_admin_jobs')}</p>
            <div class="proj-vs">
                <div class="proj-vs-item">
                    <div class="proj-vs-value">{facts.v('csr_jobs')}</div>
                    <div class="proj-vs-label">customer service representatives<br>{facts.src('csr_jobs')}</div>
                </div>
                <div class="proj-vs-item">
                    <div class="proj-vs-value">{facts.v('insurance_jobs')}</div>
                    <div class="proj-vs-label">work in insurance carriers and related firms<br>{facts.src('insurance_jobs')}</div>
                </div>
                <div class="proj-vs-item">
                    <div class="proj-vs-value">{facts.v('mck_hours')}</div>
                    <div class="proj-vs-label">of U.S. hours worked could be automated by 2030<br>{facts.src('mck_hours')}</div>
                </div>
            </div>
            <p class="proj-source" style="margin-top:1rem;">Exposure is not a layoff forecast. McKinsey&rsquo;s own estimate is {facts.v('mck_transitions')} Americans changing occupations by 2030 ({facts.src('mck_transitions')}). Goldman Sachs found {facts.v('gs_exposed')} of U.S. occupations exposed to some degree ({facts.src('gs_exposed')}).</p>
        </section>"""


def attribution_gap_html(db, facts):
    meta = db["metadata"]
    return f"""
                <div style="font-size:0.65rem;letter-spacing:0.12em;text-transform:uppercase;color:#ff4444;font-weight:700;margin-bottom:0.5rem;">The attribution gap runs both ways</div>
                <p style="font-size:0.85rem;color:#ccc;line-height:1.8;margin-bottom:0.75rem;">
                    Challenger, Gray &amp; Christmas counts <strong>{facts.v('challenger_ai')}</strong> U.S. job cuts where the employer cited AI ({facts.src('challenger_ai')}).
                    Our tracker counts <strong>{meta['total_confirmed']:,}</strong> worldwide where the company named AI, and <strong>{meta['total_estimated']:,}</strong> once likely and unclear cases are added.
                    Those are different scopes: one country against the world. We do not multiply one by the other.
                </p>
                <p style="font-size:0.85rem;color:#999;line-height:1.8;margin-bottom:0.75rem;">
                    <strong style="color:#ff8844;">Some of our number is too high.</strong>
                    A company that over-hired can say &ldquo;AI&rdquo; when it means &ldquo;costs.&rdquo; That is AI washing. It is why every event carries a confidence tier, and why &ldquo;confirmed&rdquo; only means the company said so.
                </p>
                <p style="font-size:0.85rem;color:#999;line-height:1.8;">
                    <strong style="color:#ff8844;">Some of it is too low.</strong>
                    The cheapest cut is the job that is never posted. No press release, no layoff, nothing for a tracker to catch.
                    That shows up in hiring data, not layoff data. It is the next section.
                </p>"""


def acceleration_html(db):
    by_year = defaultdict(int)
    for e in db["events"]:
        by_year[e["date"][:4]] += e.get("headcount") or 0
    years = sorted(by_year)
    peak = max(by_year.values()) or 1
    this_year = str(datetime.utcnow().year)
    last_date = max(e["date"] for e in db["events"])
    through = datetime.strptime(last_date, "%Y-%m-%d").strftime("%b %-d")
    rows = ""
    for y in years:
        partial = y == this_year
        record = by_year[y] == peak
        tag = f'{y} <span style="font-size:0.65rem;color:#444">to {through}</span>' if partial else y
        val_style = ' style="color:#ff2222"' if record else ""
        rows += f"""
            <div class="pace-row">
                <span class="pace-year-tag">{tag}</span>
                <div class="pace-bar-wrap"><div class="pace-bar{' record' if record else ''}" style="width:{by_year[y] / peak * 100:.1f}%"></div></div>
                <span class="pace-val"{val_style}>{by_year[y]:,}</span>
            </div>"""
    earlier = [by_year[y] for y in years if y != this_year]
    if this_year in by_year and earlier and by_year[this_year] > max(earlier):
        note = f"<strong>{this_year} has already passed every earlier year</strong>, with the year not over."
    else:
        note = "Year-by-year totals from the events below."
    return f"""
        <section class="pace-section">
            <h2>The Acceleration</h2>
            <p class="pace-sub">AI-linked job cuts by year: our tracker, global, each round counted once, all three confidence tiers</p>{rows}
            <p class="pace-note">{note} These are announced cuts in public reporting. Challenger, Gray &amp; Christmas tracks the U.S. employer-disclosed subset. Announcements are the visible part: the argument that follows does not depend on them.</p>
        </section>"""


def ladder_html(facts):
    return f"""
        <section class="argument-section" id="ladder">
            <h2>&ldquo;But unemployment is only {facts.v('u3')}&rdquo;</h2>
            <p class="argument-sub">True. It is also the number least able to see this. The headline rate counts people who looked for work in the last four weeks and found none. Walk down from it.</p>
            <div class="ladder">
                <div class="ladder-step">
                    <div class="ladder-value">{facts.v('u3')}</div>
                    <div class="ladder-text"><strong>Headline unemployment (U-3).</strong> Active job seekers only. {facts.src('u3')}</div>
                </div>
                <div class="ladder-step">
                    <div class="ladder-value">{facts.v('u6')}</div>
                    <div class="ladder-text"><strong>Add the underemployed (U-6).</strong> Part-timers who want full-time work, and people who have stopped looking for now. {facts.src('u6')}</div>
                </div>
                <div class="ladder-step">
                    <div class="ladder-value">{facts.v('grad_underemp')}</div>
                    <div class="ladder-text"><strong>Recent college graduates in jobs that do not need the degree.</strong> A graduate pouring coffee counts as fully employed. {facts.src('grad_underemp')}</div>
                </div>
                <div class="ladder-step">
                    <div class="ladder-value">{facts.v('lfpr')}</div>
                    <div class="ladder-text"><strong>Labor force participation.</strong> It was {facts.v('lfpr_feb2020')} in February 2020. Someone who stops looking leaves the unemployment rate entirely. Part of this drop is an aging population. The next rung takes retirees out. {facts.src('lfpr')}</div>
                </div>
                <div class="ladder-step">
                    <div class="ladder-value">{facts.v('prime_men_out')}</div>
                    <div class="ladder-text"><strong>Men aged 25 to 54 who are neither working nor looking.</strong> In the 1950s it was about {facts.v('prime_men_out_1950s')}. These are not retirees or students. {facts.src('prime_men_out')}</div>
                </div>
            </div>
            <div class="argument-note">
                <strong>The job that was never posted.</strong>
                When a role is automated through attrition, nobody is laid off. Someone leaves and the opening is never listed. Headcount shrinks, the work is gone, and the unemployment rate does not move.
                It lands on the people who would have been hired: the third rung above.
            </div>
            <p class="argument-quote">&ldquo;The easiest people to fire are the people you have not hired yet.&rdquo;
                <cite>Andrew Yang, Jubilee <a class="fact-src" href="https://www.youtube.com/watch?v=020ZvO0FbMM" target="_blank" rel="noopener">Surrounded</a>, September 2026</cite>
            </p>
            <div class="argument-note">
                <strong>The immigration factor.</strong>
                A smaller labor pool also holds the unemployment rate down while hiring slows. Fewer people looking means a lower rate by definition.
            </div>
        </section>"""


def money_html(facts):
    said = "".join(
        f'<div class="said-row"><strong>{s["who"]}</strong> ({s["when"]}): {s["said"]} '
        f'<a class="fact-src" href="{s["url"]}" target="_blank" rel="noopener">source</a></div>'
        for s in facts["ceo_statements"]["items"]
    )
    return f"""
        <section class="argument-section" id="money">
            <h2>Follow the money</h2>
            <p class="argument-sub">Layoff counts look backward. Budgets look forward. You do not need a single press release to see where companies expect the work to be done.</p>
            <div class="money-grid">
                <div class="money-card">
                    <div class="money-value">{facts.v('dc_construction')}</div>
                    <div class="money-label">a year in U.S. data center construction, against {facts.v('office_construction')} for offices. {facts.v('dc_vs_office_note')} {facts.src('dc_construction')}</div>
                </div>
                <div class="money-card">
                    <div class="money-value">{facts.v('capex_2026')}</div>
                    <div class="money-label">{facts.v('capex_2026_scope')} {facts.src('capex_2026')}</div>
                </div>
            </div>
            <div class="argument-note">
                <strong>The incentive.</strong>
                A chief executive who delivers the same output with fewer people is rewarded for it. One who will not is replaced by one who will. Nobody has to be a villain for this to happen. It is what the scoreboard pays for.
            </div>
            <p class="argument-sub" style="margin:1.1rem 0 0;">They are saying it on the record:</p>
            <div class="said-list">{said}</div>
        </section>"""


def objections_html(facts):
    items = [
        (
            "&ldquo;AI automates tasks, not jobs. A job is a bundle of tasks.&rdquo;",
            "Almost no job can be handed over whole. People keep the parts that need judgment and trust.",
            "A team of 100 that loses 60% of its tasks does not keep 100 people on the remaining 40%. The job survives. Most of the jobs do not.",
        ),
        (
            "&ldquo;Technology has always created more jobs than it destroyed.&rdquo;",
            "It has. About four in ten American workers farmed in 1900. Fewer than two in a hundred do now, and the country is richer for it.",
            "That shift took generations, and it was not gentle while it happened. This one is measured in years, and it is the first to do the thinking work that people moved into last time.",
        ),
        (
            "&ldquo;Cheaper means more demand. Look at radiologists.&rdquo;",
            "Where people want far more of something than they can afford, lower cost grows the field. Radiology is hiring.",
            "It only works where demand is nowhere near full. Nobody files more insurance claims because claims got cheaper to process.",
        ),
        (
            f"&ldquo;The World Economic Forum expects {facts.v('wef_created')} new jobs against {facts.v('wef_displaced')} displaced.&rdquo;",
            f"That is the forecast: worldwide, from every cause and not AI alone, by {facts.v('wef_horizon')}. {facts.src('wef_created')}",
            "A net figure hides who. The new jobs are not offered to the people displaced, in the place they live, at the pay they had. And an American salary is among the most expensive to keep.",
        ),
        (
            "&ldquo;New business formation is booming. People are becoming founders.&rdquo;",
            f"Applications are running at {facts.v('bfs_apps')} a month, well above 2019. {facts.src('bfs_apps')}",
            f"{facts.v('bfs_employer_note')} A laid-off analyst who registers a consulting company counts as a new business.",
        ),
        (
            "&ldquo;Companies are already rehiring. Look at Klarna.&rdquo;",
            f"Klarna did walk it back. {facts.v('klarna')} {facts.src('klarna')}",
            "A reversal belongs on the record next to the cut, and we log the ones we find. Rehiring some of a team is not rehiring the team.",
        ),
        (
            "&ldquo;Half of these &lsquo;AI layoffs&rsquo; are ordinary cost cuts with a better story.&rdquo;",
            "Some are. That is AI washing, and it is why only part of our count is marked confirmed.",
            "It cuts the other way too: most displacement never becomes a layoff at all. That is why the stronger evidence on this page is about hiring, not firing.",
        ),
    ]
    blocks = "".join(
        f"""
            <details class="objection"{' open' if i == 0 else ''}>
                <summary class="objection-claim"><span>{claim}</span></summary>
                <div class="objection-part"><span class="objection-tag tag-true">What is true</span>{true}</div>
                <div class="objection-part"><span class="objection-tag tag-miss">What it misses</span>{miss}</div>
            </details>"""
        for i, (claim, true, miss) in enumerate(items)
    )
    return f"""
        <section class="argument-section" id="objections">
            <h2>The best objections</h2>
            <p class="argument-sub">Each of these is partly right. If we cannot answer them, you should not believe the rest of this page. Open any one to read our reply.</p>{blocks}
        </section>"""


def change_our_mind_html(facts):
    rows = [
        ("Recent graduates stop sliding into jobs that do not need a degree.", facts.v("grad_underemp"), "underemployed now", "grad_underemp"),
        ("The economy outside health care adds jobs for a full year.", facts.v("jobs_ex_health_2025"), "in 2025", "jobs_ex_health_2025"),
        ("Young workers in AI-exposed occupations start getting hired again.", facts.v("canaries"), "relative decline, ages 22 to 25", "canaries"),
        ("New businesses start hiring, not only registering.", facts.v("bfs_apps"), "applications a month", "bfs_apps"),
    ]
    body = "".join(
        f"""
            <div class="mind-row">
                <div class="mind-test">{test} {facts.src(key)}</div>
                <div class="mind-now"><strong>{value}</strong> {label}</div>
            </div>"""
        for test, value, label, key in rows
    )
    return f"""
        <section class="argument-section" id="change-our-mind">
            <h2>What would change our mind</h2>
            <p class="argument-sub">We would be glad to be wrong. If these turn, we will say so here.</p>{body}
        </section>"""


def load_index():
    if not os.path.exists(INDEX_FILE):
        raise SystemExit(f"{INDEX_FILE} is missing. Run scripts/k_gauge.py to build it.")
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def _component(idx, key):
    return next(c for c in idx["components"] if c["key"] == key)


def _fmt(c, field="value"):
    return f"{c[field]:.{c['decimals']}f}{c['unit']}"


def _group_avg(idx, group):
    scores = [c["score"] for c in idx["components"] if c["group"] == group]
    return round(sum(scores) / len(scores))


def _index_at(idx, month):
    for m, value in idx["history"]:
        if m == month:
            return round(value)
    return None


def ahead_hero_html(db, facts):
    """Under the headline number: the sourced count against what the forecasters expect."""
    total = db["metadata"]["total_estimated"]
    top = facts.n("mck35_demand")
    gs = facts.n("gs_displaced")
    pct = total / top * 100
    gs_at = gs / top * 100

    def named(key, name):
        return f'<a class="fact-src" href="{facts[key]["url"]}" target="_blank" rel="noopener">{name}</a>'

    return f"""
            <div class="ahead-hero">
                <div class="depth-head"><span>What we can source, against what is forecast</span><strong>{pct:.1f}% of {facts.v('mck35_demand')}</strong></div>
                <div class="depth-track" role="img" aria-label="{total:,} sourced job cuts is {pct:.1f} percent of the {facts.v('mck35_demand')} U.S. jobs McKinsey expects automation to remove {facts['mck35_demand']['horizon']}. Goldman Sachs expects {facts.v('gs_displaced')} U.S. workers displaced {facts['gs_displaced']['horizon']}.">
                    <div class="depth-fill" style="width:{pct:.2f}%"></div>
                    <span class="depth-tick" style="left:{gs_at:.1f}%"></span>
                </div>
                <div class="depth-scale">
                    <span>0</span>
                    <span style="left:{gs_at:.1f}%">{gs / 1_000_000:.0f}M</span>
                    <span>{top / 1_000_000:.0f}M</span>
                </div>
                <div class="ahead-marks">
                    <span><strong>{facts.v('gs_displaced')}</strong> U.S. workers displaced {facts['gs_displaced']['horizon']} ({named('gs_displaced', 'Goldman Sachs')})</span>
                    <span><strong>{facts.v('mck35_demand')}</strong> U.S. jobs&rsquo; worth of work automated {facts['mck35_demand']['horizon']} ({named('mck35_demand', 'McKinsey')})</span>
                </div>
                <a class="ahead-more" href="#depth-gauge">What the forecasts say &darr;</a>
            </div>"""


def k_gauge_hero_html(idx, facts):
    """The one bar under the headline number: how far the K-shaped economy has split."""
    ref = idx["reference"]
    now = idx["index"]
    crash = ref["recession_peak"]["value"]
    shut = ref["shutdown_peak"]["value"]
    return f"""
            <div class="kg-hero">
                <div class="kg-label">K gauge</div>
                <div class="kg-sub">how far the economy has split, and how close that is to breaking</div>
                <div class="kg-score"><strong>{now}</strong>out of 100</div>
                <div class="depth-track kg-track" role="img" aria-label="The K gauge is {now} out of 100. It reached {crash} after the 2008 crash and {shut} in the 2020 shutdown.">
                    <div class="depth-zone" style="left:{crash}%; right:0"></div>
                    <div class="depth-fill" style="width:{now}%"></div>
                    <span class="depth-tick" style="left:{crash}%"></span>
                    <span class="depth-tick" style="left:{shut}%"></span>
                </div>
                <div class="depth-scale">
                    <span>0</span>
                    <span style="left:{crash}%">{crash}</span>
                    <span style="left:{shut}%">{shut}</span>
                    <span>100</span>
                </div>
                <div class="kg-marks">
                    <span><strong>{crash}</strong> after the 2008 crash</span>
                    <span><strong>{shut}</strong> the 2020 shutdown</span>
                    <span><span class="zone-swatch"></span>only reached in a crisis</span>
                </div>
                <p class="kg-caption">A K-shaped economy has one arm going up and one going down. This scores the gap between them on six public measures. It reached {crash} after the 2008 crash, with unemployment near {facts.v('unrate_2009')}. It is {now} today, with unemployment at {facts.v('u3')}. <a href="#k-gauge">How it is built &darr;</a></p>
            </div>"""


K_UP = "#e06b33"    # validated pair for the dark surface (dataviz validator, both pass)
K_DOWN = "#4a8ad0"

K_SCRIPT = """
        <script>
        (function () {
            var plot = document.querySelector('.k-plot');
            if (!plot) return;
            var d = JSON.parse(plot.getAttribute('data-k'));
            var area = plot.querySelector('.k-area');
            var cross = plot.querySelector('.k-cross');
            var tip = plot.querySelector('.k-tip');
            function show(e) {
                var r = area.getBoundingClientRect();
                var f = Math.max(0, Math.min(1, (e.clientX - r.left) / r.width));
                var i = Math.round(f * (d.years.length - 1));
                var x = i / (d.years.length - 1) * 100;
                function val(v) { return v === null ? 'not published yet' : v.toFixed(1) + '%'; }
                cross.style.left = x + '%';
                tip.innerHTML = '<b>' + d.years[i] + '</b><br><i style="background:' + d.up + '"></i>Top 1% share of wealth: <b>' + val(d.top1[i]) + '</b><br><i style="background:' + d.down + '"></i>Wage share of income: <b>' + val(d.wage[i]) + '</b>';
                if (x > 50) { tip.style.left = 'auto'; tip.style.right = (100 - x) + '%'; tip.style.marginRight = '8px'; }
                else { tip.style.right = 'auto'; tip.style.left = x + '%'; tip.style.marginLeft = '8px'; }
                cross.hidden = false; tip.hidden = false;
            }
            function hide() { cross.hidden = true; tip.hidden = true; }
            area.addEventListener('pointermove', show);
            area.addEventListener('pointerdown', show);
            area.addEventListener('pointerleave', hide);
        })();
        </script>"""


def k_shape_html(idx):
    """The K itself, drawn from data: two shares set to the same starting point."""
    arms = idx["arms"]
    years, top1, wage = arms["years"], arms["top1"], arms["wage"]
    start = arms["start"]
    span = years[-1] - years[0]
    lo, hi = 80.0, 150.0  # index scale, start year = 100

    def x(year):
        return (year - years[0]) / span * 100

    def y(value, base):
        return (hi - value / base * 100) / (hi - lo) * 100

    def line(series):
        base = series[0]
        return " ".join(f"{x(yr):.2f},{y(v, base):.2f}" for yr, v in zip(years, series) if v is not None)

    def last(series):
        return next((yr, v) for yr, v in reversed(list(zip(years, series))) if v is not None)

    up_year, up_val = last(top1)
    dn_year, dn_val = last(wage)
    up_y, dn_y = y(up_val, top1[0]), y(dn_val, wage[0])
    base_y = y(1, 1)
    up_change = (up_val / top1[0] - 1) * 100
    dn_change = (1 - dn_val / wage[0]) * 100

    ticks = [yr for yr in years if yr % 10 == 0]
    tick_html = "".join(f'<span style="left:{x(yr):.1f}%">{yr}</span>' for yr in ticks)
    table_years = [yr for yr in years if yr % 5 == 0]
    if years[-1] not in table_years:
        table_years.append(years[-1])
    rows = "".join(
        f"<tr><td>{yr}</td><td>{'%.1f%%' % top1[years.index(yr)] if top1[years.index(yr)] is not None else 'not published yet'}</td>"
        f"<td>{'%.1f%%' % wage[years.index(yr)] if wage[years.index(yr)] is not None else 'not published yet'}</td></tr>"
        for yr in table_years
    )
    data = json.dumps({"years": years, "top1": top1, "wage": wage, "up": K_UP, "down": K_DOWN}).replace('"', "&quot;")
    top1_c = _component(idx, "top1")
    wage_c = _component(idx, "wage_share")
    label = (
        f"Line chart since {start}. The top 1 percent share of all wealth rose from {top1[0]} percent to {up_val} percent. "
        f"Wages and salaries as a share of the economy's income fell from {wage[0]} percent to {dn_val} percent."
    )
    return f"""
        <section class="argument-section" id="k-shape">
            <h2>What a K-shaped economy looks like</h2>
            <p class="argument-sub">Take two numbers and start them at the same point in {start}. One is the share of all wealth held by the top 1%. The other is the share of the economy&rsquo;s income paid out as wages and salaries. One arm went up. One went down. That is the K.</p>
            <div class="k-legend">
                <span><i style="background:{K_UP}"></i>Share of all wealth held by the top 1%</span>
                <span><i style="background:{K_DOWN}"></i>Wages and salaries as a share of the economy&rsquo;s income</span>
            </div>
            <div class="k-plot" role="img" aria-label="{label}" data-k="{data}">
                <div class="k-area">
                    <svg viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
                        <line class="k-base" x1="0" x2="100" y1="{base_y:.2f}" y2="{base_y:.2f}"></line>
                        <polyline class="k-line" stroke="{K_UP}" points="{line(top1)}"></polyline>
                        <polyline class="k-line" stroke="{K_DOWN}" points="{line(wage)}"></polyline>
                    </svg>
                    <span class="k-base-label" style="top:{base_y:.1f}%">where both stood in {start}</span>
                    <span class="k-dot" style="left:{x(up_year):.1f}%;top:{up_y:.1f}%;background:{K_UP}"></span>
                    <span class="k-dot" style="left:{x(dn_year):.1f}%;top:{dn_y:.1f}%;background:{K_DOWN}"></span>
                    <div class="k-cross" hidden></div>
                    <div class="k-tip" hidden></div>
                </div>
                <div class="k-ends">
                    <div class="k-end" style="top:{up_y:.1f}%"><strong>{up_val:.1f}%</strong>of all wealth, top 1%<small>{top1[0]:.1f}% in {start} &middot; up {up_change:.0f}%</small></div>
                    <div class="k-end" style="top:{dn_y:.1f}%"><strong>{dn_val:.1f}%</strong>of income, wages<small>{wage[0]:.1f}% in {start} &middot; down {dn_change:.0f}%</small></div>
                </div>
            </div>
            <div class="k-axis"><div class="k-years">{tick_html}</div><div></div></div>
            <details class="k-table">
                <summary>See the numbers</summary>
                <table>
                    <tr><th>Year</th><th>Top 1% share of wealth</th><th>Wage share of income</th></tr>{rows}
                </table>
            </details>
            <div class="argument-note"><strong>The K gauge scores this gap.</strong> It adds four more measures to these two: three for whether you can find work, and one for how people feel. Sources: <a class="fact-src" href="{top1_c['url']}" target="_blank" rel="noopener">Federal Reserve via FRED, {top1_c['period']}</a> and <a class="fact-src" href="{wage_c['url']}" target="_blank" rel="noopener">BEA via FRED, {wage_c['period']}</a>. Each line shows the last reading of each year.</div>
        </section>{K_SCRIPT}"""


def k_gauge_detail_html(idx, facts):
    """Chapter 3: the six measures behind the index, grouped so the K is visible."""
    ref = idx["reference"]
    now = idx["index"]
    groups = ""
    for group in ("work", "gains", "mood"):
        rows = ""
        for c in [c for c in idx["components"] if c["group"] == group]:
            if c["at_record"]:
                badge = '<span class="di-badge">at its worst on record</span>'
            elif c["score"] >= 90:
                badge = '<span class="di-badge">near its worst on record</span>'
            else:
                badge = ""
            rows += f"""
                <div class="di-row">
                    <div class="di-head"><span>{c['label']}</span><span class="di-val">{_fmt(c)}<em>{c['period']}</em></span></div>
                    <div class="di-track" role="img" aria-label="{c['label']}: {c['score']} out of 100 between its best and worst readings on record"><div class="di-fill" style="width:{c['score']}%"></div></div>
                    <div class="di-foot"><span>best {_fmt(c, 'best')}, {c['best_period']}</span>{badge}<span>worst {_fmt(c, 'worst')}, {c['worst_period']}</span></div>
                    <div class="di-blurb">{c['blurb']} <a class="fact-src" href="{c['url']}" target="_blank" rel="noopener">{c['source']} via FRED, on record since {c['record_since']}</a></div>
                </div>"""
        groups += f"""
            <div class="di-group">
                <div class="di-group-head"><span class="di-group-name">{idx['groups'][group]}</span><span class="di-group-score"><strong>{_group_avg(idx, group)}</strong> out of 100</span></div>{rows}
            </div>"""

    before = _index_at(idx, "2019-12")
    start = _index_at(idx, "2023-03")
    then = ""
    if before is not None and start is not None:
        then = f" It was {before} at the end of 2019 and {start} in March 2023, where this tracker starts."

    top1 = _component(idx, "top1")
    wage = _component(idx, "wage_share")
    extremes = ""
    if top1["at_record"] and wage["at_record"]:
        extremes = " The wealth and wage measures are at their extremes anyway."

    return f"""
        <section class="argument-section" id="k-gauge">
            <h2>The K gauge: {now} out of 100</h2>
            <p class="argument-sub">One number for the split between the people who own the gains and the people who work for a wage. Six public measures, each scored from its best reading on record (0) to its worst (100), then averaged. No weights and no model. The choice of six is ours.{then}</p>{groups}
            <div class="argument-note"><strong>Read it as a K.</strong> The job-market measures average {_group_avg(idx, 'work')}. Those are the ones the headlines watch, and they are calm. The measures of who gets the gains average {_group_avg(idx, 'gains')}. The job market is the calm half of this index. It is also the half that the cuts on this page push on.</div>
            <div class="argument-note"><strong>Where is the breaking point?</strong> Nobody knows. 100 would mean all six at their worst at the same moment, which has never happened. The index reached {ref['recession_peak']['value']} in {ref['recession_peak']['period']} and {ref['shutdown_peak']['value']} in {ref['shutdown_peak']['period']}. Both times the job market recovered and the index fell.{extremes} For a sense of what breaking has looked like: in 1933, {facts.v('unrate_1933')} of American workers were unemployed ({facts.src('unrate_1933')}). The summer before, the Army cleared jobless veterans out of Washington.</div>
        </section>"""


def summary_html(db, idx, facts):
    """The whole argument in six lines. Each line is the door to its chapter."""
    meta = db["metadata"]
    total = meta["total_estimated"]
    top1 = _component(idx, "top1")
    wage = _component(idx, "wage_share")
    records = " Both are at record extremes." if top1["at_record"] and wage["at_record"] else ""
    pct = total / facts.n("mck35_demand") * 100
    low_m = facts.n("gs_displaced") / 1_000_000
    high_m = facts.n("mck35_demand") / 1_000_000
    lines = [
        ("ch-count", "What we can count.", f"{total:,} job cuts linked to AI since March 2023, each with a source. In {meta['total_confirmed']:,} of them the company named AI itself."),
        ("ch-calm", "Why the official numbers look calm.", f"Unemployment is {facts.v('u3')}. It only counts people who are still looking, so most of this never reaches it."),
        ("ch-split", "Two economies.", f"The top 1% holds {_fmt(top1)} of all wealth. Wages and salaries are {_fmt(wage)} of the economy&rsquo;s income.{records} Our K gauge reads {idx['index']} out of 100."),
        ("ch-depth", "How deep this could go.", f"Goldman and McKinsey put what is ahead at {low_m:.0f} to {high_m:.0f} million U.S. jobs&rsquo; worth of work within a decade. What we have sourced is {pct:.1f}% of the larger figure."),
        ("ch-doubt", "The best case against us.", "Seven serious objections, what is true in each, and the four numbers that would prove us wrong."),
        ("ch-next", "What we do about it.", "AI will create enormous value. The open question is who shares in it."),
    ]
    items = "".join(
        f"""
                <li><a href="#{anchor}"><span class="tldr-n">{i:02d}</span><span class="tldr-text"><strong>{title}</strong> {text}</span><span class="tldr-go">&darr;</span></a></li>"""
        for i, (anchor, title, text) in enumerate(lines, 1)
    )
    return f"""
        <section class="tldr" id="summary">
            <div class="tldr-title">The argument in one minute</div>
            <ol class="tldr-list">{items}
                <li><a href="#ch-data"><span class="tldr-n">+</span><span class="tldr-text"><strong>The data.</strong> All {len(db['events'])} events, their sources, and how we count.</span><span class="tldr-go">&darr;</span></a></li>
            </ol>
        </section>"""


def chapter_html(number, anchor, title, take):
    label = f"Part {number}" if number else "Appendix"
    return f"""
        <div class="chapter" id="{anchor}">
            <div class="chapter-num">{label}</div>
            <h2 class="chapter-title">{title}</h2>
            <p class="chapter-take">{take}</p>
        </div>"""


def load_facts():
    if not os.path.exists(FACTS_FILE):
        raise SystemExit(f"{FACTS_FILE} is missing. Every outside statistic on the page is read from it.")
    return Facts()
