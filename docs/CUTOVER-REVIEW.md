# AWeber and legal handoff — preparation only

## Provider change (not applied)

Authorized destination: separate World Skim AWeber account `2416451`, list
`6985078` (`awlist6985078`). The list number is **not** a webform ID.
No subscriber, subscription or vote was created during this work.

Current intake has two EmailOctopus script embeds (`index.html`, `archive.html`).
Inline footer handlers are duplicated across those pages, all eight dated
editions and `email/thanks.html`. They search `.emailoctopus-form`, queue the
email under `sessionStorage["ws-sub"]` and navigate to homepage signup when needed.
They currently display “Check your inbox to confirm” without verifying an actual
provider result. Changing only the embed is therefore insufficient.

Before a separate cutover commit, obtain the native AWeber webform payload for
the authorized list, verify its exact form ID, required hidden fields, success/
already-subscribed/error destinations, and actual confirmed-opt-in policy.
Replace both embeds and every footer handler together. Prefer routing footer
readers to the native form with honest completion wording over claiming a
subscription from a redirect or guessed DOM event. Do not put API credentials
in a static site or invent a form ID. Test with intercepted requests first;
any real subscription requires parent-owned authorization and execution.
Remove obsolete EmailOctopus selectors/queue behavior only in that cutover.

## Supported factual corrections for legal review (not public approval)

The public notices must not claim signup is disabled or the deployed site stores
nothing. Observed website source supports this replacement factual description:

> The site offers newsletter signup through an embedded form. It is hosted on
> GitHub Pages. Signup currently uses EmailOctopus; migration to AWeber is being
> prepared and has not yet changed the website. Trivia uses browser storage for
> results and streaks. Reader-poll confirmation stores an anonymous browser token
> for 30 days to limit repeat votes and sends the token, poll identifier and
> choice to a voting service after an explicit confirmation. No name or email is
> requested by that poll form. The footer signup flow temporarily carries a
> supplied email address in session storage when navigating to the main form.

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
3. AWeber form ID and confirmed-opt-in setting; subscription frequency, promotional
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

No legal HTML, provider, DNS, sending configuration or subscriber data is changed
by the archive synchronization commit.
