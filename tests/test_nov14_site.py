"""Nov14 exact source, current inventory, and full base preservation guards."""
from pathlib import Path
import hashlib,json,re,sys,unittest,copy
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
import sync_editions as sync
import sync_signup as signup
from nov14_compat import restore_nov14,LEDGER
DOC=ROOT/"docs/nov14-2026"
BASE=json.loads((DOC/"base-hashes.json").read_text())
SOURCE=(DOC/"approved-web-source.txt").read_text()
C=json.loads((DOC/"approved-content.json").read_text())["brands"]["worldskim"]
def digest(b):return hashlib.sha256(b).hexdigest()
def soup(s):return BeautifulSoup(s,"html.parser")
class Nov14(unittest.TestCase):
 def test_immutable_approved_source_and_content(self):
  self.assertEqual(digest(SOURCE.encode()),"86f39c3307678203a8bc92ef600749d96549e7afc1b263069e72dfe7e7b12262")
  self.assertEqual(digest((DOC/"approved-content.json").read_bytes()),"17c2014d2e145eb7d3764a1ddd68901b09f08552087d5dc5d2c76373b6dfcc43")
 def test_full_source_equality_except_approved_maintenance(self):
  source=soup(SOURCE);current=soup((ROOT/"editions/2026-11-14.html").read_text())
  # Metadata was absent in the reviewed source; no story text is corrected.
  for node in current.select('link[rel="canonical"],meta[property^="og:"]'):node.decompose()
  current.select_one("nav.ed-nav").replace_with(copy.deepcopy(source.select_one("nav.ed-nav")))
  # Serializer canonicalization changes native form spelling only. Protocol
  # equivalence and full existing native footer are checked independently.
  current.form.replace_with(copy.deepcopy(source.form))
  current.select_one(".more-grid").replace_with(copy.deepcopy(source.select_one(".more-grid")))
  for a in current.select("footer a[href]"):
   if a.get_text() in ("Latest edition","Today's trivia"):a["href"]=a["href"].replace("2026-11-14","2026-11-12")
  self.assertEqual(str(current),str(source))
 def test_all_base_pages_bytes_preserved_except_exact_maintenance(self):
  for name,expected in BASE.items():
   if name.endswith(".html"):
    self.assertEqual(digest(restore_nov14((ROOT/name).read_text(),name).encode()),expected,name)
   elif not name.startswith("tests/"):
    self.assertEqual(digest((ROOT/name).read_bytes()),expected,name)
  # No new bypass, signup/edition sync or original safeguard rewrite.
  for name in ("scripts/sync_editions.py","scripts/sync_signup.py","tests/archive_compat.py","tests/signup_compat.py"):
   self.assertEqual(digest((ROOT/name).read_bytes()),BASE[name],name)
 def test_projection_rejects_unapproved_mutations(self):
  from nov13_compat import restore_nov13
  from nov14_compat import restore_nov14_ledger
  for name,pairs in LEDGER["pages"].items():
   for pair in pairs:
    raw=restore_nov13((ROOT/name).read_text(),name)
    # Change one byte inside an explicitly maintained owner boundary.
    raw=raw.replace(pair["after"],pair["after"]+"UNAPPROVED",1)
    restored=restore_nov14_ledger(raw,name)
    self.assertNotEqual(digest(restored.encode()),BASE[name])
 def test_both_unchanged_synchronizers_and_approved_nov13(self):
  self.assertEqual(sync.planned(ROOT),{})
  self.assertEqual(signup.planned(ROOT),{})
  self.assertTrue((ROOT/"editions/2026-11-13.html").exists())
  self.assertEqual(len(list((ROOT/"editions").glob("????-??-??.html"))),14)
 def test_current_cards_switcher_metadata_and_chronology(self):
  doc=soup((ROOT/"editions/2026-11-14.html").read_text());lead=doc.select_one("article.story img")["src"]
  base="https://worldskim.com/editions/2026-11-14.html"
  self.assertEqual(doc.select_one('link[rel="canonical"]')["href"],base)
  self.assertEqual(doc.select_one('meta[property="og:url"]')["content"],base)
  self.assertEqual(doc.select_one('meta[property="og:image"]')["content"],lead)
  for name,limit in (("index.html",6),("archive.html",14)):
   raw=(ROOT/name).read_text();home=soup(raw);entries=sync.read_config(raw)["editions"]
   self.assertEqual(entries[0]["title"],C["title"].splitlines())
   self.assertEqual(entries[0]["image"],lead)
   self.assertEqual(len(home.select("#edition-grid article.card")),limit)
  home=soup((ROOT/"index.html").read_text())
  self.assertEqual(json.loads(home.select_one(".switcher")["data-items"]),
   [[s["title"],f"editions/2026-11-14.html#s{i}"]for i,s in enumerate(C["stories"],1)])
  self.assertEqual([a["href"] for a in doc.select(".more-grid a:not(.all)")],["2026-11-13.html","2026-11-12.html"])
  self.assertEqual(doc.select_one("nav.ed-nav a")["href"],"2026-11-13.html")
  self.assertIsNotNone(soup((ROOT/"editions/2026-11-13.html").read_text()).select_one('nav.ed-nav a[href="2026-11-14.html"]'))
 def test_native_signup_footer_and_all_source_slots(self):
  doc=soup((ROOT/"editions/2026-11-14.html").read_text());old=soup((ROOT/"editions/2026-11-12.html").read_text())
  self.assertEqual(str(doc.footer),str(old.footer))
  self.assertEqual(str(doc.header),str(old.header))
  source=soup(SOURCE)
  for selector in ("style","article.story","#briefing","#deep-dive","#tri","#reader-poll","script"):
   self.assertEqual([str(n)for n in doc.select(selector)],[str(n)for n in source.select(selector)],selector)
if __name__=="__main__":unittest.main()
