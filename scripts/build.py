#!/usr/bin/env python3
"""Static site generator for GTMStack Tracker.  Usage: python scripts/build.py [--out dist]"""
import argparse, datetime as dt, html, itertools, json, os, re, shutil
from statistics import median
from urllib.parse import urlparse
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape
import seo, datadates

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CATS = {
    "AI SDR agents": ("ai-sdr-agents", "AI SDR agents that prospect, write and book meetings autonomously."),
    "Cold email & engagement": ("cold-email", "Cold email and sales engagement platforms for sending sequences at scale."),
    "Data & enrichment": ("data-enrichment", "B2B contact data, enrichment and waterfall tools."),
    "Deliverability & warmup": ("deliverability", "Warmup, inbox placement testing and email verification tools."),
}
# rough popularity order used to pick which comparison pairs to generate (higher first)
POPULAR = ["apollo", "instantly", "clay", "smartlead", "lemlist", "zoominfo", "11x", "artisan", "aisdr", "replyio",
           "lusha", "hunter", "cognism", "saleshandy", "outreach", "salesloft", "amplemarket", "snovio", "woodpecker",
           "regie", "persana", "mailshake", "klenty", "lagrowthmachine", "seamless", "rocketreach", "kaspr", "prospeo",
           "fullenrich", "findymail", "bettercontact", "pdl", "hubspot-breeze", "mailreach", "warmy", "warmbox",
           "glockapps", "emailguard", "allegrow"]
PAIR_QUOTA = {"AI SDR agents": 12, "Cold email & engagement": 22, "Data & enrichment": 22, "Deliverability & warmup": 7}
# Only real price-point or plan changes are published (change log, RSS, home page, tool pages, public JSON).
# copy_change / billing_toggle / fetch_failed / baseline stay in data/changes.json as raw data only.
# A raw entry can also be hidden by hand with "public": false.
PUBLIC_TYPES = {"price_change", "plan_change"}
STATUS_LABEL = {"public": "Public pricing", "partial": "Partly public", "contact_sales": "Contact sales"}


def money(v):
    if v is None:
        return "—"
    if v == 0:
        return "$0"
    return f"${v:,.2f}".replace(".00", "") if v % 1 else f"${int(v):,}"


def is_public(c):
    return c.get("type") in PUBLIC_TYPES and c.get("public", True) is not False


def change_view(c):
    """Old-vs-new values for a dated change block. Manual plan_change entries may carry "old"/"new"."""
    c = dict(c)
    c["old"] = c.get("old") or c.get("removed") or []
    c["new"] = c.get("new") or c.get("added") or []
    return c


