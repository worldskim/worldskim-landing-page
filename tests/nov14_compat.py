"""Exact reviewed inverse spans; never ignores editorial/style/form differences."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
LEDGER=json.loads((ROOT/"tests/nov14_maintenance.json").read_text())
def restore_nov14(text,name):
    from nov13_compat import restore_nov13
    return restore_nov14_ledger(restore_nov13(text,name),name)
def restore_nov14_ledger(text,name):
    # Use the unchanged label-aware synchronizer, not global date replacement.
    import sys
    sys.path.insert(0,str(ROOT/"scripts"))
    import sync_editions
    text=sync_editions.shared_latest(text,"editions/2026-11-12.html")
    for pair in LEDGER["pages"].get(name,[]):
        assert text.count(pair["after"])==1,(name,pair["label"],"unexpected Nov14 maintenance bytes")
        text=text.replace(pair["after"],pair["before"],1)
    return text
