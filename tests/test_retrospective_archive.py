"""Current archive repair guards. Offline only; never sends a vote or signup."""
import hashlib
import importlib.util
import json
import re
import unittest
from pathlib import Path
from urllib.parse import parse_qs, unquote, urljoin, urlsplit
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs/retrospective-2026-11-12"
CONTENTS = json.loads((DOCS / "content.json").read_text())
BASE = json.loads((DOCS / "base-preservation.json").read_text())
spec = importlib.util.spec_from_file_location("repair_sync", ROOT / "scripts/sync_editions.py")
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


def soup(text):
    return BeautifulSoup(text, "html.parser")


def digest(value):
    return hashlib.sha256(value).hexdigest()


def norm(text):
    return " ".join(text.split())


class RetrospectiveArchive(unittest.TestCase):
    def test_complete_12_day_archive_and_latest(self):
        entries = sync.inventory(ROOT, sync.read_config((ROOT / "index.html").read_text()))
        self.assertEqual([e["url"] for e in entries],
                         [f"editions/2026-11-{n:02d}.html" for n in range(12, 0, -1)])
        for name in ("index.html", "archive.html"):
            raw = (ROOT / name).read_text()
            self.assertEqual(sync.read_config(raw)["editions"], entries)
            ranges = sync.Ranges(raw)
            self.assertEqual(raw[slice(*ranges.grid)], "".join(sync.card(e) for e in entries[:ranges.limit] if True))
        self.assertEqual(sync.planned(ROOT), {})

    def test_exact_content_slots_sources_and_dates(self):
        for date, data in CONTENTS.items():
            with self.subTest(date=date):
                doc = soup((ROOT / "editions" / (date + ".html")).read_text())
                self.assertEqual(doc.title.get_text(), data["title"].replace("\n", " "))
                self.assertEqual(doc.select_one('meta[name="description"]')["content"], data["description"])
                self.assertEqual(doc.select_one('link[rel="canonical"]')["href"], f"https://worldskim.com/editions/{date}.html")
                self.assertEqual(doc.select_one('meta[property="og:url"]')["content"], f"https://worldskim.com/editions/{date}.html")
                self.assertEqual(doc.select_one(".eyebrow").get_text(), data["date_line"])
                self.assertEqual(doc.select_one("[data-archive-notice]").get_text(), data["notice"])
                self.assertIn("Added November 12, 2026.", data["notice"])
                self.assertIn("Archive Edition" if date.endswith("12") else "Retrospective Edition", data["notice"])
                self.assertEqual(doc.select_one("[data-cutoff-explanation]").get_text(), data["cutoff_explanation"])
                nodes = doc.select("article.story")
                self.assertEqual(len(nodes), 3)
                for node, story in zip(nodes + [doc.select_one("#deep-dive")], data["stories"] + [data["deep_dive"]]):
                    self.assertEqual(node.find("img")["src"], story["photo"]["image_url"].replace("q=85", "q=80"))
                    self.assertEqual(node.find("img")["alt"], story["photo"]["alt"])
                    self.assertLess(len(story["photo"]["alt"].split()), 10)
                    self.assertLess(len(story["title"]), 90)
                    paragraphs = node.find_all("p", recursive=False)
                    paragraphs = [p for p in paragraphs if "kicker" not in p.get("class", [])]
                    self.assertEqual(len(paragraphs), len(story["paragraphs"]))
                    for actual, expected in zip(paragraphs, story["paragraphs"]):
                        fragment = soup(expected)
                        self.assertEqual(norm(actual.get_text(" ", strip=True)), norm(fragment.get_text(" ", strip=True)))
                        for a in fragment.select("a[href]"):
                            self.assertIsNotNone(actual.find("a", href=a["href"]))
                        words = len(fragment.get_text(" ", strip=True).split())
                        self.assertTrue((50 if story is data["deep_dive"] else 40) <= words <= 70)
                ids = ["world-view", "need-to-know", "money-markets", "future-frontiers", "the-score", "life-culture"]
                for section_id, items in zip(ids, data["briefing"].values()):
                    section = doc.find(id=section_id)
                    self.assertIsNotNone(section, section_id)
                    self.assertEqual(len(section.select("p.brief")), 3)
                    self.assertEqual([norm(p.get_text(" ", strip=True)) for p in section.select("p.brief")],
                                     [norm(soup(p).get_text(" ", strip=True)) for p in items])

    def test_trivia_poll_and_shares_are_correct_and_unregistered(self):
        for date, data in CONTENTS.items():
            doc = soup((ROOT / "editions" / (date + ".html")).read_text())
            trivia = doc.select_one("#tri")
            self.assertEqual(trivia["data-qz"], date)
            self.assertEqual(trivia["data-answer"], str("ABCD".index(data["trivia"]["correct_letter"])))
            self.assertEqual([x.get_text() for x in trivia.select(".qz-key")], list("ABCD"))
            self.assertEqual(len(trivia.select(".qz-opt")), 4)
            poll = doc.select_one("#reader-poll")
            self.assertIn(data["poll"]["question"], poll.get_text())
            self.assertFalse(data["poll"]["registered"])
            self.assertEqual(data["poll"]["duration_days"], 7)
            self.assertEqual(data["poll"]["opens_at"], "PARENT_SET_ACTUAL_PUBLICATION_TIME")
            self.assertEqual({parse_qs(urlsplit(a["href"]).query)["vote"][0] for a in poll.select("a[href]")}, {"yes", "no"})
            for a in poll.select("a[href]"):
                self.assertEqual(parse_qs(urlsplit(a["href"]).query)["poll"], [data["poll"]["slug"]])
            for a in doc.select(".share a[href]"):
                flat = unquote(a["href"])
                if "worldskim.com/editions/" in flat:
                    self.assertIn(f"worldskim.com/editions/{date}.html", flat)
                    self.assertNotIn("2026-11-10.html", flat)

    def test_no_duplicate_photos_or_topics(self):
        photos = [urlsplit(slot["photo"]["image_url"]).path for data in CONTENTS.values() for slot in data["stories"] + [data["deep_dive"]]]
        self.assertEqual(len(photos), len(set(photos)))
        topics = [slot["topic"] for data in CONTENTS.values() for slot in data["stories"] + [data["deep_dive"]]]
        self.assertEqual(len(topics), len(set(topics)))
        for name in BASE["files"]:
            if re.fullmatch(r"editions/\d{4}-\d{2}-\d{2}\.html", name):
                old = soup((ROOT / name).read_text())
                ids = [urlsplit(i["src"]).path for i in old.select("img[src]") if "images.unsplash.com" in i["src"]]
                self.assertFalse(set(ids) & set(photos), name)

    def test_all_internal_links_anchors_and_chronological_new_navigation(self):
        pages = {p.resolve(): soup(p.read_text()) for p in ROOT.rglob("*.html")}
        for path, doc in pages.items():
            for node in doc.select("[href],[src]"):
                raw = node.get("href", node.get("src", ""))
                if raw == "{!remove_web}":
                    continue
                url = urlsplit(urljoin("https://worldskim.com/" + path.relative_to(ROOT).as_posix(), raw))
                if url.scheme != "https" or url.hostname != "worldskim.com":
                    continue
                target = ROOT / unquote(url.path).lstrip("/")
                if target.is_dir():
                    target /= "index.html"
                self.assertTrue(target.is_file(), (str(path), raw))
                if url.fragment and target.resolve() in pages:
                    self.assertIsNotNone(pages[target.resolve()].find(id=unquote(url.fragment)), (str(path), raw))
        for date in CONTENTS:
            import datetime as dt
            previous = (dt.date.fromisoformat(date) - dt.timedelta(days=1)).isoformat()
            doc = pages[(ROOT / "editions" / (date + ".html")).resolve()]
            self.assertEqual(doc.select_one("nav.ed-nav a")["href"], previous + ".html")

    def test_existing_editions_only_exact_shared_link_maintenance(self):
        # Normalize only hrefs expressly owned by the unchanged synchronizer.
        for name, expected in BASE["files"].items():
            if name.startswith("editions/") and name.endswith(".html"):
                raw = (ROOT / name).read_text()
                restored = sync.shared_latest(raw, BASE["baseline_latest"])
                self.assertEqual(digest(restored.encode()), expected, name)

    def test_design_signup_collectors_and_fixed_files_preserved(self):
        baseline = soup((ROOT / "editions/2026-11-10.html").read_text())
        for date in CONTENTS:
            doc = soup((ROOT / "editions" / (date + ".html")).read_text())
            for selector in ("style", "header", "form", "script", 'link[rel="stylesheet"]'):
                self.assertEqual([str(n) for n in doc.select(selector)], [str(n) for n in baseline.select(selector)], (date, selector))
            self.assertEqual(str(doc.footer), str(baseline.footer), date)
        for name, expected in BASE["files"].items():
            if name.startswith(("scripts/", "settings/", "email/")) and not name.endswith(".html"):
                self.assertEqual(digest((ROOT / name).read_bytes()), expected, name)
        configuration = json.loads((ROOT / "settings/newsletter-form.json").read_text())
        self.assertIn("70841443", json.dumps(configuration))
        self.assertIn("awlist6985078", json.dumps(configuration))

    def test_exact_maintenance_projection_preserves_all_other_base_bytes(self):
        from retrospective_compat import restore_maintenance
        for name, expected in BASE["files"].items():
            if not name.endswith(".html"):
                continue
            current = (ROOT / name).read_text()
            self.assertEqual(digest(restore_maintenance(current, name).encode()), expected, name)
        for name in ("index.html", "archive.html"):
            current = (ROOT / name).read_text()
            with self.assertRaises(AssertionError):
                restore_maintenance(current.replace("Gibran", "Unexpected changed copy", 1), name)

    def test_reader_copy_sentence_lengths_and_no_em_dashes(self):
        for date, data in CONTENTS.items():
            labels = [soup(p).strong.get_text() for p in data["deep_dive"]["paragraphs"]]
            self.assertEqual(labels, ["What happened.", "Why it matters.", "What each side says.", "What comes next."])
            brief_copy = " ".join(p for items in data["briefing"].values() for p in items)
            for damaged in ("A british", "reaches london", "The guardian remembers",
                            "călin georgescu", "Mps criticise", "senate approval"):
                self.assertNotIn(damaged, brief_copy, (date, damaged))
            if date == "2026-11-11":
                self.assertIn("the summit seeks progress despite wars, inflation", data["stories"][1]["paragraphs"][0])
                self.assertNotIn("leaders of Brazil and Turkey urged cooperation", data["stories"][1]["paragraphs"][0])
            prose = [p for slot in data["stories"] + [data["deep_dive"]] for p in slot["paragraphs"]]
            prose += [p for items in data["briefing"].values() for p in items]
            for html in prose:
                text = soup(html).get_text(" ", strip=True).replace("U.S.", "US").replace("U.N.", "UN")
                self.assertNotIn("—", text)
                text = re.sub(r"^(What happened|Why it matters|What officials say|What prosecutors say|What each side says|What comes next)\.\s*", "", text, flags=re.I)
                sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z])", text)
                self.assertTrue(all(len(s.split()) < 25 for s in sentences), (date, text, [len(s.split()) for s in sentences]))
                if html in prose[:10]:
                    self.assertLessEqual(len(sentences), 4, (date, text))


if __name__ == "__main__":
    unittest.main(verbosity=2)
