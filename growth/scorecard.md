# GTMStack scorecard (targets due 2026-12-21)

Targets: first affiliate dollar; 1,000 organic visits/month; 100 newsletter subscribers.

| Date | GSC clicks | GSC impressions | Avg pos | Subscribers | Affiliate status | Notes |
|---|---|---|---|---|---|---|
| 2026-10-22 | 0 | 43 | 7.5 | 1 (as of Oct 20) | Klenty, Woodpecker, Prospeo approved; FullEnrich, Saleshandy, Hunter pending; $0 earned | GSC data only covers Oct 18-19 so far. Top queries: "intent data platform europe b2b" (3), "peopledatalabs" (3), "smartlead" (1). Sitemap still "Couldn't fetch", resubmitted. |
| 2026-10-29 | 0 | 49 | 31.4 | not in brief | $0 earned; affiliate_click 0 | Site Coach, GSC Oct 20-26: 5 pages indexed. Top queries: "clay pricing" (11), "apollo.io" (2); Clay cluster = 14 of 49 impressions. Top pages: /tools/clay/ (34), /alternatives/apollo/ (9). Sitemap still "Couldn't fetch". GA4 Oct 22-28: 1 user, 4 sessions, all Direct (us); affiliate_click 0, newsletter_signup_click 0. |

## Weekly growth pushes
- 2026-10-22: added 3 affiliate comparison pages (commit b502254, deploy green): /compare/snovio-vs-prospeo/, /compare/rocketreach-vs-prospeo/, /compare/saleshandy-vs-klenty/. No real price changes this week, so no IH/Reddit data post, no launch site, no Index.
- Oct 26: GA4 live (G-H8BKQMPMQ6, property 560764427); affiliate_click events tracked.
- 2026-10-29: polished affiliate pages: compare pages with Klenty/Woodpecker/Prospeo now show a "Try X" affiliate CTA under the lead, and every tool and compare page has a tool-named price-change alert signup box. Published the open pricing CSV (CC BY 4.0, /data/pricing.csv, footer link, README). No real price changes this week, so no IH/Reddit data post, launch site or Index. Site Coach brief and RedReplier threads requested; numbers to be recorded when they arrive.

- 2026-10-29 (Site Coach fixes): checked live links (68 home hrefs + nav/footer + /best/, /compare/ all 200 under /gtmstack-tracker/; nothing broken). Headless test of the live tag: page_view sends the full URL incl. /gtmstack-tracker/, and affiliate_click / newsletter_signup_click fire on rel="sponsored" and beehiiv links, so no client-side path stripping or selector bug. Clay page: title/H1 "Clay pricing 2026", plan table moved right under the hero, FAQ led by "How much is Clay?" + credits question (FAQPage JSON-LD), linked from home ("Most searched") and every compare page ("Full plan tables").
