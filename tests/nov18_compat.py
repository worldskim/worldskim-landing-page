"""Exact Nov18 inverse for frozen release snapshots; full current locks are separate."""
from pathlib import Path
import json
R=Path(__file__).resolve().parents[1]
L=json.loads((R/"tests/nov18_maintenance.json").read_text())
def restore_nov18(text,name):
 from nov19_compat import restore_nov19
 text=restore_nov19(text,name)
 for p in reversed(L["pages"].get(name,[])):
  if text.count(p["after"])==1:text=text.replace(p["after"],p["before"],1)
  else:assert text.count(p["before"])==1,(name,"unapproved Nov18 maintenance bytes")
 return text
