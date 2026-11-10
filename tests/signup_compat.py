"""Undo only the verified signup replacement for historical content hashes."""
from pathlib import Path
import importlib.util
import json
import re

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=json.loads((ROOT/"tests/signup_baseline.json").read_text())
assert MANIFEST["baseline"]=="29505c27f092127c4802fea4732a3a681b738fb2"
spec=importlib.util.spec_from_file_location("signup_renderer",ROOT/"scripts/sync_signup.py")
renderer=importlib.util.module_from_spec(spec);spec.loader.exec_module(renderer)

FIXTURE_EDITS = [
    ("assert 'eomail5.com/form/4273f0aa-d6f8-11f1-9638-4b187b7e1294.js' in (root/'index.html').read_text()",
     "assert 'https://www.aweber.com/scripts/addlead.pl' in (root/'index.html').read_text()"),
    ("unchanged EmailOctopus signup embed", "verified native AWeber signup action"),
]


def restore_fixture(text,name):
    if name=="tests/links.test.py":
        for before,after in FIXTURE_EDITS:
            assert text.count(after)==1,"Expected exact authorized provider fixture edit"
            text=text.replace(after,before,1)
    return text

def restore_signup(text,name):
    baseline=MANIFEST["pages"].get(name)
    if baseline is None:return text
    config=renderer.configuration(ROOT)
    original_forms=iter(baseline["forms"])
    def form(match):
        place="main" if 'data-newsletter-signup="main"' in match[0] else "footer"
        assert match[0]==renderer.form(config,place),(name,"unexpected signup markup")
        return baseline["embed"] if place=="main" else next(original_forms)
    text=renderer.FORM.sub(form,text)
    assert list(original_forms)==[],(name,"footer form missing")
    assert text.count(renderer.NEW_SCRIPT)==1,(name,"signup script missing/duplicated")
    text=text.replace(renderer.NEW_SCRIPT,baseline["script"],1)
    text=text.replace('<link rel="stylesheet" href="/email/signup.css">',"",1)
    return text
