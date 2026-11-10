"""Narrow compatibility for the authorized shared-footer maintenance.

Restore only explicitly labelled shared hrefs to their pinned pre-maintenance
values for old release hashes. Actual hrefs must first match current SITE_CONFIG;
the inventory suite independently asserts the live destinations on every page.
All article, source, date, style, script, form and chronological nav bytes remain
part of the old hashes.
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = json.loads((ROOT / "tests/archive_shared_baseline.json").read_text())
assert MANIFEST["baseline"] == "5e9a4508ef2befc9675e94003d8cec76ffc1ef7c"
ANCHOR = re.compile(r'(<a\b[^>]*\bhref=")([^"]*)(".*?>)(.*?)(</a>)', re.S)
LABELS = ("Latest edition", "Today's edition", "Today's trivia", "Daily trivia")
MAINTENANCE_FILES = {
    "README.md", "docs/CUTOVER-REVIEW.md", "scripts/sync_editions.py",
    "tests/test_archive_sync.py", "tests/archive_preservation.json",
    "tests/archive_shared_baseline.json", "tests/archive_compat.py",
    "tests/test_nov7_site.py", "tests/test_nov8_site.py",
    "tests/test_nov9_site.py", "tests/test_nov10_site.py",
}


def latest_url():
    text = (ROOT / "index.html").read_text()
    return json.loads(re.search(r"var SITE_CONFIG=(\{.*?\});", text, re.S)[1])["editions"][0]["url"]


def restore_shared(text, name):
    originals = iter(MANIFEST["links"].get(name, []))
    latest = latest_url()
    def replace(match):
        label = re.sub("<[^>]+>", "", match[4]).strip().replace("’", "'")
        if label not in LABELS:
            return match[0]
        original = next(originals)
        assert label == original["label"], (name, "shared link label/order changed")
        target = "/" + latest + ("#tri" if "trivia" in label.lower() else "")
        # Baseline checkout is also permitted for before/after suite comparison.
        assert match[2] in (target, original["href"]), (name, "unexpected shared destination")
        return match[1] + original["href"] + match[3] + match[4] + match[5]
    result = ANCHOR.sub(replace, text)
    assert list(originals) == [], (name, "shared links removed")
    return result
