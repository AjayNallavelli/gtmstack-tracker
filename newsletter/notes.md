
## 2026-10-20 daily check
- No real price changes today. ZoomInfo rewrote its pricing page copy (new product-line blurbs and a "Pay once. Re-pull it free for a year." line) with no plan prices published. Salesloft and Seamless.AI had minor wording tweaks.
- Findymail's pricing page was behind a Cloudflare bot check, so it's logged as a fetch failure, not a change.
- Scraper fix shipped: bot-check pages count as fetch failures, testimonial figures like "$4.9M in pipeline" are ignored, and diffs compare against the last good snapshot.

- 2026-10-22: Snov.io "price change" on Oct 21 ($39/$99 to $29.25/$74.25) was a false positive; the page showed annual-billing prices by default. Monthly is still $39/$99 (checked Oct 22). Reclassified as copy_change. If the scraper flags $39/$99 as "new" again, ignore it.
