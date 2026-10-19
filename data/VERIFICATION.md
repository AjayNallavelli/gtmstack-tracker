# Pricing verification log (2026-10-19)

Every tool's pricing page was fetched on 2026-10-19 (plain HTTP or headless Chrome, plus a US-region web fetch where the box saw localized prices). Tiers in `data/tools.json` were transcribed from that page text. No prices were estimated.

Status: **public** = USD prices published and transcribed; **partial** = some tiers custom/localized/non-USD; **contact_sales** = no prices published (recorded as such).

| Tool | Category | Status | Pricing URL | Notes |
|---|---|---|---|---|
| 11x | AI SDR agents | contact_sales | https://www.11x.ai/ | 11x.ai/pricing returned HTTP 404 on 2026-10-19; homepage only offers a demo. |
| Artisan | AI SDR agents | contact_sales | https://www.artisan.co/pricing | Pricing page requires a call; no dollar figures published. |
| AiSDR | AI SDR agents | public | https://aisdr.com/pricing/ | Usage-based self-serve; add-ons: warmed-up mailbox $33 |
| Regie.ai | AI SDR agents | public | https://www.regie.ai/pricing | Monthly price shown; annual saves 17% |
| Reply.io | AI SDR agents | public | https://reply.io/pricing/ | Monthly vs annual both shown; LinkedIn automation $69/mo/acct, Calls & SMS $29/mo/acct add-ons |
| Amplemarket | AI SDR agents | partial | https://www.amplemarket.com/pricing | Annual term only shown |
| Persana AI | AI SDR agents | public | https://persana.ai/pricing | Prices shown billed annually (annual saves 20%); monthly prices not captured |
| Instantly | Cold email & engagement | public | https://instantly.ai/pricing | Monthly and annual both shown |
| Smartlead | Cold email & engagement | public | https://www.smartlead.ai/pricing | Monthly shown; annual Base $32, Pro $78; verified-prospect-email add-on $59/mo on Base/Pro |
| lemlist | Cold email & engagement | public | https://www.lemlist.com/pricing | Monthly vs annual (save 20%); data add-on $20/mo for 2k credits, intent signals $29/mo. lemwarm warmup is now bundled into lemlist plans (no |
| Apollo.io | Cold email & engagement | public | https://www.apollo.io/pricing | Pricing renders client-side; captured with headless Chrome. |
| Woodpecker | Cold email & engagement | partial | https://woodpecker.co/pricing/ | Box fetch showed INR; USD figures read via a US-region fetch. |
| Saleshandy | Cold email & engagement | public | https://www.saleshandy.com/pricing/ | Monthly vs annual (annual: $408/$912/$1,788 per year); taxes excluded |
| Mailshake | Cold email & engagement | public | https://mailshake.com/pricing/ | Monthly vs yearly; Data Finder add-on $19/mo, ready-to-use mailboxes $12/mo |
| Snov.io | Cold email & engagement | public | https://snov.io/pricing | Monthly; 25% off annual. LinkedIn slots $69/mo each |
| Klenty | Cold email & engagement | public | https://www.klenty.com/pricing/ | Billed annually (save up to 20%); Parallel & Power Dialer add-on $45/user/mo |
| La Growth Machine | Cold email & engagement | partial | https://lagrowthmachine.com/pricing/ | Prices published in EUR only |
| Outreach | Cold email & engagement | contact_sales | https://www.outreach.io/pricing |  |
| Salesloft | Cold email & engagement | contact_sales | https://www.salesloft.com/pricing |  |
| Clay | Data & enrichment | public | https://www.clay.com/pricing | Actions + data credits priced separately; data credits from $0.05 each |
| ZoomInfo | Data & enrichment | contact_sales | https://www.zoominfo.com/pricing |  |
| HubSpot Breeze Intelligence (Data Hub) | Data & enrichment | partial | https://www.hubspot.com/pricing/data | Clearbit was acquired by HubSpot and became Breeze Intelligence; enrichment now sold via Data Hub + HubSpot Credits. |
| Lusha | Data & enrichment | public | https://www.lusha.com/pricing/ | Billed yearly (credits upfront) |
| Cognism | Data & enrichment | contact_sales | https://www.cognism.com/pricing |  |
| Seamless.AI | Data & enrichment | contact_sales | https://seamless.ai/pricing |  |
| RocketReach | Data & enrichment | partial | https://rocketreach.co/pricing | Geo-localized pricing; USD per-plan prices not captured |
| Kaspr | Data & enrichment | public | https://www.kaspr.io/pricing | Monthly vs annual; also EUR/GBP |
| People Data Labs | Data & enrichment | public | https://www.peopledatalabs.com/pricing | Annual saves 20% |
| Hunter | Data & enrichment | public | https://hunter.io/pricing | Monthly vs yearly (save 30%) |
| FullEnrich | Data & enrichment | public | https://fullenrich.com/pricing | Credit slider; rollover 3 months (monthly) / 12 months (yearly) |
| Findymail | Data & enrichment | public | https://www.findymail.com/pricing/ | Plain HTTP fetch blocked (403); captured with headless Chrome. |
| Prospeo | Data & enrichment | public | https://prospeo.io/pricing | Page is client-rendered; captured via web fetch. |
| BetterContact | Data & enrichment | public | https://bettercontact.rocks/pricing/ | Monthly; annual = 2 months free |
| Allegrow | Deliverability & warmup | public | https://www.allegrow.co/pricing |  |
| Warmbox | Deliverability & warmup | public | https://www.warmbox.ai/pricing/ | Monthly vs yearly |
| MailReach | Deliverability & warmup | public | https://www.mailreach.co/pricing | Per-mailbox slider; annual saves 20% |
| Warmy | Deliverability & warmup | partial | https://www.warmy.io/pricing |  |
| GlockApps | Deliverability & warmup | public | https://glockapps.com/pricing/ | Annual (save 30%) figures shown |
| EmailGuard | Deliverability & warmup | public | https://emailguard.io/pricing |  |

Totals: 39 tools: 26 public, 6 partial, 7 contact-sales.