def load():
    site = json.loads((ROOT / "site.json").read_text())
    site["base_url"] = os.environ.get("SITE_URL", site["base_url"]).rstrip("/")
    # sub-path hosting (e.g. GitHub project pages): https://user.github.io/repo -> "/repo"
    site["base_path"] = urlparse(site["base_url"]).path.rstrip("/")
    tools = json.loads((DATA / "tools.json").read_text())["tools"]
    raw = json.loads((DATA / "changes.json").read_text()) if (DATA / "changes.json").exists() else []
    changes = [change_view(c) for c in raw if is_public(c)]
    started = {}
    for c in raw:
        if c["type"] == "baseline":
            started[c["tool_id"]] = min(started.get(c["tool_id"], c["date"]), c["date"])
    # affiliate links live in one file: data/affiliates.json  {slug: url | {"url":..., "program":...}}
    aff = json.loads((DATA / "affiliates.json").read_text()) if (DATA / "affiliates.json").exists() else {}
    for t in tools:
        a = aff.get(t["id"])
        if a:
            t["affiliate_url"] = a if isinstance(a, str) else a.get("url", "")
            if isinstance(a, dict) and a.get("program"):
                t["affiliate_program"] = a["program"]
            t["affiliate_perk"] = a.get("perk", "") if isinstance(a, dict) else ""
    unknown = [k for k in aff if not k.startswith("_") and k not in {t["id"] for t in tools}]
    if unknown:
        raise SystemExit(f"affiliates.json has unknown tool slugs: {unknown}")
    snaps = {}
    sd = DATA / "snapshots"
    if sd.exists():
        for d in sorted(p for p in sd.iterdir() if p.is_dir()):
            for f in d.glob("*.json"):
                m = json.loads(f.read_text())
                snaps.setdefault(m["id"], []).append({"date": d.name, "status": m.get("status"),
                                                      "points": len(m.get("price_tokens", [])), "hash": m.get("hash"),
                                                      "tokens": m.get("price_tokens", [])})
    ddates = datadates.update(json.loads((DATA / "tools.json").read_text())["tools"], dt.date.today().isoformat())
    for t in tools:
        t["slug"] = t["id"]
        t["cat_slug"] = CATS[t["category"]][0]
        h = sorted(snaps.get(t["id"], []), key=lambda s: s["date"], reverse=True)
        t["history"] = h
        ok = [s for s in h if s["status"] == "ok"]
        t["last_checked"] = ok[0]["date"] if ok else t["date_checked"]
        t["last_fetch_failed"] = bool(h) and h[0]["status"] != "ok"
        t["changes"] = [c for c in changes if c["tool_id"] == t["id"]]
        t["tracking_since"] = started.get(t["id"]) or (h[-1]["date"] if h else t["date_checked"])
        # date this tool's underlying data last really changed: tools.json edits or a real detected change
        t["data_date"] = max([ddates.get(t["id"], t["date_checked"])] + [c["date"] for c in t["changes"]])
        t["status_label"] = STATUS_LABEL[t["pricing_status"]]
        paid = [x for tr in t["tiers"] for x in (tr["monthly_usd"], tr["annual_monthly_usd"]) if x]
        t["entry_paid"] = ep = min(paid) if paid else None
        bands = ["free"] if t["has_free_plan"] else []
        if t.get("price_display") and t["id"] not in ("mailreach",):
            bands.append("other")
        elif ep is None and not t["has_free_plan"]:
            bands.append("contact")
        elif ep is not None:
            bands.append("u50" if ep < 50 else "50to150" if ep <= 150 else "o150")
        t["price_band"] = " ".join(bands)
        t["outbound_url"] = t["affiliate_url"] or t["website"]
        t["is_affiliate"] = bool(t["affiliate_url"])
        # paid featured listing: pinned first in category + homepage lists, labelled "Featured (paid)", links rel=sponsored
        t["is_featured"] = t.get("featured") is True
    return site, tools, changes


def pick_pairs(tools):
    rank = {tid: i for i, tid in enumerate(POPULAR)}
    pairs = []
    by_id = {t["id"]: t for t in tools}

    def add_pair(a, b, cat):
        if rank.get(a["id"], 99) > rank.get(b["id"], 99):
            a, b = b, a
        keys = {p["slug"] for p in pairs} | {f"{p['b']['id']}-vs-{p['a']['id']}" for p in pairs}
        key = f"{a['id']}-vs-{b['id']}"
        if key not in keys:
            pairs.append({"slug": key, "a": a, "b": b, "category": cat})
            return True
        return False

    for cat, quota in PAIR_QUOTA.items():
        used = 0
        # pinned pairs first (tool["compare_with"]), counted against the category quota
        for t in tools:
            if t["category"] != cat:
                continue
            for other in t.get("compare_with", []):
                if other in by_id and used < quota and add_pair(t, by_id[other], cat):
                    used += 1
        members = [t for t in tools if t["category"] == cat or (cat in t["categories"] and cat != "Deliverability & warmup")]
        cand = []
        for a, b in itertools.combinations(members, 2):
            if a["category"] != cat and b["category"] != cat:
                continue
            score = rank.get(a["id"], 99) + rank.get(b["id"], 99)
            # prefer pairs where at least one side has public pricing
            if a["pricing_status"] == "contact_sales" and b["pricing_status"] == "contact_sales":
                score += 8
            cand.append((score, a, b))
        cand.sort(key=lambda x: x[0])
        for _, a, b in cand:
            if used >= quota:
                break
            if add_pair(a, b, cat):
                used += 1
    return pairs[:sum(PAIR_QUOTA.values())]


