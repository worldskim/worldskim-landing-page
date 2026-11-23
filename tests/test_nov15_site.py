"""Nov15 exact source and scoped maintenance proof, with unmodified sync gates."""
from pathlib import Path
from bs4 import BeautifulSoup as BS
import copy,hashlib,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import sync_editions as sync,sync_signup as signup
from nov15_compat import restore_nov15,LEDGER
SOURCE=(ROOT/'docs/nov15-2026/approved-web-source.txt').read_text()
def sha(b):return hashlib.sha256(b).hexdigest()
class November15(unittest.TestCase):
 def test_immutable_source_and_full_editorial_design(self):
  self.assertEqual(sha(SOURCE.encode()),'f3091ff35feb78f6e7bceb81fe6ecfb6cc44ba22354206ae8ab6d53e1082e97b')
  self.assertEqual(sha((ROOT/'docs/nov15-2026/approved-content.json').read_bytes()),'b19661a05b64cb367ef6a8221ec64db33f6ecc6753548130431a4d8f8bfca546')
  from nov16_compat import restore_nov16
  a=BS(SOURCE,'html.parser');b=BS(restore_nov16((ROOT/'editions/2026-11-15.html').read_text(),'editions/2026-11-15.html'),'html.parser')
  for sel in ('style','article.story','#briefing','#deep-dive','#tri','#reader-poll','script','header'):
   self.assertEqual([str(x)for x in a.select(sel)],[str(x)for x in b.select(sel)],sel)
  for sel in ('nav.ed-nav','.more-grid','form'):b.select_one(sel).replace_with(copy.deepcopy(a.select_one(sel)))
  b.select_one('meta[property="og:image"]')['content']=a.select_one('meta[property="og:image"]')['content']
  for x in b.select('footer a[href]'):
   if x.get_text()in("Latest edition","Today's trivia"):x['href']=x['href'].replace('2026-11-15','2026-11-14')
  self.assertEqual(str(a),str(b))
 def test_exact_old_site_preservation_and_guards(self):
  for name,expected in LEDGER['base_hashes'].items():
   raw=(ROOT/name).read_bytes()
   if name.endswith('.html'):raw=restore_nov15(raw.decode(),name).encode()
   self.assertEqual(sha(raw),expected,name)
  for name,expected in LEDGER['guard_hashes'].items():self.assertEqual(sha((ROOT/name).read_bytes()),expected,name)
 def test_projection_rejects_undeclared_editorial_and_metadata(self):
  for name in LEDGER['pages']:
   raw=(ROOT/name).read_text();bad=raw.replace('<title>','<title>UNAPPROVED ',1)
   try:restored=restore_nov15(bad,name)
   except AssertionError:continue
   self.assertNotEqual(sha(restored.encode()),LEDGER['base_hashes'][name])
 def test_both_syncs_and_complete_current_inventory(self):
  self.assertEqual(sync.planned(ROOT),{});self.assertEqual(signup.planned(ROOT),{})
  entries=sync.read_config((ROOT/'index.html').read_text())['editions']
  self.assertEqual([e['url']for e in entries],[f'editions/2026-11-{n:02}.html'for n in range(23,0,-1)])
  self.assertEqual(entries[8]['image'],LEDGER['lead_photo'])
  for name,limit in [('index.html',6),('archive.html',23)]:
   d=BS((ROOT/name).read_text(),'html.parser');self.assertEqual(len(d.select('#edition-grid article.card')),limit)
   self.assertEqual(d.select_one('#edition-grid .card-link')['href'],'editions/2026-11-23.html')
 def test_reader_targets_and_metadata(self):
  d=BS((ROOT/'editions/2026-11-15.html').read_text(),'html.parser')
  self.assertEqual(d.select_one('link[rel=canonical]')['href'],'https://worldskim.com/editions/2026-11-15.html')
  self.assertEqual(d.select_one('meta[property="og:image"]')['content'],LEDGER['lead_photo'])
  self.assertEqual(d.select_one('nav.ed-nav a')['href'],'2026-11-14.html')
  self.assertEqual([x['href']for x in d.select('.more-grid a:not(.all)')],['2026-11-14.html','2026-11-13.html'])
  self.assertEqual(d.select_one('#tri')['data-answer'],'2')
  self.assertEqual(len(d.select('article.story')),3)
  for section in ('world-view','need-to-know','money-markets','future-frontiers','the-score','life-culture'):
   self.assertEqual(len(d.select(f'#{section} p.brief')),3,section)
