#!/usr/bin/env python3
"""
Translation audit - AI Layoff Tracker
======================================
Lists the visible text on a translated page that is still in English.

Skipped on purpose: scripts and styles, the news ticker, the events table
(company names, notes and dates stay in English by design), source citations,
and the language switcher.

Usage: python scripts/i18n_audit.py [zh-hans|zh-hant|es] [--list]
"""

import re
import sys
from html.parser import HTMLParser

SKIP_CLASSES = {"ticker-wrap", "recent", "fact-src", "lang-switcher", "voice-quote", "evis-quote"}
SKIP_TAGS = {"script", "style", "code"}
VOID = {"br", "img", "input", "meta", "link", "hr", "source", "wbr", "line", "polyline", "path", "circle", "rect"}
LATIN_WORD = re.compile(r"[A-Za-z]{3,}")
ENTITY = re.compile(r"&#?[A-Za-z0-9]+;")
# Names and terms that are the same in every language.
ALLOWED = re.compile(
    r"(?<![A-Za-z])(AI|IA|GPT|BLS|FRED|BEA|JOLTS|Eudy|McKinsey|Goldman|Sachs|Challenger|Gray|Christmas|Fortune|Klarna|Amazon|Ford|Shopify|"
    r"Andy|Jassy|Jim|Farley|Tobi|L&uuml;tke|Andrew|Yang|Jubilee|Surrounded|Dario|Amodei|Anthropic|Pope|Leo|XIV|Magnifica|Humanitas|"
    r"Heather|Long|NBC|ICE|Trump|Iran|Dem|Party|DOGE|Stanford|Census|Bureau|Cengage|Group|NACE|EPI|WEF|Layoffs|fyi|TrueUp|GitHub|"
    r"Wayback|Machine|muhan|being|Alphabet|Microsoft|Meta|Walnut|Axios|Lebergott|Margo|Michigan|University|Federal|Reserve|"
    r"merged_duplicates|LIVE|Youngstown|Gary|Detroit|Ohio|Seattle|Austin|Boston|NYC|York|Francisco|San|New|Uber|Nov|Oct|Sep|"
    r"Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Dec|Instagram|Bloomberg|Entrepreneur|Washington|Armada|Bridge|Digital|Economy|Lab|"
    r"World|Economic|Forum|marginal|EE|UU|vs|io|[\w.]+@[\w.]+)(?![A-Za-z])")


class Nodes(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.stack = []      # (tag, skipped)
        self.nodes = []
        self.buf = ""

    def skipped(self):
        return any(s for _, s in self.stack)

    def flush(self):
        text = " ".join(self.buf.split())
        if text and not self.skipped():
            self.nodes.append(text)
        self.buf = ""

    def handle_starttag(self, tag, attrs):
        self.flush()
        if tag in VOID:
            return
        classes = set((dict(attrs).get("class") or "").split())
        self.stack.append((tag, tag in SKIP_TAGS or bool(classes & SKIP_CLASSES)))

    def handle_endtag(self, tag):
        self.flush()
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        self.buf += data

    def handle_entityref(self, name):
        self.buf += "&%s;" % name

    def handle_charref(self, name):
        self.buf += "&#%s;" % name


def text_nodes(html):
    start = html.find("<main>")
    parser = Nodes()
    parser.feed(html[start:] if start >= 0 else html)
    parser.flush()
    return parser.nodes


def leftover(html, english_html=None, lang="zh"):
    """Text nodes of a translated page that are still English.

    Chinese pages: any node with English words left in it. Spanish shares the
    alphabet, so there a node counts only if it is unchanged from the English page.
    """
    nodes = text_nodes(html)
    if lang == "es":
        if english_html is None:
            with open("public/index.html", "r", encoding="utf-8") as f:
                english_html = f.read()
        english = text_nodes(english_html)
        if len(english) != len(nodes):
            return [n for n in nodes if is_english(n)]
        return [n for n, en in zip(nodes, english) if n == en and is_english(n)]
    return [n for n in nodes if is_english(n)]


def is_english(node):
    """True when a text node still has English words in it (entities and shared names aside)."""
    return bool(LATIN_WORD.search(ENTITY.sub(" ", ALLOWED.sub("", node))))


def worklist():
    """English text nodes that are still English on at least one translated page."""
    with open("public/index.html", "r", encoding="utf-8") as f:
        english = text_nodes(f.read())
    todo = []
    for lang in ("zh-hans", "zh-hant", "es"):
        with open(f"public/{lang}/index.html", "r", encoding="utf-8") as f:
            translated = text_nodes(f.read())
        if len(translated) != len(english):
            raise SystemExit(f"{lang}: page structure differs from English ({len(translated)} vs {len(english)} text nodes)")
        for en, tr in zip(english, translated):
            still = (tr == en) if lang == "es" else is_english(tr)
            if still and is_english(en) and en not in todo:
                todo.append(en)
    return todo


def main():
    if "--worklist" in sys.argv:
        import json
        import os
        os.makedirs("scripts/i18n", exist_ok=True)
        todo = worklist()
        with open("scripts/i18n/worklist.json", "w", encoding="utf-8") as f:
            json.dump(todo, f, ensure_ascii=False, indent=1)
        print(f"{len(todo)} English text node(s) written to scripts/i18n/worklist.json ({sum(len(t) for t in todo):,} characters)")
        return 0
    langs = [a for a in sys.argv[1:] if not a.startswith("--")] or ["zh-hans", "zh-hant", "es"]
    worst = 0
    for lang in langs:
        with open(f"public/{lang}/index.html", "r", encoding="utf-8") as f:
            nodes = leftover(f.read(), lang=lang)
        worst = max(worst, len(nodes))
        print(f"{lang}: {len(nodes)} text node(s) still in English")
        if "--list" in sys.argv:
            for node in nodes:
                print("   " + node[:160])
    return 0


if __name__ == "__main__":
    sys.exit(main())
