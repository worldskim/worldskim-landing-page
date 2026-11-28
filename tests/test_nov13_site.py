"""Actual approved Nov13 archive insertion; newest Nov14 remains authoritative."""
from pathlib import Path
import copy,hashlib,json,re,sys,unittest
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import sync_editions as sync,sync_signup as signup
from nov13_compat import restore_nov13,LEDGER
DOC=ROOT/"docs/nov13-2026"
BASE=json.loads((DOC/"base-hashes.json").read_text())
SOURCE=(DOC/"approved-web-source.txt").read_text()
C=json.loads((DOC/"approved-content.json").read_text())["brands"]["worldskim"]
def digest(b):return hashlib.sha256(b).hexdigest()
def soup(s):return BeautifulSoup(s,"html.parser")
class Nov13(unittest.TestCase):
 def test_immutable_actual_approved_source_and_content(self):
  self.assertEqual(digest(SOURCE.encode()),"8d8a26f5c44dd0614d793ceaee4b76e4b051f7c5d7e832fc4c3e9e8fe51060cb")
  self.assertEqual(digest((DOC/"approved-content.json").read_bytes()),"87f38d1a7cc07a1a7da4754826e6dd8aede085b7830d0c08dcd398a086636a4b")
 def test_full_source_equality_except_approved_maintenance(self):
  source=soup(SOURCE);current=soup((ROOT/"editions/2026-11-13.html").read_text())
  for node in current.select('link[rel="canonical"],meta[property^="og:"]'):node.decompose()
  for selector in ("nav.ed-nav","form",".more-grid"):
   current.select_one(selector).replace_with(copy.deepcopy(source.select_one(selector)))
  for a in current.select("footer a[href]"):
   if a.get_text() in ("Latest edition","Today's trivia"):a["href"]=a["href"].replace("2026-11-28","2026-11-12").replace("2026-11-27","2026-11-12").replace("2026-11-26","2026-11-12").replace("2026-11-25","2026-11-12").replace("2026-11-24","2026-11-12").replace("2026-11-23","2026-11-12").replace("2026-11-22","2026-11-12").replace("2026-11-21","2026-11-12").replace("2026-11-20","2026-11-12").replace("2026-11-19","2026-11-12")
  self.assertEqual(str(current),str(source))
 def test_all_existing_html_and_fixed_assets_exact_preservation(self):
  for name,expected in BASE.items():
   if name.endswith(".html"):
    self.assertEqual(digest(restore_nov13((ROOT/name).read_text(),name).encode()),expected,name)
   elif not name.startswith("tests/"):
    self.assertEqual(digest((ROOT/name).read_bytes()),expected,name)
  for name in ("scripts/sync_editions.py","scripts/sync_signup.py","tests/archive_compat.py","tests/signup_compat.py","tests/retrospective_maintenance.json","tests/nov14_maintenance.json"):
   self.assertEqual(digest((ROOT/name).read_bytes()),BASE[name],name)
 def test_exact_projection_does_not_hide_unapproved_content(self):
  for name,pairs in LEDGER["pages"].items():
   for pair in pairs:
    raw=__import__("nov15_compat").restore_nov15((ROOT/name).read_text(),name).replace(pair["after"],pair["after"]+"UNAPPROVED",1)
    try: restored=restore_nov13(raw,name)
    except AssertionError: continue  # exact-boundary rejection is fail-closed
    self.assertNotEqual(digest(restored.encode()),BASE[name])
 def test_unchanged_syncs_full_inventory_and_current_nov14(self):
  self.assertEqual(sync.planned(ROOT),{});self.assertEqual(signup.planned(ROOT),{})
  entries=sync.read_config((ROOT/"index.html").read_text())["editions"]
  self.assertEqual([e["url"]for e in entries],[f"editions/2026-11-{n:02d}.html"for n in range(28,0,-1)])
  self.assertEqual(entries[15]["title"],C["title"].splitlines())
  self.assertEqual(entries[15]["image"],soup(SOURCE).select_one("article.story img")["src"])
  oldhome=soup(restore_nov13((ROOT/"index.html").read_text(),"index.html"));home=soup(__import__("nov15_compat").restore_nov15((ROOT/"index.html").read_text(),"index.html"))
  self.assertEqual(str(home.select_one(".switcher")),str(oldhome.select_one(".switcher")))
  for name in ("index.html","archive.html"):
   doc=soup((ROOT/name).read_text())
   self.assertEqual(len(doc.select("#edition-grid article.card")),6 if name=="index.html"else 28)
   self.assertEqual(doc.select_one('#edition-grid .card-link')["href"],"editions/2026-11-28.html")
   for a in doc.select("footer a[href]"):
    if a.get_text() in ("Latest edition","Today's trivia"):self.assertIn("2026-11-28.html",a["href"])
 def test_new_date_metadata_and_complete_chronology(self):
  doc=soup((ROOT/"editions/2026-11-13.html").read_text());base="https://worldskim.com/editions/2026-11-13.html"
  self.assertEqual(doc.select_one('link[rel="canonical"]')["href"],base)
  self.assertEqual(doc.select_one('meta[property="og:url"]')["content"],base)
  self.assertEqual(doc.select_one('meta[property="og:image"]')["content"],doc.select_one("article.story img")["src"])
  for date,expected in [("12",["2026-11-11.html","2026-11-13.html"]),("13",["2026-11-12.html","2026-11-14.html"])]:
   self.assertEqual([a["href"]for a in soup((ROOT/f"editions/2026-11-{date}.html").read_text()).select("nav.ed-nav a")],expected)
  self.assertEqual(soup((ROOT/"editions/2026-11-14.html").read_text()).select_one("nav.ed-nav a")["href"],"2026-11-13.html")
 def test_source_articles_briefs_deep_trivia_poll_styles_scripts_native_footer(self):
  doc=soup((ROOT/"editions/2026-11-13.html").read_text());source=soup(SOURCE)
  for selector in ("style","article.story","#briefing","#deep-dive","#tri","#reader-poll","script"):
   self.assertEqual([str(n)for n in doc.select(selector)],[str(n)for n in source.select(selector)],selector)
  self.assertEqual(str(doc.footer),str(soup((ROOT/"editions/2026-11-14.html").read_text()).footer))
  for selector in ("article.story","#deep-dive","#tri","#reader-poll","style","script","meta","header"):
   current14=soup((ROOT/"editions/2026-11-14.html").read_text())
   old14=soup(restore_nov13((ROOT/"editions/2026-11-14.html").read_text(),"editions/2026-11-14.html"))
   self.assertEqual([str(n)for n in current14.select(selector)],[str(n)for n in old14.select(selector)],selector)
if __name__=="__main__":unittest.main()
