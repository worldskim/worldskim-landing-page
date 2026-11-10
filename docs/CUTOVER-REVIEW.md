# AWeber and legal handoff — preparation only

## Provider change (local candidate; parent publishes)

Authorized destination: separate World Skim AWeber account `2416451`, list
`6985078` (`awlist6985078`). The list number is **not** a webform ID.
No subscriber, subscription or vote was created during this work.

Before this candidate, intake had two EmailOctopus script embeds (`index.html`, `archive.html`).
Inline footer handlers were duplicated across those pages, all eight dated
editions and `email/thanks.html`. They search `.emailoctopus-form`, queue the
email under `sessionStorage["ws-sub"]` and navigate to homepage signup when needed.
They displayed “Check your inbox to confirm” without verifying an actual
provider result. Changing only the embed is therefore insufficient.

The parent supplied native provider-generated form `70841443` for this account/
list. `settings/newsletter-form.json` preserves all nine hidden fields from that
payload, including `redirect` and `meta_redirect_onlist` pointing to the provider's
`https://www.aweber.com/thankyou-coi.htm?m=text`. All thirteen forms now use a
native POST to `https://www.aweber.com/scripts/addlead.pl`, without XHR, local
success claims, EmailOctopus scripts/selectors, address queues or automatic
submission. Provider CSS/display-tracking pixel were omitted; original site
form styling is retained. Email-only validation works without JavaScript; the
small shared script adds accessible invalid-email feedback only.

`scripts/sync_signup.py --check` validates generated form consistency. Mocked
browser tests cover all thirteen forms both with and without JavaScript, exact
POST payload, validation, provider destination/failure, and no automatic writes.
They are not evidence of a real subscriber being accepted, email delivery,
confirmation settings or DNS readiness. No API credential is in the site.

## Supported factual corrections for legal review (not public approval)

The public notices must not claim signup is disabled or the deployed site stores
nothing. Observed website source supports this replacement factual description:

> The site offers newsletter signup and is hosted on GitHub Pages. The prepared
> website change sends signup email addresses directly to AWeber through its
> native form. Trivia uses browser storage for
> results and streaks. Reader-poll confirmation stores an anonymous browser token
> for 30 days to limit repeat votes and sends the token, poll identifier and
> choice to a voting service after an explicit confirmation. No name or email is
> requested by that poll form. The prepared signup change does not store or
> automatically forward signup email addresses through browser storage.

This is proposed factual wording, not an approved complete privacy notice.
Change provider/queue descriptions again when the actual cutover is verified.
Do not remove draft banners and imply legal approval. The disclosures page is
also a review draft; no compensation, ownership, independence or AI-use claims
have been supplied that justify replacing it with final boilerplate.

## Exact decisions/evidence still needed

1. Legal operator/data controller's registered name, business address, approved
   privacy/corrections contact; confirm `hello@worldskim.com` is monitored and by
   whom. Publication brand or account owner is not enough.
2. Approved effective date and legal reviewer signoff; jurisdictions served,
   minimum age, legal bases, mandatory rights/request verification, deadlines,
   appeals/regulator contact, governing law and any acceptance mechanism.
3. Actual AWeber confirmed-opt-in setting (form ID is now verified); subscription frequency, promotional
   scope, cancellation/unsubscribe process, all signup fields, consent/source/IP
   records, open/click tracking and any partner enrollment.
4. Actual vendor roles, processing locations and transfer safeguards for hosting,
   AWeber, mailbox, image delivery and Convex poll collection. Existing notices
   omit the anonymous-token voting backend.
5. Backend poll record retention/deletion, access/security owners and abuse
   policy. Thirty days is the frontend token lifetime, **not** proof backend
   records are deleted after thirty days. Trivia storage has no stated expiration.
6. Subscriber/contact/consent/engagement/suppression/backups retention, security
   practices and fulfillment of access/deletion/opt-out requests.
7. Any analytics, cookies/pixels or email-provider tracking and consent controls,
   sharing/sale/co-registration/targeted advertising, sponsors/affiliate payments.
   Do not promise “never sell/share” without confirmed practices.
8. Editorial corrections, actual AI/editorial workflow and photo/content license
   review; no source-link fact check or photo-rights audit is implied here.

No legal HTML, DNS, sending configuration or subscriber data is changed by this
candidate. Provider intake changes are isolated from the already merged archive
commit and still require parent-owned publication.
