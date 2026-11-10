from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json, re

root = Path('.').resolve()
class Page(HTMLParser):
    def __init__(self, path):
        super().__init__()
        self.ids, self.links = set(), []
        self.feed(path.read_text())
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.add(a['id'])
        for k in ('href', 'src'):
            if a.get(k): self.links.append(a[k])

pages = {p.resolve(): Page(p) for p in root.rglob('*.html')}
checked = 0
for name in ['index.html', 'archive.html', 'editions/2026-11-06.html']:
    path = (root/name).resolve()
    page = pages[path]
    for link in page.links:
        url = urlsplit(link)
        if url.scheme or url.netloc: continue
        target = ((root / url.path.lstrip('/')) if url.path.startswith('/') else path.parent/url.path).resolve() if url.path else path
        if target.is_dir(): target /= 'index.html'
        assert target.exists(), (name, link, 'missing destination')
        if url.fragment and target in pages:
            assert unquote(url.fragment) in pages[target].ids, (name, link, 'missing anchor')
        checked += 1
    if name != 'editions/2026-11-06.html':
        config = json.loads(re.search(r'var SITE_CONFIG=(.*?);', path.read_text()).group(1))
        assert [x['url'] for x in config['editions']] == ['editions/2026-11-10.html', 'editions/2026-11-09.html', 'editions/2026-11-08.html', 'editions/2026-11-07.html', 'editions/2026-11-06.html', 'editions/2026-11-03.html', 'editions/2026-11-02.html', 'editions/2026-11-01.html']
        for edition in config['editions']:
            assert (root/edition['url']).exists()
draft = (root/'editions/2026-11-06.html').read_text()
assert 'href="2026-11-03.html">← Previous edition' in draft
assert 'data-qz="2026-11-06"' in draft
assert 'https://www.aweber.com/scripts/addlead.pl' in (root/'index.html').read_text()
print(f'PASS: {checked} internal links/assets/anchors; latest/archive metadata; previous edition; dated trivia; verified native AWeber signup action')

# Every dated share control uses this edition URL and current approved title.
from html import unescape
from urllib.parse import parse_qs
current_title = unescape(re.search(r"<title>(.*?)</title>", draft).group(1))
current_url = "https://worldskim.com/editions/2026-11-06.html"
share_links = [link for link in pages[(root/"editions/2026-11-06.html").resolve()].links
               if any(marker in link for marker in ("mailto:?subject=", "facebook.com/sharer/", "twitter.com/intent/", "threads.net/intent/", "linkedin.com/sharing/", "reddit.com/submit", "wa.me/?"))]
assert len(share_links) == 9
for link in share_links:
    query = parse_qs(urlsplit(link).query)
    flat = " ".join(value for values in query.values() for value in values)
    assert current_url in flat, (link, "stale share URL")
    assert "2026-11-03" not in flat and "America votes." not in flat, (link, "stale sharing metadata")
    if "text" in query or "title" in query or (link.startswith("mailto:") and query.get("subject", [""])[0] != "You should read World Skim"):
        assert current_title in flat, (link, "current title absent")
print("PASS: all 9 share controls use current Nov6 URL; edition-sharing text uses exact current Title Case title")
