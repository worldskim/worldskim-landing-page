"""Exact approved Nov15 inverse spans, never ignores editorial/style/form changes."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[1]
LEDGER=json.loads((ROOT/"tests/nov15_maintenance.json").read_text())
def restore_nov15(text,name):
 sys.path.insert(0,str(ROOT/"scripts"))
 import sync_editions
 text=sync_editions.shared_latest(text,"editions/2026-11-14.html")
 for pair in LEDGER["pages"].get(name,[]):
  if text.count(pair["after"])==1:text=text.replace(pair["after"],pair["before"],1)
  else:assert text.count(pair["before"])==1,(name,pair["label"],"unexpected Nov15 maintenance bytes")
 return text