def compare_points(a, b):
    """Plain-language facts derived only from the dataset."""
    pts = []
    ea, eb = a["entry_paid"], b["entry_paid"]
    for x in (a, b):
        if x.get("price_display"):
            pts.append(f"{x['name']} pricing is not a simple monthly plan: {x['price_display']}.")
    if a.get("price_display") or b.get("price_display"):
        ea = eb = None
    ma, mb = seo.monthly_entry(a), seo.monthly_entry(b)
    if ea is not None and eb is not None and ea != eb and ma is not None and ma == mb:
        lo, hi = (a, b) if ea < eb else (b, a)
        pts.append(f"On month-to-month billing both start at {money(ma)}/mo. {lo['name']} is cheaper only on annual billing ({money(lo['entry_paid'])}/mo billed yearly).")
    elif ea is not None and eb is not None and ea != eb:
        lo, hi = (a, b) if ea < eb else (b, a)
        pts.append(f"{lo['name']} has the lower listed entry price ({money(lo['entry_paid'])}/mo vs {money(hi['entry_paid'])}/mo for {hi['name']}). Check the billing basis (per seat, annual vs monthly) in the tables below.")
    for x, y in ((a, b), (b, a)):
        if x["pricing_status"] == "contact_sales" and y["pricing_status"] != "contact_sales":
            pts.append(f"{x['name']} does not publish prices (contact sales); {y['name']} does.")
    if a["has_free_plan"] != b["has_free_plan"]:
        f = a if a["has_free_plan"] else b
        pts.append(f"Only {f['name']} lists a $0 / free tier.")
    elif a["has_free_plan"]:
        pts.append("Both list a $0 / free tier.")
    if not pts:
        pts.append("Neither tool publishes enough pricing to compare entry prices directly; both require a sales conversation.")
    return pts


ROOT_REL = re.compile(r'((?:href|src|action)=")/(?!/)')


def prefix_links(text, base_path):
    """Rewrite root-relative URLs (href="/x") to live under the site's sub-path."""
    if not base_path:
        return text
    return ROOT_REL.sub(lambda m: m.group(1) + base_path + "/", text)


AI_CRAWLERS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User", "Claude-SearchBot", "anthropic-ai",
               "PerplexityBot", "Perplexity-User", "Google-Extended", "Applebot-Extended", "CCBot", "Meta-ExternalAgent",
               "Amazonbot", "Bytespider", "cohere-ai", "DuckAssistBot", "MistralAI-User"]


def robots_txt(site):
    lines = ["# GTMStack Tracker: all crawlers, including AI crawlers, are welcome.", "User-agent: *", "Allow: /", ""]
    for b in AI_CRAWLERS:
        lines += [f"User-agent: {b}", "Allow: /", ""]
    lines.append(f"Sitemap: {site['base_url']}/sitemap.xml")
    # Identical copy under a second filename so GSC can be pointed at a fresh URL
    # if sitemap.xml stays stuck on "Couldn't fetch".
    lines.append(f"Sitemap: {site['base_url']}/sitemap-index.xml")
    return "\n".join(lines) + "\n"


