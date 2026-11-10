"""Offline protocol and scope assertions for the separate intake candidate."""
from html.parser import HTMLParser
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("sync_signup",ROOT/"scripts/sync_signup.py")
sync=importlib.util.module_from_spec(spec);spec.loader.exec_module(sync)


class Forms(HTMLParser):
    def __init__(self,text):
        super().__init__();self.forms=[];self.current=None;self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="form":
            self.current={"attributes":a,"inputs":[]};self.forms.append(self.current)
        if tag=="input" and self.current is not None:self.current["inputs"].append(a)
    def handle_endtag(self,tag):
        if tag=="form":self.current=None


class Signup(unittest.TestCase):
    def test_every_native_form_exact_provider_protocol(self):
        config=sync.configuration(ROOT);count=0
        for p in ROOT.rglob("*.html"):
            text=p.read_text()
            self.assertNotIn("eomail",text)
            # Public legal review drafts still name the old provider; they need
            # factual/operator decisions, not an invented legal-policy rewrite.
            if p.name not in ("privacy.html","terms.html","disclosures.html"):
                self.assertNotIn("emailoctopus",text.lower())
            self.assertNotIn("ws-sub",text)
            self.assertNotIn("Check your inbox to confirm",text)
            for form in Forms(text).forms:
                attrs=form["attributes"]
                self.assertIn("data-newsletter-signup",attrs,str(p))
                self.assertEqual(attrs["action"],config["action"])
                self.assertEqual(attrs["method"],"post")
                self.assertEqual(attrs["accept-charset"],"UTF-8")
                self.assertNotIn("novalidate",attrs)
                hidden={i["name"]:i["value"] for i in form["inputs"] if i.get("type")=="hidden"}
                self.assertEqual(hidden,config["hidden"])
                visible=[i for i in form["inputs"] if i.get("type")!="hidden"]
                self.assertEqual(len(visible),1)
                self.assertEqual(visible[0]["name"],"email")
                self.assertEqual(visible[0]["type"],"email")
                self.assertIn("required",visible[0])
                self.assertIn("aria-describedby",visible[0])
                count+=1
        self.assertEqual(count,13)

    def test_native_signup_generation_is_idempotent(self):
        self.assertEqual(sync.planned(ROOT),{})

    def test_signup_javascript_never_transmits_or_claims_success(self):
        source=(ROOT/"email/signup.js").read_text()
        for forbidden in ("fetch(", "XMLHttpRequest", "sendBeacon", "sessionStorage", "localStorage",
                          "preventDefault(", "Check your inbox", "You're in"):
            self.assertNotIn(forbidden,source)

    def test_scope_preserves_non_signup_bytes(self):
        from signup_compat import restore_signup,MANIFEST
        for name,data in MANIFEST["pages"].items():
            restored=restore_signup((ROOT/name).read_text(),name)
            self.assertEqual(hashlib.sha256(restored.encode()).hexdigest(),data["sha256"],name)


if __name__=="__main__":unittest.main(verbosity=2)
