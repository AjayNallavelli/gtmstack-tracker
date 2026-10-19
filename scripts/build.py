#!/usr/bin/env python3
"""Static site generator for GTMStack Tracker.  Usage: python scripts/build.py [--out dist]"""
import argparse, datetime as dt, html, itertools, json, os, re, shutil
from urllib.parse import urlparse
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

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
PAIR_QUOTA = {"AI SDR agents": 12, "Cold email & engagement": 21, "Data & enrichment": 20, "Deliverability & warmup": 8}
STATUS_LABEL = {"public": "Public pricing", "partial": "Partly public", "contact_sales": "Contact sales"}


def money(v):
    if v is None:
        return "—"
    if v == 0:
        return "$0"
    return f"${v:,.2f}".replace(".00", "") if v % 1 else f"${int(v):,}"


def load():
    site = json.loads((ROOT / "site.json").read_text())
    site["base_url"] = os.environ.get("SITE_URL", site["base_url"]).rstrip("/")
    # sub-path hosting (e.g. GitHub project pages): https://user.github.io/repo -> "/repo"
    site["base_path"] = urlparse(site["base_url"]).path.rstrip("/")
    tools = json.loads((DATA / "tools.json").read_text())["tools"]
    changes = json.loads((DATA / "changes.json").read_text()) if (DATA / "changes.json").exists() else []
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
    for t in tools:
        t["slug"] = t["id"]
        t["cat_slug"] = CATS[t["category"]][0]
        h = sorted(snaps.get(t["id"], []), key=lambda s: s["date"], reverse=True)
        t["history"] = h
        ok = [s for s in h if s["status"] == "ok"]
        t["last_checked"] = ok[0]["date"] if ok else t["date_checked"]
        t["last_fetch_failed"] = bool(h) and h[0]["status"] != "ok"
        t["changes"] = [c for c in changes if c["tool_id"] == t["id"]]
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
    return pairs[:60]


def compare_points(a, b):
    """Plain-language facts derived only from the dataset."""
    pts = []
    ea, eb = a["entry_paid"], b["entry_paid"]
    for x in (a, b):
        if x.get("price_display"):
            pts.append(f"{x['name']} pricing is not a simple monthly plan: {x['price_display']}.")
    if a.get("price_display") or b.get("price_display"):
        ea = eb = None
    if ea is not None and eb is not None and ea != eb:
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
    env.filters["nicedate"] = lambda d: dt.date.fromisoformat(d).strftime("%b %-d, %Y")
    now = dt.date.today()
    month = now.strftime("%B %Y")
    pairs = pick_pairs(tools)
    by_id = {t["id"]: t for t in tools}
    for t in tools:
        t["pairs"] = [p for p in pairs if p["a"]["id"] == t["id"] or p["b"]["id"] == t["id"]]
        t["alternatives"] = [x for x in tools if x["category"] == t["category"] and x["id"] != t["id"]][:6]
    cats = [{"name": n, "slug": s, "blurb": b, "tools": [t for t in tools if n in t["categories"]]} for n, (s, b) in CATS.items()]
    stats = {"tools": len(tools), "public": sum(t["pricing_status"] != "contact_sales" for t in tools),
             "contact": sum(t["pricing_status"] == "contact_sales" for t in tools),
             "free": sum(t["has_free_plan"] for t in tools),
             "last": max(t["last_checked"] for t in tools)}
    common = dict(site=site, cats=cats, stats=stats, month=month, year=now.year)
    pages = []

    def render(tpl, path, **ctx):
        p = out / path.strip("/") / "index.html" if not path.endswith((".html", ".xml", ".txt")) else out / path.strip("/")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(prefix_links(env.get_template(tpl).render(**common, path=path, **ctx), site["base_path"]))
        if path.endswith("/") or path == "/":
            pages.append(path)

    render("index.html", "/", tools=tools, changes=changes[:6],
           title=f"{site['name']}: AI SDR, cold email & data tool pricing (tracked daily)",
           description=f"Compare pricing for {len(tools)} AI SDR, cold email, enrichment and deliverability tools. We snapshot every pricing page daily and log what changed.")
    for c in cats:
        render("category.html", f"/category/{c['slug']}/", cat=c,
               title=f"{c['name']} pricing compared ({month}) | {site['name']}",
               description=f"{c['blurb']} Plans, prices and pricing history for {len(c['tools'])} tools.")
    for t in tools:
        render("tool.html", f"/tools/{t['slug']}/", t=t,
               title=f"{t['name']} review, plans & pricing history | {site['name']}",
               description=f"{t['name']}: {t['description'][:110]} Plans, limits and a dated log of pricing changes.")
        sp = t["price_display"] if t.get("price_display") else f"from {money(t['entry_paid'])}/mo" if t["entry_paid"] else ("free plan available" if t["has_free_plan"] else "contact sales only")
        render("pricing.html", f"/pricing/{t['slug']}/", t=t,
               title=f"{t['name']} pricing {now.year}: plans, limits & changes ({sp})",
               description=f"How much does {t['name']} cost? Every plan, monthly vs annual price and key limits, checked {t['last_checked']} from the official pricing page.")
    for p in pairs:
        render("compare.html", f"/compare/{p['slug']}/", p=p, points=compare_points(p["a"], p["b"]),
               title=f"{p['a']['name']} vs {p['b']['name']} pricing ({month}) | {site['name']}",
               description=f"{p['a']['name']} vs {p['b']['name']}: side-by-side plans, entry price, free tier and pricing history from the official pricing pages.")
    render("compare_index.html", "/compare/", pairs=pairs, title=f"Tool comparisons | {site['name']}",
           description="Side-by-side pricing comparisons of AI sales and outbound tools in the same category.")
    render("changes.html", "/changes/", changes=changes, by_id=by_id,
           title=f"What changed: pricing & plan change log | {site['name']}",
           description="A dated feed of pricing and plan changes detected on the pricing pages of AI sales and outbound tools.")
    render("feed.xml", "/changes/feed.xml", changes=changes[:50])
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
    shutil.copytree(ROOT / "static", out / "static")
    (out / "data").mkdir()
    pub = json.loads((DATA / "tools.json").read_text())
    for t in pub["tools"]:
        t["affiliate_url"] = by_id[t["id"]]["affiliate_url"]
    (out / "data" / "tools.json").write_text(json.dumps(pub, indent=1, ensure_ascii=False))
    if (DATA / "changes.json").exists():
        shutil.copy(DATA / "changes.json", out / "data" / "changes.json")
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for p in pages:
        sm.append(f"  <url><loc>{html.escape(site['base_url'] + p)}</loc><lastmod>{stats['last']}</lastmod></url>")
    sm.append("</urlset>")
    (out / "sitemap.xml").write_text("\n".join(sm) + "\n")
    # 404 page must work from any depth on GitHub Pages: links are already absolute-with-prefix
    (out / ".nojekyll").write_text("")
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {site['base_url']}/sitemap.xml\n")
    print(f"Built {len(pages)} HTML pages ({len(tools)} tools, {len(tools)} pricing pages, {len(pairs)} comparisons) -> {out}")


if __name__ == "__main__":
    main()