def home_ld(site, tools, stats, since, modified):
    base = site["base_url"] + "/"
    org = {"@type": "Organization", "@id": base + "#org", "name": site["name"], "url": base,
           "logo": {"@type": "ImageObject", "url": base + "static/logo.png", "width": 512, "height": 512}, "sameAs": [site["x_url"]] if site.get("x_url") else [],
           "email": site.get("contact_email") or None,
           "description": site["tagline"] + "."}
    web = {"@type": "WebSite", "@id": base + "#website", "name": site["name"], "url": base, "publisher": {"@id": base + "#org"}}
    ds = {"@type": "Dataset", "@id": base + "#dataset",
          "name": "GTMStack Tracker: AI sales & outbound tool pricing dataset",
          "description": (f"Plans, monthly and annual prices, free tiers and limits for {stats['tools']} AI SDR, cold email, "
                          "data enrichment and deliverability tools, copied from each vendor's public pricing page, re-checked daily, "
                          "with a dated log of real price and plan changes."),
          "url": base, "license": "https://creativecommons.org/licenses/by/4.0/",
          "creator": {"@type": "Organization", "name": site["name"], "url": base},
          "publisher": {"@type": "Organization", "name": site["name"], "url": base},
          "isAccessibleForFree": True, "inLanguage": "en",
          "keywords": ["sales software pricing", "AI SDR pricing", "cold email tool pricing", "B2B data enrichment pricing",
                       "email deliverability pricing", "SaaS price changes"],
          "temporalCoverage": f"{since}/..", "dateModified": modified, "variableMeasured": ["plan price (USD/month)", "annual price (USD/month)", "free plan", "pricing status"],
          "distribution": [
              {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": base + "data/tools.json", "name": "Tools, plans and prices"},
              {"@type": "DataDownload", "encodingFormat": "application/json", "contentUrl": base + "data/changes.json", "name": "Real price and plan changes"}]}
    org = {k: v for k, v in org.items() if v}
    return {"@context": "https://schema.org", "@graph": [org, web, ds]}



# tools whose price_display is still a rankable USD monthly figure (mirrors seo.NUMERIC_DISPLAY)
INDEX_NUMERIC_DISPLAY = {"mailreach"}


def entry_for_index(t):
    """Lowest listed paid USD/mo for index stats. Skip null, usage-based, and non-USD display quotes."""
    if t.get("price_display") and t["id"] not in INDEX_NUMERIC_DISPLAY:
        return None
    return t.get("entry_paid")


def write_pricing_csv(path, tools, by_id=None):
    """One row per plan; same columns as the live open dataset."""
    import csv, io
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["tool_id", "tool", "category", "website", "pricing_url", "pricing_status", "plan",
                "monthly_usd", "annual_monthly_usd", "limits", "note", "billing_note", "has_free_plan", "date_checked"])
    for t in sorted(tools, key=lambda x: x["id"]):
        checked = (by_id or {}).get(t["id"], t).get("last_checked") or t.get("date_checked", "")
        for tier in t.get("tiers") or [{}]:
            w.writerow([t["id"], t["name"], t.get("category", ""), t.get("website", ""), t.get("pricing_url", ""),
                        t.get("pricing_status", ""), tier.get("plan", ""),
                        "" if tier.get("monthly_usd") is None else tier.get("monthly_usd"),
                        "" if tier.get("annual_monthly_usd") is None else tier.get("annual_monthly_usd"),
                        tier.get("limits", ""), tier.get("note", ""), t.get("billing_note", ""),
                        t.get("has_free_plan", False), checked])
    path.write_text(buf.getvalue())
    return path


