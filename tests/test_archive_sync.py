"""Current, repeatable inventory checks, independent of one release's snapshots."""
from html.parser import HTMLParser
import importlib.util
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sync_editions", ROOT / "scripts/sync_editions.py")
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class Links(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.hrefs = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.hrefs.append(dict(attrs).get("href"))


class ArchiveSync(unittest.TestCase):
    def test_frozen_hash_compatibility_is_limited_to_shared_hrefs(self):
        from archive_compat import restore_shared
        text = (ROOT / "editions/2026-11-01.html").read_text()
        restored = restore_shared(text, "editions/2026-11-01.html")
        self.assertNotEqual(text, restored)
        # A different story word is not normalized away.
        changed = text.replace("<title>", "<title>Unexpected editorial change ", 1)
        self.assertNotEqual(restore_shared(changed, "editions/2026-11-01.html"), restored)
        # A made-up destination is rejected, not treated as a shared-link update.
        latest = "/" + sync.read_config((ROOT / "index.html").read_text())["editions"][0]["url"]
        with self.assertRaises(AssertionError):
            restore_shared(text.replace('href="' + latest + '"', 'href="/wrong.html"', 1),
                           "editions/2026-11-01.html")

    def test_baseline_design_editorial_forms_and_legal_preserved(self):
        manifest = json.loads((ROOT / "tests/archive_preservation.json").read_text())
        self.assertEqual(manifest["baseline"], "5e9a4508ef2befc9675e94003d8cec76ffc1ef7c")
        for name, expected in manifest["files"].items():
            path = ROOT / name
            data = path.read_bytes()
            if path.suffix == ".html":
                from retrospective_compat import restore_maintenance
                text = restore_maintenance(data.decode(), name)
                if (ROOT / "tests/signup_baseline.json").exists():
                    from signup_compat import restore_signup
                    text = restore_signup(text, name)
                if name in ("index.html", "archive.html"):
                    ranges = sync.Ranges(text)
                    start, end = ranges.grid
                    text = text[:start] + "<STATIC_CARDS>" + text[end:]
                # Only named shared hrefs may differ on historical pages.
                text = sync.shared_latest(text, "editions/2000-01-01.html")
                data = text.encode()
            self.assertEqual(hashlib.sha256(data).hexdigest(), expected, name)

    def test_current_source_is_synchronized(self):
        self.assertEqual(sync.planned(ROOT), {})

    def test_static_cards_equal_complete_inventory_and_home_limit(self):
        entries = sync.inventory(ROOT, sync.read_config((ROOT / "index.html").read_text()))
        for name in ("index.html", "archive.html"):
            text = (ROOT / name).read_text()
            ranges = sync.Ranges(text)
            start, end = ranges.grid
            expected = entries[:ranges.limit] if ranges.limit else entries
            self.assertEqual(Links(text[start:end]).hrefs, [e["url"] for e in expected])
            self.assertEqual(text[start:end], "".join(sync.card(e) for e in expected))
            self.assertEqual(sync.read_config(text)["editions"], entries)

    def test_shared_latest_and_trivia_everywhere(self):
        latest = sync.read_config((ROOT / "index.html").read_text())["editions"][0]["url"]
        for path in ROOT.rglob("*.html"):
            text = path.read_text()
            self.assertEqual(text, sync.shared_latest(text, latest), str(path))

    def test_generator_future_inventory_and_preserves_editorial(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in ("index.html", "archive.html", "editions", "email"):
                source = ROOT / name
                if source.is_dir():
                    shutil.copytree(source, root / name)
                else:
                    shutil.copy(source, root / name)
            # A real new file without approved card metadata must fail closed.
            newest = sync.read_config((root / "index.html").read_text())["editions"][0]
            future = dict(newest, url="editions/2099-01-01.html", date="Thursday, January 1, 2099")
            (root / future["url"]).write_text((root / newest["url"]).read_text())
            with self.assertRaisesRegex(ValueError, "every dated edition"):
                sync.planned(root)
            p = root / "index.html"
            original = p.read_text()
            config = sync.read_config(original)
            config["editions"].insert(0, future)
            import json
            match = sync.CONFIG.search(original)
            p.write_text(original[:match.start(2)] + json.dumps(config) + original[match.end(2):])
            before = {p: p.read_text() for p in (root / "editions").glob("*.html")}
            for path, text in sync.planned(root).items():
                path.write_text(text)
            self.assertEqual(sync.planned(root), {})
            for path, text in before.items():
                self.assertEqual(path.read_text(), sync.shared_latest(text, future["url"]))
            archive = (root / "archive.html").read_text()
            ranges = sync.Ranges(archive)
            self.assertEqual(Links(archive[slice(*ranges.grid)]).hrefs[0], future["url"])

    def test_escaping_and_no_historical_navigation_rewrite(self):
        text = '<a href="2026-11-01.html">← Previous edition</a><a href="/editions/2026-11-01.html">Latest edition</a>'
        changed = sync.shared_latest(text, "editions/2099-01-01.html")
        self.assertIn('href="2026-11-01.html">← Previous edition', changed)
        entry = dict(url="editions/2099-01-01.html", title=['<script>"&'], image='https://example.test/?a=1&b="',
                     date="date", readingTime="6 min read", description="<b>not HTML</b>")
        rendered = sync.card(entry)
        self.assertNotIn("<script>", rendered)
        self.assertIn("&lt;b&gt;not HTML&lt;/b&gt;", rendered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
