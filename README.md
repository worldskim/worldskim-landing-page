# Website maintenance

The repository is a static GitHub Pages site. `index.html`'s existing
`SITE_CONFIG.editions` is the publisher-maintained card metadata, ordered newest
first. It must include each approved `editions/YYYY-MM-DD.html` file exactly once.
No edition date or news copy is inferred from today's date.

After staging an approved edition and updating that metadata:

```sh
python3 scripts/sync_editions.py
python3 scripts/sync_editions.py --check
python3 -m unittest discover -s tests -p test_archive_sync.py
python3 tests/links.test.py
node tests/trivia.test.cjs
PLAYWRIGHT_MODULE=/path/to/playwright node tests/polls.browser.test.cjs
```

The synchronizer uses the existing card markup and classes. It writes the same
metadata into the archive, renders the homepage's configured card limit and the
complete archive even without JavaScript, and updates explicitly labelled shared
Latest edition / Today's trivia links on all pages. It fails closed if an edition
file has no approved metadata, if there are duplicates, or if ordering is wrong.
It does not change editorial content, story sources, dates, Previous/Next
navigation, polls, trivia, styles, logos, signup configuration or legal notices.
Run `--check` as a release gate; no build automation exists in this repository.

Historical `test_nov*_site.py` suites contain frozen, date-specific release scope
and exact-file hashes. They already had seven failures on main at `5e9a450`;
intentional shared-footer updates also conflict with those historical snapshots.
Do not rewrite editorial baselines merely to hide this. Use the current inventory
test and review the limited footer-only historical diff.