def build_month_index(year_month, tools, changes, tracking_since, extra=None):
    """Stats + copy for /indexes/YYYY-MM/. extra may supply honesty_note / next_month_note / raises / cuts."""
    extra = extra or {}
    y, m = map(int, year_month.split("-"))
    month_name = dt.date(y, m, 1).strftime("%B %Y")
    period_label = dt.date(y, m, 1).strftime("%B %Y")
    entries = []
    for t in tools:
        ep = entry_for_index(t)
        if ep is not None:
            entries.append((t["name"], ep))
    vals = [e[1] for e in entries]
    lowest = min(vals) if vals else None
    lowest_tools = [n for n, v in entries if v == lowest] if lowest is not None else []
    month_changes = [c for c in changes if c["date"].startswith(year_month)]
    cats = []
    for name, (slug, _blurb) in CATS.items():
        cats.append({"name": name, "slug": slug, "count": sum(1 for t in tools if t["category"] == name)})
    free_count = sum(1 for t in tools if t["has_free_plan"])
    contact_count = sum(1 for t in tools if t["pricing_status"] == "contact_sales")
    raises = extra.get("raises", 0)
    cuts = extra.get("cuts", 0)
    median_entry = median(vals) if vals else None
    answer = (
        f"As of the {month_name} Pricing Index (built from tools.json; tracking since {tracking_since}), "
        f"we track {len(tools)} AI sales tools: {free_count} list a $0 tier, {contact_count} are contact-sales only, "
        f"and among {len(vals)} tools with a numeric USD entry price the median is {money(median_entry)}/mo "
        f"(lowest {money(lowest)}/mo). The public log recorded {len(month_changes)} typed price_change/plan_change "
        f"row{'s' if len(month_changes) != 1 else ''} in {month_name}; structured plan tables had {raises} raise(s) and {cuts} cut(s) hand-updated."
    )
    return {
        "slug": year_month,
        "year_month": year_month,
        "month_name": month_name,
        "period_label": period_label,
        "h1": f"AI Sales Tool Pricing Index — {month_name}",
        "title": f"AI Sales Tool Pricing Index — {month_name}",
        "answer": answer,
        "lead": (
            f"One citable snapshot of entry prices, free tiers and typed pricing-log activity for the tools GTMStack Tracker covers. "
            f"Numbers below are computed from data/tools.json; the change section uses only public price_change / plan_change rows dated in {month_name}."
        ),
        "tool_count": len(tools),
        "free_count": free_count,
        "contact_count": contact_count,
        "numeric_count": len(vals),
        "median_entry": median_entry,
        "lowest_entry": lowest,
        "lowest_tools": lowest_tools,
        "change_count": len(month_changes),
        "raises": raises,
        "cuts": cuts,
        "categories": cats,
        "changes": month_changes,
        "honesty_note": extra.get("honesty_note", ""),
        "next_month_note": extra.get("next_month_note", ""),
        "tracking_since": tracking_since,
        "csv_name": f"pricing-index-{year_month}.csv",
        "csv_href": f"/data/pricing-index-{year_month}.csv",
        "blurb": f"{len(tools)} tools · median entry {money(median_entry)}/mo · {len(month_changes)} typed log row(s)",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "dist"))
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    site, tools, changes = load()
    env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=select_autoescape(["html", "xml"]))
    env.filters["money"] = money
    env.filters["rfc822"] = lambda d: dt.date.fromisoformat(d).strftime("%a, %d %b %Y 06:00:00 +0000")
    env.filters["faq_item"] = lambda f: {"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}}
    env.filters["nicedate"] = lambda d: dt.date.fromisoformat(d).strftime("%b %-d, %Y")
    now = dt.date.today()
    month = now.strftime("%B %Y")
    pairs = pick_pairs(tools)
    by_id = {t["id"]: t for t in tools}
    pair_by_ids = {frozenset((p["a"]["id"], p["b"]["id"])): p for p in pairs}
    for t in tools:
        seo.enrich(t)
    for t in tools:
        t["pairs"] = [p for p in pairs if p["a"]["id"] == t["id"] or p["b"]["id"] == t["id"]]
        t["all_alternatives"] = seo.rank(seo.peers(t, tools))
        t["alternatives"] = t["all_alternatives"][:6]
    cats = [{"name": n, "slug": s, "blurb": b, "tools": [t for t in tools if n in t["categories"]],
             "featured": sorted([t for t in tools if n in t["categories"] and t["is_featured"]], key=lambda t: t["name"])} for n, (s, b) in CATS.items()]
    stats = {"tools": len(tools), "public": sum(t["pricing_status"] != "contact_sales" for t in tools),
             "contact": sum(t["pricing_status"] == "contact_sales" for t in tools),
             "free": sum(t["has_free_plan"] for t in tools),
             "last": max(t["last_checked"] for t in tools)}
    # buyer-intent roundups (/best/...), built only from tools.json
    roundups = []
    for c in cats:
        label, short = seo.CAT_LABEL[c["name"]], seo.CAT_SHORT[c["slug"]]
        ranked = seo.rank(c["tools"])
        free = [t for t in ranked if t["has_free_plan"]]
        priced = [t for t in ranked if t["sort_price"] is not None]
        cheapest = min(priced, key=lambda t: t["sort_price"]) if priced else None
        c["roundups"] = []
        specs = [("cheapest", f"cheapest-{short}-tools", ranked,
                  f"Cheapest {label} tools ({now.year}): {len(ranked)} ranked by price",
                  f"Cheapest {label} tools ({now.year})",
                  f"{len(ranked)} {label} tools ranked by lowest listed paid price" + (f"; {cheapest['name']} is cheapest {cheapest['entry_label']}" if cheapest else "") + f". {len(free)} have a free plan. Checked {stats['last']}.")]
        if len(free) >= 2:
            specs.append(("free", f"best-free-{short}-tools", free,
                          f"Best free {label} tools ({now.year}): {len(free)} with a $0 plan",
                          f"Best free {label} tools ({now.year})",
                          f"{len(free)} {label} tools with a $0 plan: {seo.names(free)}. What each free tier is and what the first paid plan costs."))
        specs.append(("annual", f"{short}-tools-annual-vs-monthly-pricing", ranked,
                      f"{label[0].upper() + label[1:]} tools pricing compared: annual vs monthly ({now.year})",
                      f"{label[0].upper() + label[1:]} tools pricing compared: annual vs monthly cost",
                      f"Monthly vs annual prices and yearly cost for {len(ranked)} {label} tools, with the annual discount for every plan that publishes one."))
        for kind, slug, ts, title, h1, desc in specs:
            r = {"kind": kind, "slug": slug, "cat": c, "label": label, "tools": ts, "title": title, "h1": h1,
                 "description": desc, "faq": seo.roundup_faq(kind, label, ts)}
            roundups.append(r)
            c["roundups"].append(r)
    all_free = seo.rank([t for t in tools if t["has_free_plan"]])
    roundups.append({"kind": "free", "slug": "free-ai-sales-outbound-tools", "cat": None, "label": "AI sales & outbound",
                     "tools": all_free, "title": f"Free AI sales & outbound tools ({now.year}): {len(all_free)} with a $0 plan",
                     "h1": f"Free AI sales & outbound tools ({now.year})",
                     "description": f"Every AI SDR, cold email, data and deliverability tool we track that lists a $0 plan ({len(all_free)} of {len(tools)}), with the first paid upgrade price.",
                     "faq": seo.roundup_faq("free", "AI sales & outbound", all_free)})
    # Long-tail: free/cheap email warmup (dedicated warmers + cold-email tools that include warmup)
    WARMUP_DEDICATED = {"warmbox", "mailreach", "warmy"}
    def _is_email_warmup(t):
        if t["id"] in WARMUP_DEDICATED:
            return True
        blob = f"{t.get('description') or ''} {t.get('billing_note') or ''}".lower()
        return any(k in blob for k in ("warmup", "warm-up", "warmer", "lemwarm"))
    warmup_tools = seo.rank([t for t in tools if _is_email_warmup(t)])
    deliv = next(c for c in cats if c["name"] == "Deliverability & warmup")
    priced_w = [t for t in warmup_tools if t["sort_price"] is not None]
    cheapest_w = min(priced_w, key=lambda t: t["sort_price"]) if priced_w else None
    free_warmup = sum(
        1 for t in warmup_tools
        if t["has_free_plan"] or "free warmup" in f"{t.get('description') or ''} {t.get('billing_note') or ''}".lower()
    )
    wr = {"kind": "cheapest", "slug": "free-email-warmup-tools", "cat": deliv, "label": "email warmup",
          "tools": warmup_tools,
          "title": f"Free & cheap email warmup tools ({now.year}): {len(warmup_tools)} ranked by price",
          "h1": f"Free & cheap email warmup tools ({now.year})",
          "description": (
              f"{len(warmup_tools)} email warmup tools ranked by lowest listed paid price"
              + (f"; {cheapest_w['name']} is cheapest {cheapest_w['entry_label']}" if cheapest_w else "")
              + f". {free_warmup} include a free plan or free bundled warmup. Checked {stats['last']}."
          ),
          "faq": seo.roundup_faq("cheapest", "email warmup", warmup_tools)}
    roundups.append(wr)
    deliv["roundups"].append(wr)
    for t in tools:
        t["roundups"] = [r for r in roundups if r["cat"] and r["cat"]["name"] in t["categories"]]
    common = dict(site=site, cats=cats, stats=stats, month=month, year=now.year, roundups=roundups)
    pages = []

    def lastmod(ts):
        return max(t["data_date"] for t in ts) if ts else None

    def render(tpl, path, sitemap=True, lastmod=None, **ctx):
        p = out / path.strip("/") / "index.html" if not path.endswith((".html", ".xml", ".txt")) else out / path.strip("/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(prefix_links(env.get_template(tpl).render(**common, path=path, **ctx), site["base_path"]))
        if sitemap and (path.endswith("/") or path == "/"):
            pages.append((path, lastmod))

    all_lm = lastmod(tools)
    tracking_since = min(t["tracking_since"] for t in tools)
    common["tracking_since"] = tracking_since
    render("index.html", "/", lastmod=all_lm, home_ld=home_ld(site, tools, stats, tracking_since, all_lm), tools=sorted(tools, key=lambda t: (not t["is_featured"], t["name"].lower())), changes=changes[:6],
           title=f"{site['name']}: AI SDR, cold email & data tool pricing (tracked daily)",
           description=f"Compare pricing for {len(tools)} AI SDR, cold email, enrichment and deliverability tools. We snapshot every pricing page daily and log what changed.")
    for c in cats:
        render("category.html", f"/category/{c['slug']}/", lastmod=lastmod(c["tools"]), cat=c, filterable=True, faq=seo.roundup_faq("cheapest", seo.CAT_LABEL[c["name"]], c["tools"]),
               title=f"{c['name']} pricing compared ({month}) | {site['name']}",
               description=f"{c['blurb']} Plans, prices and pricing history for {len(c['tools'])} tools.")
    for t in tools:
        sp = t["price_display"] if t.get("price_display") else f"from {money(t['entry_paid'])}/mo" if t["entry_paid"] else ("free plan available" if t["has_free_plan"] else "contact sales only")
        render("tool.html", f"/tools/{t['slug']}/", lastmod=t["data_date"], answer=seo.answer_line_tool(t), t=t, faq=t["faq"],
               title=f"{t['name']} pricing {now.year}: plans, limits & annual cost",
               description=f"{t['name']} pricing, checked {t['last_checked']}: {sp}. Free plan: {'yes' if t['has_free_plan'] else 'no'}. Every plan, monthly vs annual price, limits and pricing history.")
        alts = t["all_alternatives"]
        afree = sum(x["has_free_plan"] for x in alts)
        render("alternatives.html", f"/alternatives/{t['slug']}/", lastmod=lastmod([t] + alts), answer=seo.answer_line_alternatives(t, alts), t=t, filterable=True, alts=alts, faq=seo.alternatives_faq(t, alts),
               vs={x["id"]: pair_by_ids.get(frozenset((t["id"], x["id"]))) for x in alts},
               title=f"{t['name']} alternatives ({now.year}): {len(alts)} tools compared by price",
               description=f"{len(alts)} {t['name']} alternatives sorted by entry price, {afree} with a free plan. Plans, free tiers and side-by-side comparisons, checked {stats['last']}.")
        # /pricing/<slug>/ is kept for existing links but consolidated into the tool page (canonical + not in sitemap)
        render("pricing.html", f"/pricing/{t['slug']}/", sitemap=False, canonical=f"/tools/{t['slug']}/", t=t,
               title=f"{t['name']} pricing {now.year}: plans, limits & changes ({sp})",
               description=f"How much does {t['name']} cost? Every plan, monthly vs annual price and key limits, checked {t['last_checked']} from the official pricing page.")
    for p in pairs:
        render("compare.html", f"/compare/{p['slug']}/", lastmod=lastmod([p["a"], p["b"]]), answer=seo.answer_line_compare(p["a"], p["b"]), p=p, points=compare_points(p["a"], p["b"]),
               title=f"{p['a']['name']} vs {p['b']['name']} pricing ({month}) | {site['name']}",
               description=f"{p['a']['name']} vs {p['b']['name']}: side-by-side plans, entry price, free tier and pricing history from the official pricing pages.")
    for r in roundups:
        render("roundup.html", f"/best/{r['slug']}/", lastmod=lastmod(r["tools"]), answer=seo.answer_line_roundup(r), r=r, filterable=True, faq=r["faq"], title=r["title"], description=r["description"])
    render("best_index.html", "/best/", lastmod=all_lm, title=f"Buyer guides: cheapest & free AI sales tools ({now.year}) | {site['name']}",
           description="Data-driven roundups of the cheapest and free AI SDR, cold email, data enrichment and deliverability tools, built from tracked pricing pages.")
    render("compare_index.html", "/compare/", lastmod=lastmod([x for p in pairs for x in (p["a"], p["b"])]), pairs=pairs, title=f"Tool comparisons | {site['name']}",
           description="Side-by-side pricing comparisons of AI sales and outbound tools in the same category.")
    render("changes.html", "/changes/", lastmod=max([c["date"] for c in changes], default=tracking_since), changes=changes, by_id=by_id,
           title=f"What changed: pricing & plan change log | {site['name']}",
           description="A dated feed of pricing and plan changes detected on the pricing pages of AI sales and outbound tools.")
    render("feed.xml", "/changes/feed.xml", changes=changes[:50])
    # monthly pricing indexes (first Thursday publish; freeze tools.json rows into named CSV)
    indexes = []
    oct_extra = {
        "raises": 0,
        "cuts": 0,
        "honesty_note": (
            "Honesty note: the public log recorded 1 price_change row for Woodpecker on 2026-10-23 "
            "(\"Pricing page changed: removed $0, $0.01, $1, $10, $20, $2000, $27, $29.\"). "
            "That row is a scraper price-point delta on the pricing page text. The structured plan tables "
            "in tools.json for Woodpecker were NOT hand-updated for a vendor plan raise or cut; curated "
            "plan tables are maintained separately from the automated log."
        ),
        "next_month_note": (
            "November already has real changes that belong in the November index next month, not as October events: "
            "Instantly (2026-11-03 Outreach Hypergrowth $97→$107 / $77.6→$85.58) and La Growth Machine "
            "(2026-11-04 EUR pricing redesign). They are listed on /changes/ now but counted in November's index."
        ),
    }
    indexes.append(build_month_index("2026-10", tools, changes, tracking_since, oct_extra))
    render("indexes.html", "/indexes/", lastmod=all_lm, indexes=indexes,
           title=f"AI Sales Tool Pricing Indexes | {site['name']}",
           description="Monthly citable snapshots of AI sales tool entry prices, free tiers and typed price/plan changes.")
    for ix in indexes:
        render("pricing_index.html", f"/indexes/{ix['slug']}/", lastmod=all_lm, idx=ix,
               title=f"{ix['title']} | {site['name']}",
               description=ix["answer"])

    render("featured.html", "/get-featured/", title=f"Get featured on {site['name']}",
           description="Feature your sales or outbound tool in front of buyers comparing GTM software pricing.")
    render("newsletter.html", "/newsletter/", title=f"The {site['name']} newsletter",
           description="A weekly email with every pricing change across AI SDR, cold email and data tools.")
    render("static_page.html", "/disclosure/", page="disclosure", title=f"Affiliate disclosure | {site['name']}",
           description="How GTMStack Tracker makes money and how affiliate links are marked.")
    render("static_page.html", "/methodology/", page="methodology", title=f"Methodology | {site['name']}",
           description="How we collect, verify and diff pricing data.")
    render("404.html", "404.html", title="Page not found", description="Page not found")
    # assets, data download, sitemap, robots
    shutil.copytree(ROOT / "static", out / "static", ignore=shutil.ignore_patterns("root"))
    # files in static/root/ are published verbatim at the site root (e.g. search-console verification)
    if (ROOT / "static" / "root").exists():
        for f in (ROOT / "static" / "root").iterdir():
            if f.is_file():
                shutil.copy(f, out / f.name)
    (out / "data").mkdir()
    pub = json.loads((DATA / "tools.json").read_text())
    for t in pub["tools"]:
        t["affiliate_url"] = by_id[t["id"]]["affiliate_url"]
    (out / "data" / "tools.json").write_text(json.dumps(pub, indent=1, ensure_ascii=False))
    # open pricing dataset (CC BY 4.0): one row per plan, no affiliate URLs
    write_pricing_csv(out / "data" / "pricing.csv", pub["tools"], by_id)
    write_pricing_csv(DATA / "pricing.csv", pub["tools"], by_id)
    # Frozen monthly index CSVs: once published, copy the repo file into dist.
    # Do not regenerate from current tools.json (that would rewrite a citable snapshot).
    for ix in indexes:
        src = DATA / ix["csv_name"]
        dest = out / "data" / ix["csv_name"]
        if src.exists():
            dest.write_bytes(src.read_bytes())
        else:
            write_pricing_csv(src, pub["tools"], by_id)
            write_pricing_csv(dest, pub["tools"], by_id)
    # public change data = real changes only (the raw log incl. copy/toggle/fetch-failed rows stays in the repo)
    (out / "data" / "changes.json").write_text(json.dumps([{k: v for k, v in c.items() if k not in ("old", "new")} for c in changes], indent=1, ensure_ascii=False))
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p, lm in pages:
        # lastmod = date the page's underlying data last really changed; omitted for pages with no tracked data
        sm.append(f"  <url><loc>{html.escape(site['base_url'] + p)}</loc>" + (f"<lastmod>{lm}</lastmod>" if lm else "") + "</url>")
    sm.append("</urlset>")
    sitemap_body = "\n".join(sm) + "\n"
    (out / "sitemap.xml").write_text(sitemap_body)
    # Exact copy of the urlset under a second filename (GSC "Couldn't fetch" workaround).
    (out / "sitemap-index.xml").write_text(sitemap_body)
    # 404 page must work from any depth on GitHub Pages: links are already absolute-with-prefix
    (out / ".nojekyll").write_text("")
    (out / "robots.txt").write_text(robots_txt(site))
    print(f"Built {len(pages)} sitemap pages ({len(tools)} tools, {len(tools)} alternatives, {len(roundups)} roundups, {len(pairs)} comparisons; "
          f"{len(tools)} /pricing/ pages canonicalised to tool pages) -> {out}")


if __name__ == "__main__":
    main()
