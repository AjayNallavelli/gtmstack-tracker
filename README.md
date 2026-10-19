# GTMStack Tracker (v1)

GTMStack Tracker is a static website that lists AI sales and outbound tools (AI SDR agents, cold email, data and enrichment, deliverability and warmup). For each tool it keeps the current price plus a dated history of pricing and plan changes and a "What changed" feed. Competing directories only show today's price.

## Layout

```
data/tools.json           # the dataset: 39 tools, tiers, pricing URLs, affiliate_url (blank)
data/VERIFICATION.md      # per-tool verification status (public / partial / contact_sales)
data/snapshots/YYYY-MM-DD # daily raw text (.txt) + extracted pricing lines/price points (.json)
data/changes.json         # change log produced by the diff (feeds /changes/ and RSS)
scripts/snapshot.py       # fetch -> normalize -> snapshot -> diff  (daily job)
scripts/build.py          # Jinja2 static site generator -> dist/
scripts/check_links.py    # internal link checker + rel=sponsored check for affiliate links
scripts/seed_tools.py     # one-time seed used to create tools.json (do NOT re-run; it overwrites)
templates/, static/       # HTML templates and CSS; static/root/* is copied verbatim to the site root (Search Console file) (no JS framework; ~2 KB inline JS for filters)
newsletter/issue-001.md   # draft of the first newsletter issue (not sent)
site.json                 # site name, base URL, placeholder featured price, newsletter form action
.github/workflows/daily.yml  # ready-made daily scrape + deploy workflow (inactive until pushed)
```

## Run it

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
./run.sh            # daily job: scrape + diff + build + link check
./run.sh scrape     # only snapshot/diff  (python scripts/snapshot.py [--only clay,apollo] [--date 2026-10-20])
./run.sh build      # only build dist/ and check links
./run.sh serve      # build and serve at http://localhost:8787
```

- The scraper uses headless Chrome (`google-chrome` or `chromium` on PATH) for pages marked `"fetch_method": "chrome"` and falls back to plain HTTP. Pages marked `http` fall back to Chrome. A full run with 6 workers takes about 40 seconds.
- Running the scraper twice on the same date is safe: entries for that date are replaced, not duplicated.
- **Price changes.** When a price point appears or disappears, the scraper writes a `price_change` entry to `changes.json`, including the diff. Changed wording on the pricing page is logged as `copy_change`. The structured plan tables in `tools.json` are curated by hand, so update the matching tool's `tiers` when a real change is flagged.
- **Affiliate links.** Add `"<tool-slug>": {"url": "...", "program": "..."}` to `data/affiliates.json`. It is the single source of truth; the build merges it into each tool and fails on unknown slugs. Active now: Klenty, Woodpecker, Prospeo. An optional `perk` string is shown next to the CTA on tool and pricing pages. To guarantee comparison pages for a tool, list partner slugs in its `compare_with` in `tools.json`; those pairs are generated first within the category quota. The site then uses it for the "Visit" button with `rel="sponsored noopener"` and an "Affiliate" label. A disclosure appears in the footer and on `/disclosure/`. `check_links.py` fails the build if any affiliate link is missing `rel=sponsored`.
- **Featured listings.** Set `"featured": true` on a tool. The flag is in the schema, but the templates don't use it yet.

## Known limitations (v1)

- **Prices vary by visitor location.** Some vendors (RocketReach, HubSpot) localise by country. The first CI run (US) re-baselined everything, and RocketReach and HubSpot plan tables now use the USD figures it captured.
- **Prospeo** blocks plain-HTTP fetches from some networks; the CI headless-Chrome fetch works.
- **Diffs can be noisy.** Promo banners and A/B tests can trigger `copy_change` entries. Review them before they go into the newsletter.
- **"From $X/mo" is the lowest listed paid price.** It may be an annual or per-seat price. Each pricing table shows monthly and annual prices separately.

## Live hosting (GitHub Pages)

Live at https://ajaynallavelli.github.io/gtmstack-tracker/ from repo https://github.com/AjayNallavelli/gtmstack-tracker.
`.github/workflows/daily.yml` runs daily at 02:30 UTC (08:00 IST), and also on manual dispatch and on code pushes to `main`. A scheduled or manual run does four things in order:
1. Snapshots and diffs every pricing page.
2. Commits `data/` changes back to `main` as `gtmstack-bot`.
3. Builds the site and checks links.
4. Deploys with `actions/deploy-pages`.

A code push skips the scrape and only rebuilds and deploys.

**First CI run = new baseline.** The runner sits in a different region from the box that made the original baseline, so some vendors show other currencies. When `data/ci_baseline.json` is missing, the scraper runs with `--rebaseline`: it saves snapshots but logs no diffs, then creates the marker. Delete the marker to re-baseline again, or run `python scripts/snapshot.py --rebaseline` by hand.

**Sub-path hosting.** `base_url` in `site.json` contains `/gtmstack-tracker`. The build adds that prefix to every root-relative `href`/`src`/`action`. To preview locally at the root, build with `SITE_URL=http://localhost:8787 python scripts/build.py`. For a custom domain later, set `base_url` to the domain, add a CNAME in Pages settings, and rebuild.

Note: crawlers only read `robots.txt` at a domain root, so the sub-path copy has no effect. Submit `sitemap.xml` in Google Search Console instead, or move to a custom domain.

## Other free hosting options

1. **GitHub (free).** Create a repo, push this folder (`.gitignore` excludes `.venv`, `dist` and `scratch`), then turn on *Settings → Pages → Source: GitHub Actions*. `.github/workflows/daily.yml` then scrapes daily at 08:00 IST, commits the snapshots, builds the site and deploys it to GitHub Pages. Public repos get unlimited Actions minutes; private repos get 2,000 free minutes a month, and this job uses about 2–3 minutes a day.
2. **Or Cloudflare Pages (free).** Connect the repo with build command `pip install -r requirements.txt && python scripts/build.py` and output folder `dist`. Keep the GitHub Action for the daily scrape (remove its deploy steps); each commit triggers a Cloudflare rebuild. Cloudflare also adds free analytics.
3. **Domain.** Set `base_url` in `site.json`, or `SITE_URL` in the workflow, to the real domain so canonicals and the sitemap are correct. Then add the domain in Pages or Cloudflare.

## Newsletter provider options (not set up)

| Provider | Free tier (check current terms) | Notes |
|---|---|---|
| beehiiv | Free up to 2,500 subscribers | Built-in ad network and referral program; good fit for sponsor revenue |
| Buttondown | Free up to 100 subscribers | Markdown-native, simple embed form; cheap paid tiers |
| Kit (ConvertKit) | Free up to 10,000 subscribers (limited features) | Strong automations; sponsor network |
| MailerLite | Free up to 500–1,000 subscribers | Cheap, good forms |
| Substack | Free (takes 10% of paid subscriptions only) | Least control over branding and domain |

**Connected: beehiiv** (https://gtmstack.beehiiv.com). Settings are under `newsletter` in `site.json`. The full embed (`v3/loader.js`) appears only on the homepage and `/newsletter/`. The footer, tool pages and vs pages use a light "Subscribe free" button that links to the subscribe page, and each embed has a noscript fallback link. beehiiv's `attribution.js` loads once per page, async, in `<head>`.

## Monetization hooks

- Affiliates: Instantly (reported 20–40% recurring), Smartlead (15–35%), Clay (20%), and others. Join each program, then paste the links into `affiliate_url`.
- Paid featured listing: the price on `/get-featured/` is a placeholder in `site.json` and needs the owner's confirmation.
- Newsletter sponsor slot: there's a placeholder in the draft issue.
