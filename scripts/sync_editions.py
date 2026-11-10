#!/usr/bin/env python3
"""Synchronize static cards/latest links from the publisher's existing SITE_CONFIG.

Run after adding an approved dated edition and its index.html SITE_CONFIG entry.
No network, editorial generation, provider changes or publishing is performed.
"""
import argparse
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CONFIG = re.compile(r"(var SITE_CONFIG=)(\{.*?\})(;)", re.S)
DATED = re.compile(r"editions/(\d{4}-\d{2}-\d{2})\.html$")


class Ranges(HTMLParser):
    """Locate element contents without reserializing the surrounding template."""
    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.lines = [0]
        for m in re.finditer("\n", text):
            self.lines.append(m.end())
        self.stack = []
        self.grid = None
        self.footer = None
        self.limit = None
        self.feed(text)

    def position(self):
        line, col = self.getpos()
        return self.lines[line - 1] + col

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag not in ("div", "footer"):
            return
        kind = "grid" if attrs.get("id") == "edition-grid" else "footer" if tag == "footer" else None
        if kind == "grid":
            self.limit = int(attrs["data-limit"]) if attrs.get("data-limit") else None
        self.stack.append((tag, kind, self.position() + len(self.get_starttag_text())))

    def handle_endtag(self, tag):
        if tag not in ("div", "footer") or not self.stack:
            return
        opened, kind, start = self.stack.pop()
        if opened != tag:
            raise ValueError("Unexpected template nesting")
        if kind:
            setattr(self, kind, (start, self.position()))


def read_config(text):
    match = CONFIG.search(text)
    if not match:
        raise ValueError("Expected existing JSON SITE_CONFIG in homepage")
    return json.loads(match[2])


def inventory(root, config):
    entries = config["editions"]
    urls = [e["url"] for e in entries]
    files = sorted("editions/" + p.name for p in (root / "editions").glob("????-??-??.html"))
    if not urls or len(urls) != len(set(urls)) or sorted(urls) != files:
        raise ValueError("SITE_CONFIG must list every dated edition exactly once; add approved metadata first")
    if urls != sorted(urls, reverse=True) or any(not DATED.fullmatch(u) for u in urls):
        raise ValueError("Edition URLs must be dated paths in newest-first order")
    for entry in entries:
        if not isinstance(entry["title"], list) or not entry["title"]:
            raise ValueError("Expected existing headline-array card format")
        for key in ("date", "description", "readingTime", "image"):
            if not isinstance(entry[key], str):
                raise ValueError("Invalid card field: " + key)
    return entries


def card(e):
    esc = lambda s: escape(s, quote=True)
    title = "".join('<span class="hl">' + esc(s) + "</span>" for s in e["title"])
    cover = ('<div class="cover"><img src="' + esc(e["image"]) +
             '" alt="" loading="lazy" width="800" height="450"></div>') if e["image"] else (
             '<div class="cover text">' + esc(" ".join(e["title"])) + "</div>")
    return ('<article class="card"><a href="' + esc(e["url"]) +
            '" class="card-link">' + cover + '<div class="card-copy"><p class="meta">' +
            esc(e["date"]) + " · " + esc(e["readingTime"]) + "</p><h3>" + title +
            "</h3><p>" + esc(e["description"]) +
            '</p><span class="read">Read edition →</span></div></a></article>')


def shared_latest(text, latest):
    """Only explicitly named shared links; never dated article/nav/poll links."""
    def replace(m):
        label = re.sub("<[^>]+>", "", m[3]).strip().replace("’", "'")
        if label in ("Latest edition", "Today's edition", "Today's trivia", "Daily trivia"):
            href = "/" + latest + ("#tri" if "trivia" in label.lower() else "")
            return m[1] + href + m[2] + m[3] + m[4]
        return m[0]
    return re.sub(r'(<a\b[^>]*\bhref=")[^"]*(".*?>)(.*?)(</a>)', replace, text, flags=re.S)


def planned(root):
    home = (root / "index.html").read_text()
    config = read_config(home)
    entries = inventory(root, config)
    changes = {}
    for path in [root / "index.html", root / "archive.html"]:
        text = path.read_text()
        match = CONFIG.search(text)
        if not match:
            raise ValueError("Missing existing SITE_CONFIG: " + path.name)
        # Keep the original data spelling when already identical.
        if json.loads(match[2]) != config:
            text = text[:match.start(2)] + json.dumps(config, ensure_ascii=False) + text[match.end(2):]
        parts = Ranges(text)
        if not parts.grid:
            raise ValueError("Missing edition-grid: " + path.name)
        cards = entries[:parts.limit] if parts.limit else entries
        start, end = parts.grid
        text = text[:start] + "".join(card(e) for e in cards) + text[end:]
        changes[path] = shared_latest(text, entries[0]["url"])
    # Shared destinations are current on historical pages too; editorial and
    # chronological Previous/Next navigation stay exactly as published.
    for path in sorted(root.rglob("*.html")):
        if path not in changes:
            changes[path] = shared_latest(path.read_text(), entries[0]["url"])
    return {p: value for p, value in changes.items() if p.read_text() != value}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail on stale generated content without writing")
    args = parser.parse_args()
    changes = planned(ROOT)
    for path, value in changes.items():
        print(("STALE " if args.check else "SYNC ") + str(path.relative_to(ROOT)))
        if not args.check:
            path.write_text(value)
    return int(bool(changes) and args.check)


if __name__ == "__main__":
    raise SystemExit(main())
