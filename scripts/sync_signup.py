#!/usr/bin/env python3
"""Render the verified native form protocol; no network or subscription writes."""
import argparse
from html import escape
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
FORM = re.compile(r'<form\b[^>]*\bclass="[^"]*\bws-foot-form\b[^"]*"[^>]*>.*?</form>', re.S)
EO = re.compile(r'<script\b[^>]*src="https://eomail5\.com/form/[^"]+"[^>]*></script>')
OLD_SCRIPT = re.compile(r'<script>\s*/\* Footer signup:.*?</script>', re.S)
NEW_SCRIPT = '<script src="/email/signup.js" defer></script>'


def configuration(root):
    config = json.loads((root / "settings/newsletter-form.json").read_text())
    if config["action"] != "https://www.aweber.com/scripts/addlead.pl":
        raise ValueError("Only the verified native AWeber action is supported")
    if config["hidden"]["listname"] != "awlist6985078" or config["hidden"]["meta_web_form_id"] != "70841443":
        raise ValueError("Unexpected form/list; verify a new native provider payload before changing")
    return config


def form(config, placement):
    prefix = "ws-main" if placement == "main" else "ws-foot"
    esc = lambda value: escape(value, quote=True)
    hidden = "".join('<input type="hidden" name="' + esc(name) + '" value="' + esc(value) + '">' for name, value in config["hidden"].items())
    return ('<form class="ws-foot-form" data-newsletter-signup="' + placement +
            '" method="post" accept-charset="UTF-8" action="' + esc(config["action"]) + '">' +
            hidden + '<label class="sr-only" for="' + prefix + '-email">Email address</label>' +
            '<div class="ws-foot-box"><input id="' + prefix + '-email" type="email" name="email"' +
            ' placeholder="Your email" autocomplete="email" required aria-describedby="' +
            prefix + '-message"><button type="submit">Subscribe</button></div>' +
            '<p class="ws-foot-msg" id="' + prefix + '-message" data-signup-message role="status" aria-live="polite"></p></form>')


def planned(root):
    config = configuration(root)
    changes = {}
    for path in sorted(root.rglob("*.html")):
        text = path.read_text()
        if not FORM.search(text) and not EO.search(text):
            continue
        def replace(match):
            placement = "main" if 'data-newsletter-signup="main"' in match[0] else "footer"
            return form(config, placement)
        text = FORM.sub(replace, text)
        text = EO.sub(lambda _: form(config, "main"), text)
        text = OLD_SCRIPT.sub(NEW_SCRIPT, text)
        if NEW_SCRIPT not in text:
            raise ValueError("Missing signup script boundary: " + str(path))
        if path.name in ("index.html", "archive.html") and path.parent == root:
            link = '<link rel="stylesheet" href="/email/signup.css">'
            if link not in text:
                text = text.replace("</head>", link + "</head>", 1)
        if text != path.read_text():
            changes[path] = text
    return changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    changes = planned(ROOT)
    for path, text in changes.items():
        print(("STALE " if args.check else "SYNC ") + str(path.relative_to(ROOT)))
        if not args.check:
            path.write_text(text)
    return int(args.check and bool(changes))


if __name__ == "__main__":
    raise SystemExit(main())
