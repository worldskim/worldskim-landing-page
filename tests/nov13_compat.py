"""Exact new Nov13 inventory/nav/recent inverse; no general normalization."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
LEDGER=json.loads((ROOT/"tests/nov13_maintenance.json").read_text())
def restore_nov13(text,name):
    for pair in LEDGER["pages"].get(name,[]):
        assert text.count(pair["after"])==1,(name,pair["label"],"unexpected Nov13 maintenance bytes")
        text=text.replace(pair["after"],pair["before"],1)
    return text
