#!/usr/bin/env python3
"""
Text-node translations - AI Layoff Tracker
===========================================
Translates the page one text node at a time: the text between two HTML tags.
The tables live in scripts/i18n/<lang>.json as {english text: translation}.

Why text nodes: a whole-node match cannot hit half of some other sentence, and
the order of the table does not matter.

Numbers that change every day
-----------------------------
A number that appears in both the English text and its translation is carried
across: "547,016 job cuts" keeps matching tomorrow when the number is 548,120,
and the translation gets the new number.

A number that the translation rewrote (for example "15 million" as "1500万")
is matched literally. If that English number ever changes, the node stops
matching and falls back to English. Stale text shows up in the audit
(scripts/i18n_audit.py); it never shows a wrong number.
"""

import json
import os
import re
from collections import Counter

TABLE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "i18n")
NUMBER = re.compile(r"\d[\d,.]*\d|\d")
SCRIPT_OR_STYLE = re.compile(r"(<script\b.*?</script>|<style\b.*?</style>)", re.DOTALL | re.IGNORECASE)
TEXT_NODE = re.compile(r">([^<>]+)<")
META_CONTENT = re.compile(r'(<meta\b[^>]*\bcontent=")([^"]*)(")')


def _compile(english, translation):
    """Return (regex, parts) where parts rebuild the translation from a match."""
    available = Counter(NUMBER.findall(translation))
    seen = Counter()
    groups = {}  # (number text, which occurrence) -> group index
    pattern, last = [], 0
    for match in NUMBER.finditer(english):
        value = match.group(0)
        pattern.append(re.escape(english[last:match.start()]))
        if seen[value] < available[value]:
            groups[(value, seen[value])] = len(groups) + 1
            pattern.append(r"(\d[\d,.]*\d|\d)")
        else:
            pattern.append(re.escape(value))
        seen[value] += 1
        last = match.end()
    pattern.append(re.escape(english[last:]))

    parts, last, seen = [], 0, Counter()
    for match in NUMBER.finditer(translation):
        value = match.group(0)
        parts.append(translation[last:match.start()])
        parts.append(groups.get((value, seen[value]), value))
        seen[value] += 1
        last = match.end()
    parts.append(translation[last:])
    return re.compile("".join(pattern)), parts


class NodeTranslator:
    def __init__(self, lang_code):
        path = os.path.join(TABLE_DIR, lang_code + ".json")
        self.exact, self.patterns = {}, []
        table = {}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                table.update(json.load(f))
        head_path = os.path.join(TABLE_DIR, "head.json")  # <meta content="..."> text, all languages in one file
        if os.path.exists(head_path):
            with open(head_path, "r", encoding="utf-8") as f:
                table.update(json.load(f).get(lang_code, {}))
        for english, translation in table.items():
            english = " ".join(english.split())
            if not english or not translation or english == translation:
                continue
            self.exact[english] = translation
            if NUMBER.search(english):
                self.patterns.append(_compile(english, translation))

    def lookup(self, text):
        if text in self.exact:
            return self.exact[text]
        for regex, parts in self.patterns:
            match = regex.fullmatch(text)
            if match:
                return "".join(match.group(p) if isinstance(p, int) else p for p in parts)
        return None

    def _node(self, match):
        raw = match.group(1)
        text = " ".join(raw.split())
        if not text:
            return match.group(0)
        translated = self.lookup(text)
        if translated is None:
            return match.group(0)
        lead = raw[:len(raw) - len(raw.lstrip())]
        trail = raw[len(raw.rstrip()):]
        return ">" + lead + translated + trail + "<"

    def _meta(self, match):
        translated = self.lookup(" ".join(match.group(2).split()))
        return match.group(0) if translated is None else match.group(1) + translated + match.group(3)

    def apply(self, html):
        if not self.exact:
            return html
        head_end = html.find("</head>")
        if head_end > 0:  # share text and description, before any other pass can touch them
            html = META_CONTENT.sub(self._meta, html[:head_end]) + html[head_end:]
        pieces = SCRIPT_OR_STYLE.split(html)
        for i in range(0, len(pieces), 2):  # odd pieces are script/style blocks
            pieces[i] = TEXT_NODE.sub(self._node, pieces[i])
        return "".join(pieces)
