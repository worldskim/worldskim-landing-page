"""Exact, byte-bound latest/archive maintenance projection for old snapshots.

This does not normalize news, sources, forms, scripts, styles or legal content.
The current repair suite separately checks all actual pages and binds this
projection back to the untouched base commit hashes.
"""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = json.loads((ROOT / "tests/retrospective_maintenance.json").read_text())
REPAIR_FILES = {'docs/nov21-2026/old-rows.json', 'tests/nov21_compat.py', 'tests/test_nov21_site.py', 'docs/nov21-2026/approved-web-source.txt', 'docs/nov21-2026/approved-content.json', 'editions/2026-11-21.html', 'tests/nov21_maintenance.json'} | {'docs/nov20-2026/old-rows.json', 'tests/nov20_compat.py', 'tests/test_nov20_site.py', 'docs/nov20-2026/approved-web-source.txt', 'docs/nov20-2026/approved-content.json', 'editions/2026-11-20.html', 'tests/nov20_maintenance.json'} | {'docs/nov19-2026/old-rows.json', 'tests/nov19_compat.py', 'tests/test_nov19_site.py', 'docs/nov19-2026/approved-web-source.txt', 'docs/nov19-2026/approved-content.json', 'editions/2026-11-19.html', 'tests/nov19_maintenance.json'} | {'tests/nov18_compat.py', 'docs/nov18-2026/approved-web-source.txt', 'editions/2026-11-18.html', 'docs/nov18-2026/old-rows.json', 'tests/test_nov18_site.py', 'tests/nov18_maintenance.json', 'docs/nov18-2026/approved-content.json'} | {'tests/nov17_compat.py', 'docs/nov17-2026/approved-web-source.txt', 'docs/nov17-2026/approved-content.json', 'tests/test_nov17_site.py', 'tests/nov17_maintenance.json', 'docs/nov17-2026/old-rows.json', 'editions/2026-11-17.html'} | {'docs/nov16-2026/old-rows.json', 'tests/test_nov16_site.py', 'tests/nov16_maintenance.json', 'tests/nov16_compat.py', 'docs/nov16-2026/approved-web-source.txt', 'docs/nov16-2026/approved-content.json', 'editions/2026-11-16.html'} | {'editions/2026-11-15.html','tests/nov15_compat.py','tests/nov15_maintenance.json','tests/test_nov15_site.py','docs/nov15-2026/approved-content.json','docs/nov15-2026/approved-web-source.txt'} | {'tests/test_nov13_site.py', 'tests/nov13_maintenance.json', 'editions/2026-11-13.html', 'docs/nov13-2026/base-hashes.json', 'docs/nov13-2026/approved-content.json', 'tests/nov13_compat.py', 'docs/nov13-2026/approved-web-source.txt'} | set(LEDGER["changed_files"]) | {'docs/nov14-2026/approved-web-source.txt', 'tests/nov14_maintenance.json', 'docs/nov14-2026/approved-content.json', 'editions/2026-11-14.html', 'tests/test_nov14_site.py', 'tests/nov14_compat.py', 'docs/nov14-2026/base-hashes.json'}
spec = importlib.util.spec_from_file_location("maintenance_sync", ROOT / "scripts/sync_editions.py")
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


def restore_maintenance(text, name, shared=True):
    from nov14_compat import restore_nov14
    text = restore_nov14(text, name)
    for pair in LEDGER["pages"].get(name, []):
        count = pair.get("count", 1)
        assert text.count(pair["after"]) == count, (name, pair["label"], "unexpected current maintenance bytes")
        text = text.replace(pair["after"], pair["before"], count)
    if name.endswith(".html") and shared:
        text = sync.shared_latest(text, "editions/2026-11-10.html")
    if not shared:
        text = sync.shared_latest(text, sync.read_config((ROOT / "index.html").read_text())["editions"][0]["url"])
    return text


def restore_link_inventory(text):
    text=text.replace("'editions/2026-11-21.html', ", "", 1)
    text=text.replace("'editions/2026-11-20.html', ", "", 1)
    text=text.replace("'editions/2026-11-19.html', ", "", 1)
    text=text.replace("'editions/2026-11-18.html', ", "", 1)
    text=text.replace("'editions/2026-11-17.html', ", "", 1)
    text = text.replace("\'editions/2026-11-16.html\', ", "", 1)
    text = text.replace("'editions/2026-11-15.html', ", "", 1)
    text = text.replace("'editions/2026-11-13.html', ", "", 1)
    text = text.replace("'editions/2026-11-14.html', ", "", 1)
    pair = LEDGER["link_inventory"]
    assert text.count(pair["after"]) == 1, "Unexpected current link inventory fixture"
    return text.replace(pair["after"], pair["before"], 1)
