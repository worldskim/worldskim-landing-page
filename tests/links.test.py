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
        assert [x['url'] for x in config['editions']] == ['editions/2026-11-06.html', 'editions/2026-11-03.html', 'editions/2026-11-02.html', 'editions/2026-11-01.html']
        for edition in config['editions']:
            assert (root/edition['url']).exists()
draft = (root/'editions/2026-11-06.html').read_text()
assert 'href="2026-11-03.html">← Previous edition' in draft
assert 'data-qz="2026-11-06"' in draft
assert 'eomail5.com/form/4273f0aa-d6f8-11f1-9638-4b187b7e1294.js' in (root/'index.html').read_text()
print(f'PASS: {checked} internal links/assets/anchors; latest/archive metadata; previous edition; dated trivia; unchanged EmailOctopus signup embed')
