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
REPAIR_FILES = set(LEDGER["changed_files"])
spec = importlib.util.spec_from_file_location("maintenance_sync", ROOT / "scripts/sync_editions.py")
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


def restore_maintenance(text, name, shared=True):
    for pair in LEDGER["pages"].get(name, []):
        count = pair.get("count", 1)
        assert text.count(pair["after"]) == count, (name, pair["label"], "unexpected current maintenance bytes")
        text = text.replace(pair["after"], pair["before"], count)
    if name.endswith(".html") and shared:
        text = sync.shared_latest(text, "editions/2026-11-10.html")
    return text


def restore_link_inventory(text):
    pair = LEDGER["link_inventory"]
    assert text.count(pair["after"]) == 1, "Unexpected current link inventory fixture"
    return text.replace(pair["after"], pair["before"], 1)
