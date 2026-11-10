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
and exact-file hashes. They already had seven failures on main at `5e9a450`.
`archive_compat.py` restores only explicitly labelled shared footer destinations
to their pinned pre-maintenance values for old hash comparisons; the current
inventory suite checks the actual latest destinations separately. All editorial,
style, script, form and Previous/Next navigation bytes remain checked. The seven
unrelated pre-existing frozen-release failures are not skipped or hidden.

## Native newsletter forms

The separate intake change uses provider-generated AWeber form `70841443` for
World Skim account `2416451`, list `6985078`. Its public, non-secret protocol is
stored in `settings/newsletter-form.json`. Every signup is a native HTML POST;
the provider's response is authoritative, not a local success message.

```sh
python3 scripts/sync_signup.py --check
python3 -m unittest discover -s tests -p test_signup.py
PLAYWRIGHT_MODULE=/path/to/playwright node tests/signup.browser.test.cjs
```

Run the synchronizer without `--check` after introducing a reviewed page to keep
its footer form consistent. The browser suite intercepts all form submissions
and does not subscribe anyone. `signup_compat.py` restores only exact approved
signup markup/script boundaries for historical snapshots; `test_signup.py`
checks every generated form and hashes the rest of each page against the pinned
pre-intake source. Legal review decisions remain in `docs/CUTOVER-REVIEW.md`.
