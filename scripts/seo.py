"""Buyer-intent helpers for the static build: derived pricing facts, FAQ text, roundups and alternatives.

Everything here is derived from data/tools.json only. Nothing is invented: when a vendor does not publish a
price the text says so ("contact sales"), and usage-based / non-USD pricing is quoted verbatim from price_display.
"""
import datetime as dt

# tools whose price_display is a plain per-month USD range, so their numeric entry price is safe to rank on
NUMERIC_DISPLAY = {"mailreach"}
CAT_LABEL = {
    "AI SDR agents": "AI SDR",
    "Cold email & engagement": "cold email",
    "Data & enrichment": "data enrichment",
    "Deliverability & warmup": "email deliverability & warmup",
}
CAT_SHORT = {"ai-sdr-agents": "ai-sdr", "cold-email": "cold-email", "data-enrichment": "data-enrichment",
             "deliverability": "deliverability"}


def money(v):
    if v is None:
        return "—"
    if v == 0:
        return "$0"
    return f"${v:,.2f}".replace(".00", "") if v % 1 else f"${int(v):,}"


def _first_price(tr):
    return next((x for x in (tr["monthly_usd"], tr["annual_monthly_usd"]) if x), None)


def tier_price_text(tr):
    m, a = tr["monthly_usd"], tr["annual_monthly_usd"]
    if m and a and m != a:
        return f"{money(m)}/mo monthly or {money(a)}/mo billed annually"
    if m:
        return f"{money(m)}/mo" + (" (same price billed annually)" if a == m else "")
    if a:
        return f"{money(a)}/mo billed annually"
    return "price not published"


def enrich(t):
    """Attach derived, data-only pricing facts to a tool dict (after build.load())."""
    numeric = not t.get("price_display") or t["id"] in NUMERIC_DISPLAY
    t["sort_price"] = t["entry_paid"] if numeric else None
    paid = [tr for tr in t["tiers"] if _first_price(tr)]
    t["cheapest_tier"] = min(paid, key=lambda tr: min(x for x in (tr["monthly_usd"], tr["annual_monthly_usd"]) if x)) if paid else None
    t["free_tier"] = next((tr["plan"] for tr in t["tiers"] if tr["monthly_usd"] == 0 or tr["annual_monthly_usd"] == 0), None) if t["has_free_plan"] else None
    t["free_is_trial"] = bool(t["free_tier"] and "trial" in t["free_tier"].lower())
    sv = []
    for tr in t["tiers"]:
        m, a = tr["monthly_usd"], tr["annual_monthly_usd"]
        if m and a and a < m:
            sv.append({"plan": tr["plan"], "monthly": m, "annual": a, "pct": round((m - a) / m * 100),
                       "per_year": round((m - a) * 12, 2)})
    t["savings"] = sv
    t["max_saving"] = max(sv, key=lambda s: s["pct"]) if sv else None
    t["annual_only"] = [tr["plan"] for tr in t["tiers"] if tr["annual_monthly_usd"] and not tr["monthly_usd"]]
    t["annual_rows"] = [{"plan": tr["plan"],
                         "annual_total": round(tr["annual_monthly_usd"] * 12, 2) if tr["annual_monthly_usd"] else None,
                         "monthly_total": round(tr["monthly_usd"] * 12, 2) if tr["monthly_usd"] else None}
                        for tr in t["tiers"] if _first_price(tr)]
    # short label for tables: "from $37.60/mo (Outreach Growth, billed annually)"
    if t["pricing_status"] == "contact_sales" and not paid:
        t["entry_label"] = "Contact sales (no public prices)"
    elif t.get("price_display") and t["id"] not in NUMERIC_DISPLAY:
        t["entry_label"] = t["price_display"]
    elif t["cheapest_tier"]:
        ct = t["cheapest_tier"]
        basis = "billed annually" if not ct["monthly_usd"] or (ct["annual_monthly_usd"] and ct["annual_monthly_usd"] < ct["monthly_usd"]) else "billed monthly"
        t["entry_label"] = f"from {money(t['entry_paid'])}/mo ({ct['plan']}, {basis})"
    elif t["has_free_plan"]:
        t["entry_label"] = "Free plan; paid plans not priced publicly"
    else:
        t["entry_label"] = "Contact sales (no public prices)"
    t["credit_cols"] = any("actions_per_month" in tr or "data_credits_per_month" in tr for tr in t["tiers"])
    t["spotlight"] = SPOTLIGHT.get(t["id"])
    if t["id"] == "clay":
        clay_fields(t)
    if t["id"] == "lemlist":
        lemlist_fields(t)
    t["promo_live"] = live_promo(t)
    if t["id"] == "klenty":
        klenty_fields(t)
    if t["id"] == "prospeo":
        prospeo_fields(t)
    t["faq"] = tool_faq(t)
    t["summary"] = tool_summary(t)


NOW_YEAR = dt.date.today().year

# Tool pages that get extra internal links from related pages (top search queries).
SPOTLIGHT = {"clay": "How much does Clay cost? Clay pricing by plan",
             "lemlist": "lemlist pricing: every plan, monthly vs annual",
             "klenty": "Klenty pricing: plans billed annually",
             "prospeo": "Prospeo pricing: free plan and credit costs"}

# Affiliate CTA picks per page: approved programs from data/affiliates.json only.
# "seq" = sequencing alternatives, "data" = lead-data tools (lemlist sells a data add-on, so these fit naturally).
AFF_PICKS = {"lemlist": {"seq": ["woodpecker", "klenty"], "data": ["prospeo", "fullenrich"]},
             "klenty": {"seq": ["woodpecker"], "data": ["prospeo", "fullenrich"]},
             "prospeo": {"data": ["fullenrich"]},
             "apollo": {"seq": ["woodpecker", "klenty"], "data": ["prospeo", "fullenrich"]}}
# Intro line for the "data" picks (default wording is lemlist-specific).
AFF_DATA_INTRO = {"klenty": "Need more emails and phone numbers than Klenty's included data credits?",
                  "prospeo": "Want a second email/phone finder to compare against Prospeo?",
                  "apollo": "Looking for a dedicated email or phone finder instead of Apollo.io's credits?"}

# Spotlight tool pages linked from alternatives pages even when the tool is not a category peer.
ALT_EXTRA_SPOTLIGHT = {"apollo": ["clay"], "instantly": ["clay"]}


def live_promo(t, today=None):
    """A vendor sale from tools.json "promo", only while it runs. Date-gated so the page stops claiming
    the sale on the first build after promo["ends"] (the site rebuilds daily)."""
    p = t.get("promo")
    if not p:
        return None
    today = today or dt.date.today()
    if today > dt.date.fromisoformat(p["ends"]):
        return None
    by = {tr["plan"]: tr for tr in t["tiers"]}
    rows = [f"{plan} {money(v)}/mo (was {money(by[plan]['annual_monthly_usd'])})" for plan, v in p["prices"].items() if plan in by]
    return {**p, "text": (f"{p['label']} sale, verified {nicedate(p['verified'])}, ends {nicedate(p['ends'])}: {p['summary']} - "
                          + ", ".join(rows) + " billed annually. Regular prices are in the table below.")}


def _n(v):
    return f"{v:,}"


def _clay_tiers(t):
    by = {tr["plan"]: tr for tr in t["tiers"]}
    return by["Free"], by["Launch"], by["Growth"], by["Enterprise"]


def clay_fields(t):
    """Answer box, H1, title and meta for /tools/clay/ (targets 'clay pricing' and 'how much is clay'). Numbers come from data/tools.json."""
    free, launch, growth, ent = _clay_tiers(t)
    d = nicedate(t["last_checked"])
    t["answer_box"] = (
        f"How much is Clay? The Free plan is $0 ({_n(free['actions_per_month'])} actions and {_n(free['data_credits_per_month'])} data credits a month). "
        f"Paid plans start with Launch at {money(launch['monthly_usd'])}/month, or {money(launch['annual_monthly_usd'])}/month billed annually, "
        f"which includes {_n(launch['actions_per_month'])} actions and {_n(launch['data_credits_per_month'])} data credits a month; "
        f"Growth is {money(growth['monthly_usd'])}/month ({money(growth['annual_monthly_usd'])} annually) and Enterprise is custom-priced. "
        f"Data credits start at $0.05 each and actions cost under $0.01 each, per Clay's pricing page (checked {d}).")
    t["h1"] = f"Clay pricing {NOW_YEAR}: how much does Clay cost?"
    t["plans_h2"] = "How much is Clay? Cost by plan"
    t["seo_title"] = f"Clay Pricing {NOW_YEAR}: How Much Is Clay? Plans & Credit Costs"
    t["seo_desc"] = (f"How much is Clay? Free plan, Launch {money(launch['monthly_usd'])}/mo ({money(launch['annual_monthly_usd'])} annual), "
                     f"Growth {money(growth['monthly_usd'])}/mo ({money(growth['annual_monthly_usd'])} annual), plus cost per credit. Checked {t['last_checked']}.")


def clay_faq(t):
    free, launch, growth, ent = _clay_tiers(t)
    n = "Clay"
    return [
        {"q": "How much is Clay?", "a": t["answer_box"]},
        {"q": "Is Clay free?",
         "a": (f"Yes, in part. Clay's Free plan costs $0 and includes unlimited seats and tables, {_n(free['actions_per_month'])} actions and "
               f"{_n(free['data_credits_per_month'])} data credits a month, up to 200 rows per table, and no phone number enrichment. "
               f"The paid Launch plan ({money(launch['monthly_usd'])}/month, {money(launch['annual_monthly_usd'])}/month annually) adds phone enrichment "
               f"and larger tables, and Clay's pricing page offers a 14-day trial on paid plans (checked {nicedate(t['last_checked'])}).")},
        {"q": "Clay pricing per credit: how much does a credit cost?",
         "a": ("Clay's pricing page says data credits start at $0.05 each and get cheaper as you grow, and actions start at less than $0.01 each. "
               "Credits and actions are priced separately. If you bring your own API keys for a data provider, the run uses one action and no data credits. "
               "Enrichments that return no result do not use credits or actions. "
               f"As a worked example from the same page, Launch's {_n(launch['data_credits_per_month'])} monthly data credits are {money(launch['data_credits_usd_monthly_billing'])} of its {money(launch['monthly_usd'])}/month "
               f"(about ${launch['data_credits_usd_monthly_billing'] / launch['data_credits_per_month']:.2f} per credit), and Growth's {_n(growth['data_credits_per_month'])} credits are {money(growth['data_credits_usd_monthly_billing'])} of its {money(growth['monthly_usd'])}/month (about ${growth['data_credits_usd_monthly_billing'] / growth['data_credits_per_month']:.3f} per credit).")},
        {"q": "How much does Clay cost per month?",
         "a": (f"Launch is {money(launch['monthly_usd'])}/month billed monthly, or {money(launch['annual_monthly_usd'])}/month billed annually "
               f"({money(launch['annual_monthly_usd'] * 12)} a year). Growth is {money(growth['monthly_usd'])}/month, or {money(growth['annual_monthly_usd'])}/month billed annually "
               f"({money(growth['annual_monthly_usd'] * 12)} a year). Enterprise pricing is custom with an annual commitment.")},
    ]


def _lemlist_tiers(t):
    by = {tr["plan"]: tr for tr in t["tiers"]}
    return by["Email"], by["Multichannel"], by["Enterprise"]


def lemlist_fields(t):
    """Answer box, H1, title and meta for /tools/lemlist/ (targets 'lemlist pricing'). Numbers come from data/tools.json."""
    em, mc, ent = _lemlist_tiers(t)
    d = nicedate(t["date_checked"])
    t["answer_box"] = (
        f"lemlist pricing {NOW_YEAR}: from {money(em['annual_monthly_usd'])}/month. The Email plan is {money(em['monthly_usd'])}/month billed monthly "
        f"or {money(em['annual_monthly_usd'])}/month billed annually (unlimited users, 50,000 emails a month); Multichannel is {money(mc['monthly_usd'])}/month "
        f"or {money(mc['annual_monthly_usd'])}/month billed annually, per user (email, LinkedIn, SMS and calls); Enterprise is custom-priced. "
        f"There is a 14-day free trial but no free plan (verified on lemlist.com/pricing, {d}).")
    t["h1"] = f"lemlist pricing {NOW_YEAR}: plans, cost per month & annual price"
    t["seo_title"] = f"lemlist Pricing {NOW_YEAR}: Plans from {money(em['annual_monthly_usd'])}/mo, Monthly vs Annual"
    t["seo_desc"] = (f"lemlist pricing, verified {t['date_checked']}: Email {money(em['monthly_usd'])}/mo ({money(em['annual_monthly_usd'])} annual), "
                     f"Multichannel {money(mc['monthly_usd'])}/mo ({money(mc['annual_monthly_usd'])} annual) per user, Enterprise custom. Add-ons, trial and alternatives.")


def lemlist_faq(t):
    em, mc, ent = _lemlist_tiers(t)
    d = nicedate(t["date_checked"])
    return [
        {"q": "How much does lemlist cost?", "a": t["answer_box"]},
        {"q": "How much does lemlist cost per month?",
         "a": (f"Billed monthly, lemlist Email is {money(em['monthly_usd'])}/month and Multichannel is {money(mc['monthly_usd'])}/month per user. "
               f"Billed annually they drop to {money(em['annual_monthly_usd'])}/month ({money(em['annual_monthly_usd'] * 12)} a year) and "
               f"{money(mc['annual_monthly_usd'])}/month per user ({money(mc['annual_monthly_usd'] * 12)} a year). Quarterly billing saves 10% (checked {d}).")},
        {"q": "Does lemlist have a free plan?",
         "a": ("No. lemlist has no $0 plan. It offers a 14-day free trial that, per its pricing page, includes the Multichannel plan's features "
               "(except in-app calls) and 200 free credits for finding emails and phone numbers.")},
        {"q": "What do lemlist's add-ons cost?",
         "a": ("Lead data enrichment is $20/month ($16/month billed annually) for 2,000 credits a month (about 400 emails or 100 phone numbers); "
               "buying intent signals are $29/month ($21/month billed annually) for 100 signals a month. lemwarm warm-up is included in every plan, "
               f"and unused credits roll over while the subscription is active (checked {d}).")},
        {"q": "What are the best lemlist alternatives?",
         "a": ("For email sequencing, Woodpecker and Klenty are the closest alternatives we track; for cheaper high-volume cold email, see Instantly and Smartlead. "
               "The full list, sorted by price, is on our lemlist alternatives page.")},
    ]


def lemlist_alt_fields(t, alts):
    """Answer box, title and meta for /alternatives/lemlist/ (targets 'lemlist alternatives')."""
    em, mc, ent = _lemlist_tiers(t)
    d = nicedate(t["date_checked"])
    free = [x for x in alts if x["has_free_plan"]]
    t["alt_answer"] = (
        f"Best lemlist alternatives ({d}): Woodpecker and Klenty for email sequencing, Instantly and Smartlead for high-volume cold email, "
        f"and {len(free)} of the {len(alts)} alternatives below have a free plan. lemlist itself starts at {money(em['annual_monthly_usd'])}/month billed annually "
        f"({money(em['monthly_usd'])} month-to-month) for Email and {money(mc['annual_monthly_usd'])}/month per user for Multichannel, verified on lemlist.com/pricing.")
    t["alt_h1"] = f"Best lemlist alternatives ({NOW_YEAR}): {len(alts)} tools compared by price"
    t["alt_title"] = f"Best lemlist Alternatives {NOW_YEAR}: {len(alts)} Cheaper & Free Tools by Price"
    t["alt_desc"] = (f"{len(alts)} lemlist alternatives sorted by price, {len(free)} with a free plan. lemlist costs {money(em['annual_monthly_usd'])}-{money(em['monthly_usd'])}/mo "
                     f"(Email) and {money(mc['annual_monthly_usd'])}-{money(mc['monthly_usd'])}/mo per user (Multichannel), verified {t['date_checked']}.")
    # Ranked shortlist near the top of /alternatives/lemlist/ (GSC: "lemlist alternatives").
    # Cold-email peers only — warmup-only tools share a category with lemlist but are not substitutes.
    # Prices come from already-enriched entry_label / sort_price (tools.json), not hand-typed.
    cold = [x for x in alts if "Cold email & engagement" in x.get("categories", []) and x.get("sort_price") is not None]
    t["alt_ranked"] = cold[:8]
    t["alt_ranked_heading"] = f"Top lemlist alternatives by price ({NOW_YEAR})"


def _join_and(parts):
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return ", ".join(parts[:-1]) + " and " + parts[-1]


def _from_price(x):
    """Name plus entry price from already-enriched tools.json data, never hand-typed."""
    if x.get("entry_paid") is not None:
        return f"{x['name']} from {money(x['entry_paid'])}/mo"
    return x["name"]


# Closest Apollo.io substitutes we actually track (lead data and/or sales engagement).
# The shortlist is sorted by each tool's sort_price from tools.json.
APOLLO_CLOSEST = (
    "snovio", "woodpecker", "rocketreach", "hunter", "saleshandy",
    "prospeo", "lusha", "instantly", "findymail", "kaspr",
    "klenty", "fullenrich", "lemlist", "clay",
)


def apollo_alt_fields(t, alts):
    """Answer box, title and meta for /alternatives/apollo/ (targets 'Apollo.io alternatives')."""
    d = nicedate(t["last_checked"])
    free = [x for x in alts if x["has_free_plan"]]
    by = {x["id"]: x for x in alts}
    data = [by[i] for i in ("hunter", "snovio", "lusha", "rocketreach", "prospeo") if i in by and by[i].get("entry_paid") is not None]
    outreach = [by[i] for i in ("instantly", "lemlist") if i in by and by[i].get("entry_paid") is not None]
    clay = by.get("clay")
    bits = []
    if data:
        bits.append(f"{_join_and([_from_price(x) for x in data])} for lead data")
    if outreach:
        bits.append(f"{_join_and([_from_price(x) for x in outreach])} for outreach")
    if clay and clay.get("entry_paid") is not None:
        bits.append(f"{_from_price(clay)} for enrichment")
    free_tr = next((tr for tr in t["tiers"] if tr.get("monthly_usd") == 0 or tr.get("annual_monthly_usd") == 0), None)
    free_bit = ""
    if t["has_free_plan"]:
        lim = (free_tr or {}).get("limits") or t.get("free_tier") or "Free"
        free_bit = f", with a Free plan ({lim.rstrip('.')})"
    t["alt_answer"] = (
        f"Best Apollo.io alternatives in {NOW_YEAR} (checked {d}): {'; '.join(bits)}. "
        f"{len(free)} of the {len(alts)} alternatives below have a free plan. "
        f"Apollo.io itself starts at {money(t['entry_paid'])}/month billed annually (Basic){free_bit}.")
    t["alt_h1"] = f"Best Apollo.io Alternatives in {NOW_YEAR}: {len(alts)} tools compared by price"
    t["alt_title"] = f"Best Apollo.io Alternatives {NOW_YEAR}: {len(alts)} Tools Compared by Price"
    t["alt_desc"] = (
        f"{len(alts)} Apollo.io Alternatives sorted by price, {len(free)} with a free plan. "
        f"Apollo.io starts at {money(t['entry_paid'])}/mo billed annually (Basic){free_bit}. "
        f"Checked {t['last_checked']}.")
    ranked = [by[i] for i in APOLLO_CLOSEST if i in by and by[i].get("sort_price") is not None]
    ranked.sort(key=lambda x: x["sort_price"])
    t["alt_ranked"] = ranked[:8]
    t["alt_ranked_heading"] = f"Top Apollo.io Alternatives by price ({NOW_YEAR})"
    t["aff_data_intro"] = AFF_DATA_INTRO["apollo"]
    t["aff_seq_intro"] = "For sales engagement and email sequencing, these are the closest alternatives we track:"


def _by_plan(t):
    return {tr["plan"]: tr for tr in t["tiers"]}


def klenty_fields(t):
    """Answer box, H1, title and meta for /tools/klenty/. Regular prices come from data/tools.json; the sale line only while live."""
    b = _by_plan(t)
    st, gr, pl = b["Starter"], b["Growth"], b["Plus"]
    d = nicedate(t["date_checked"])
    sale = ""
    if t.get("promo_live"):
        pp = t["promo_live"]["prices"]
        sale = (f" Until {nicedate(t['promo_live']['ends'])} a {t['promo_live']['label']} sale cuts these to "
                f"{money(pp['Starter'])}, {money(pp['Growth'])} and {money(pp['Plus'])}.")
    t["answer_box"] = (
        f"Klenty pricing {NOW_YEAR}: from {money(st['annual_monthly_usd'])}/month. Starter is {money(st['annual_monthly_usd'])}/month billed annually "
        f"(unlimited users and mailboxes, 15,000 contacts and 75,000 emails a month), Growth is {money(gr['annual_monthly_usd'])}/user/month and "
        f"Plus is {money(pl['annual_monthly_usd'])}/user/month, both billed annually; Klenty does not publish month-to-month prices. "
        f"There is a 14-day free trial but no free plan (verified on klenty.com/pricing, {d})." + sale)
    t["h1"] = f"Klenty pricing {NOW_YEAR}: plans, cost per month & annual price"
    t["seo_title"] = f"Klenty Pricing {NOW_YEAR}: Plans from {money(st['annual_monthly_usd'])}/mo, Trial & Alternatives"
    t["seo_desc"] = (f"Klenty pricing, verified {t['date_checked']}: Starter {money(st['annual_monthly_usd'])}/mo, Growth {money(gr['annual_monthly_usd'])}/user/mo, "
                     f"Plus {money(pl['annual_monthly_usd'])}/user/mo billed annually. Add-ons, 14-day trial and cheaper alternatives.")
    t["self_cta"] = "Try Klenty free for 14 days"
    t["aff_data_intro"] = AFF_DATA_INTRO["klenty"]


def klenty_faq(t):
    b = _by_plan(t)
    st, gr, pl = b["Starter"], b["Growth"], b["Plus"]
    d = nicedate(t["date_checked"])
    return [
        {"q": "How much does Klenty cost?", "a": t["answer_box"]},
        {"q": "How much does Klenty cost per month?",
         "a": (f"Klenty lists per-month prices billed annually: Starter {money(st['annual_monthly_usd'])}/month ({money(st['annual_monthly_usd'] * 12)} a year), "
               f"Growth {money(gr['annual_monthly_usd'])} per user/month ({money(gr['annual_monthly_usd'] * 12)} a year) and Plus {money(pl['annual_monthly_usd'])} per user/month "
               f"({money(pl['annual_monthly_usd'] * 12)} a year). Add-ons: Power & Parallel Dialer $45 per user/month and Dynamic Presence $50 per seat/month (checked {d}).")},
        {"q": "Does Klenty have a free plan or free trial?",
         "a": ("Klenty has no free plan. Its pricing page offers a 14-day free trial with access to all features and up to 200 emails to prospects; "
               "after the trial you upgrade with a credit card or the account is deactivated.")},
        {"q": "Is Klenty cheaper if you pay annually?",
         "a": ("Klenty shows annual and quarterly billing, and its billing toggle says you save up to 30% with annual. It does not publish "
               "month-to-month or quarterly dollar prices, so we only list the annual-billed per-month prices.")},
        {"q": "What are the best Klenty alternatives?",
         "a": ("For email sequencing, Woodpecker, lemlist, Reply.io and Saleshandy are the closest alternatives we track; Apollo bundles a lead database with sequences. "
               "The full list, sorted by price, is on our Klenty alternatives page.")},
    ]


def prospeo_fields(t):
    """Answer box, H1, title and meta for /tools/prospeo/. Numbers come from data/tools.json."""
    b = _by_plan(t)
    fr, st, gr, pro = b["Free"], b["Starter"], b["Growth"], b["Pro"]
    d = nicedate(t["date_checked"])
    t["answer_box"] = (
        f"Prospeo pricing {NOW_YEAR}: from {money(st['annual_monthly_usd'])}/month. There is a free plan ({fr['limits']}); Starter is "
        f"{money(st['monthly_usd'])}/month or {money(st['annual_monthly_usd'])}/month billed yearly ({st['limits']}), Growth is {money(gr['monthly_usd'])}/month "
        f"or {money(gr['annual_monthly_usd'])}/month yearly ({gr['limits'].split(';')[0]}) and Pro is {money(pro['monthly_usd'])}/month or "
        f"{money(pro['annual_monthly_usd'])}/month yearly ({pro['limits']}). Last verified on prospeo.io/pricing on {d}.")
    t["h1"] = f"Prospeo pricing {NOW_YEAR}: free plan, credits & cost per month"
    t["seo_title"] = f"Prospeo Pricing {NOW_YEAR}: Free Plan, Plans from {money(st['annual_monthly_usd'])}/mo & Credits"
    t["seo_desc"] = (f"Prospeo pricing: free plan, Starter {money(st['monthly_usd'])}/mo ({money(st['annual_monthly_usd'])} yearly), Growth {money(gr['monthly_usd'])}/mo, "
                     f"Pro {money(pro['monthly_usd'])}/mo, credits per plan and alternatives. Last verified {t['date_checked']}.")
    t["self_cta"] = "Try Prospeo free"
    t["aff_data_intro"] = AFF_DATA_INTRO["prospeo"]


def prospeo_faq(t):
    b = _by_plan(t)
    fr, st, gr, pro = b["Free"], b["Starter"], b["Growth"], b["Pro"]
    d = nicedate(t["date_checked"])
    return [
        {"q": "How much does Prospeo cost?", "a": t["answer_box"]},
        {"q": "How much does Prospeo cost per month?",
         "a": (f"Billed monthly: Starter {money(st['monthly_usd'])}, Growth {money(gr['monthly_usd'])} and Pro {money(pro['monthly_usd'])} per month. "
               f"Billed yearly: {money(st['annual_monthly_usd'])}, {money(gr['annual_monthly_usd'])} and {money(pro['annual_monthly_usd'])} per month "
               f"({money(st['annual_monthly_usd'] * 12)}, {money(gr['annual_monthly_usd'] * 12)} and {money(pro['annual_monthly_usd'] * 12)} a year). "
               f"Credits: {st['limits']} on Starter, {gr['limits'].split(';')[0]} on Growth, {pro['limits']} on Pro (last verified {d}).")},
        {"q": "Does Prospeo have a free plan?",
         "a": f"Yes. Prospeo's Free plan costs $0 and includes {fr['limits']} (last verified {d})."},
        {"q": "What are the best Prospeo alternatives?",
         "a": ("The closest email and phone finders we track are Hunter, Apollo, FullEnrich, Findymail, Lusha, Snov.io and RocketReach. "
               "The full list, sorted by price, is on our Prospeo alternatives page.")},
    ]


def answer_free(t):
    n, d = t["name"], t["last_checked"]
    if t["has_free_plan"]:
        s = f"Yes. {n}'s pricing page lists a $0 tier called \"{t['free_tier'] or 'Free'}\" (checked {d})."
        if t["free_is_trial"]:
            s += " It is labelled a trial, so check whether it is time-limited."
        return s
    s = f"No. {n} does not list a $0 plan on its pricing page (checked {d})."
    if t["pricing_status"] == "contact_sales":
        s += " Prices are only available from sales."
    return s


def answer_cost(t):
    n = t["name"]
    if t["pricing_status"] == "contact_sales" and not t["cheapest_tier"]:
        return f"{n} does not publish prices. You need to contact sales for a quote." + (f" {t['verification_note']}" if t.get("verification_note") else "")
    others = [f"{tr['plan']} {tier_price_text(tr)}" for tr in t["tiers"] if _first_price(tr)]
    if t.get("price_display") and t["id"] not in NUMERIC_DISPLAY:
        s = f"{n}'s pricing page lists: {t['price_display']}."
        if others:
            s += " Priced plans/add-ons: " + "; ".join(others) + "."
    elif t["cheapest_tier"]:
        ct = t["cheapest_tier"]
        s = f"The cheapest paid {n} plan is {ct['plan']} at {tier_price_text(ct)}."
        rest = [o for tr, o in zip([tr for tr in t["tiers"] if _first_price(tr)], others) if tr is not ct]
        if rest:
            s += " Other plans: " + "; ".join(rest) + "."
    else:
        s = f"{n} has a free plan, but its paid plans are not priced publicly."
    if t.get("billing_note"):
        s += f" Billing: {t['billing_note'].rstrip('.')}."
    return s


def answer_annual(t):
    n = t["name"]
    if t["id"] == "aisdr":
        # Verified on aisdr.com/pricing (2026-11-12): annual is 20% off quarterly; no public dollar amounts.
        return (f"Yes, for subscription plans quoted by sales. {n}'s pricing page says annual plans give a 20% "
                f"discount compared to quarterly plans. Pay-as-you-go is charged daily at $1.50 per person prospected and has no annual rate.")
    if t["savings"]:
        ms = t["max_saving"]
        s = (f"Yes. Paying annually cuts {n} {ms['plan']} from {money(ms['monthly'])} to {money(ms['annual'])} per month, "
             f"{ms['pct']}% less ({money(ms['per_year'])} saved over a year).")
        if len(t["savings"]) > 1:
            s += " Annual discounts by plan: " + "; ".join(f"{x['plan']} {x['pct']}%" for x in t["savings"]) + "."
        return s
    if t["annual_only"]:
        return f"{n} lists only an annual-billed price for {', '.join(t['annual_only'])}, so there is no monthly price to compare against."
    if t["pricing_status"] == "contact_sales" and not t["cheapest_tier"]:
        return f"{n} does not publish prices, so any annual discount is negotiated with sales."
    if any(tr["monthly_usd"] and tr["annual_monthly_usd"] == tr["monthly_usd"] for tr in t["tiers"]):
        return f"No. {n} lists the same per-month price for monthly and annual billing."
    return f"{n}'s pricing page does not list a separate annual price, so no annual discount is published."


def tool_faq(t):
    n = t["name"]
    faq = [
        {"q": f"How much is {n}?", "a": answer_cost(t)},
        {"q": f"Does {n} have a free plan?", "a": answer_free(t)},
        {"q": f"Is {n} cheaper if you pay annually?", "a": answer_annual(t)},
        {"q": f"When was {n} pricing last checked?",
         "a": f"{t['last_checked']}, from the official pricing page ({t['pricing_url']}). We re-check it automatically every day and log any change."},
    ]
    if t["id"] == "clay" and t.get("answer_box"):  # top GSC query cluster: "clay pricing", "how much is clay"
        faq = clay_faq(t) + [f for f in faq if f["q"] in (f"Is {n} cheaper if you pay annually?", f"When was {n} pricing last checked?")]
    if t["id"] == "lemlist" and t.get("answer_box"):  # GSC: "lemlist pricing", "lemlist cost per month"
        faq = lemlist_faq(t) + [f for f in faq if f["q"] in (f"Is {n} cheaper if you pay annually?", f"When was {n} pricing last checked?")]
    if t["id"] == "klenty" and t.get("answer_box"):
        faq = klenty_faq(t) + [f for f in faq if f["q"] == f"When was {n} pricing last checked?"]
    if t["id"] == "prospeo" and t.get("answer_box"):
        faq = prospeo_faq(t) + [f for f in faq if f["q"] in (f"Is {n} cheaper if you pay annually?", f"When was {n} pricing last checked?")]
    if t["id"] == "aisdr":  # GSC: "aisdr" already ranks near page 1
        faq.insert(1, {
            "q": f"Can I try {n} without a paid subscription?",
            "a": (
                f"You can sign up without a credit card and set up a campaign first; {n}'s pricing page says the paywall appears when you launch. "
                f"There is no $0 plan. Self-serve pay-as-you-go is {t.get('price_display') or '$1.50 per person prospected'}, charged daily."
            ),
        })
    return faq


def tool_summary(t):
    n = t["name"]
    if t["pricing_status"] == "contact_sales" and not t["cheapest_tier"]:
        return (f"{n} does not publish prices: you have to talk to sales to get a quote, and there is "
                f"{'a' if t['has_free_plan'] else 'no'} $0 plan listed. We last checked its pricing page on {t['last_checked']}.")
    parts = [f"{n} lists {len(t['tiers'])} plan{'s' if len(t['tiers']) != 1 else ''} on its pricing page."]
    if t.get("price_display") and t["id"] not in NUMERIC_DISPLAY:
        parts.append(f"Pricing is not a simple monthly plan: {t['price_display']}.")
    elif t["cheapest_tier"]:
        parts.append(f"The cheapest paid plan is {t['cheapest_tier']['plan']} at {tier_price_text(t['cheapest_tier'])}.")
    parts.append(f"There is a $0 tier ({t['free_tier']})." if t["has_free_plan"] else "There is no free plan.")
    if t["max_saving"]:
        parts.append(f"Annual billing saves up to {t['max_saving']['pct']}%.")
    parts.append(f"Prices checked {t['last_checked']} on the official pricing page.")
    return " ".join(parts)


def faq_ld(faq):
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [{"@type": "Question", "name": f["q"], "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in faq]}


def rank(tools):
    """Featured (paid) first, then numeric entry price asc, then non-USD/usage-based, free-only, contact sales."""
    def key(t):
        if t["sort_price"] is not None:
            g = 0
        elif t.get("price_display"):
            g = 1
        elif t["has_free_plan"]:
            g = 2
        else:
            g = 3
        return (not t["is_featured"], g, t["sort_price"] or 0, t["name"].lower())
    return sorted(tools, key=key)


def peers(t, tools):
    return [x for x in tools if x["id"] != t["id"] and (t["category"] in x["categories"] or x["category"] in t["categories"])]


def names(ts):
    ts = [t["name"] for t in ts]
    return ", ".join(ts[:-1]) + (" and " if len(ts) > 1 else "") + ts[-1] if ts else ""


def alternatives_faq(t, alts):
    n = t["name"]
    priced = [x for x in alts if x["sort_price"] is not None and not x["is_featured"]]
    free = [x for x in alts if x["has_free_plan"]]
    contact = [x for x in alts if x["pricing_status"] == "contact_sales" and not x["cheapest_tier"]]
    out = []
    free_alt_a = (f"Yes. {len(free)} alternative{'s' if len(free) != 1 else ''} list a $0 tier: {names(free)}." if free
                  else f"None of the {len(alts)} alternatives we track lists a $0 tier.")
    # Lead with pricing FAQs on pages already getting GSC impressions (lemlist, Instantly, Apollo).
    if t["id"] in ("lemlist", "instantly", "apollo"):
        out.append({"q": f"How much is {n}?", "a": answer_cost(t)})
        out.append({"q": f"Does {n} have a free plan?", "a": answer_free(t)})
        if t["id"] == "lemlist" and t.get("answer_box"):
            out[0] = {"q": "How much does lemlist cost?", "a": t["answer_box"]}
            out.insert(0, {"q": "What are the best lemlist alternatives?", "a": t.get("alt_answer") or ""})
        elif t["id"] == "lemlist":
            out.append({"q": f"How much does {n} cost per month?", "a": answer_cost(t)})
        elif t["id"] == "apollo" and t.get("alt_answer"):
            out[0] = {"q": "How much does Apollo.io cost?", "a": answer_cost(t)}
            out.insert(0, {"q": "What are the best Apollo.io alternatives?", "a": t["alt_answer"]})
        out.append({"q": f"Is there a free {n} alternative?", "a": free_alt_a})
    if priced:
        c = min(priced, key=lambda x: x["sort_price"])
        a = f"Among the {len(alts)} alternatives we track, {c['name']} has the lowest listed paid entry price: {c['entry_label']}."
        if t["sort_price"] is not None:
            cheaper = [x for x in priced if x["sort_price"] < t["sort_price"]]
            a += f" {len(cheaper)} alternative{'s' if len(cheaper) != 1 else ''} list a lower entry price than {n} ({t['entry_label']})."
        out.append({"q": f"What is the cheapest {n} alternative?", "a": a})
    if t["id"] not in ("lemlist", "instantly", "apollo"):
        out.append({"q": f"Is there a free alternative to {n}?", "a": free_alt_a})
    if contact:
        out.append({"q": f"Which {n} alternatives don't publish pricing?",
                    "a": f"{names(contact)} only offer pricing through sales."})
    return out


def roundup_faq(kind, label, ts):
    priced = [x for x in ts if x["sort_price"] is not None and not x["is_featured"]]
    free = [x for x in ts if x["has_free_plan"]]
    contact = [x for x in ts if x["pricing_status"] == "contact_sales" and not x["cheapest_tier"]]
    sav = sorted([x for x in ts if x["max_saving"]], key=lambda x: -x["max_saving"]["pct"])
    out = []
    if priced and kind in ("cheapest", "annual"):
        c = min(priced, key=lambda x: x["sort_price"])
        out.append({"q": f"What is the cheapest {label} tool?",
                    "a": f"Of the {len(ts)} {label} tools we track, {c['name']} has the lowest listed paid entry price: {c['entry_label']}." +
                         (" " + "; ".join(f"{x['name']} {x['entry_label']}" for x in sorted(priced, key=lambda x: x['sort_price'])[1:3]) + " come next." if len(priced) > 1 else "")})
    if kind == "free":
        tr = [x for x in free if x["free_is_trial"]]
        out.append({"q": f"Which {label} tools have a free plan?",
                    "a": f"{len(free)} of the {len(ts)} {label} tools we track list a $0 tier: {names(free)}." if free else f"None of the {label} tools we track lists a $0 tier."})
        fp = [x for x in free if x["sort_price"] is not None]
        if fp:
            c = min(fp, key=lambda x: x["sort_price"])
            out.append({"q": f"Which free {label} tool is cheapest to upgrade?",
                        "a": f"{c['name']}: after the free tier, paid plans start {c['entry_label']}."})
        if tr:
            out.append({"q": "Are these free plans or free trials?",
                        "a": f"Most are listed as free plans. {names(tr)} label{'s' if len(tr) == 1 else ''} the $0 tier as a trial, so it may be time-limited."})
    else:
        out.append({"q": f"Which {label} tools have a free plan?",
                    "a": f"{names(free)} list a $0 tier." if free else f"None of the {label} tools we track lists a $0 tier."})
    if kind in ("cheapest", "annual"):
        out.append({"q": f"Is annual billing cheaper for {label} tools?",
                    "a": (f"Often. {len(sav)} of {len(ts)} tools publish a lower per-month price for annual billing. The biggest listed discount is "
                          f"{sav[0]['name']} {sav[0]['max_saving']['plan']} ({sav[0]['max_saving']['pct']}% off: {money(sav[0]['max_saving']['monthly'])} → {money(sav[0]['max_saving']['annual'])}/mo).")
                         if sav else f"None of the {label} tools we track publishes a separate, lower annual price."})
    if contact:
        out.append({"q": f"Which {label} tools don't publish pricing?", "a": f"{names(contact)} require a sales conversation for pricing."})
    return out


# ---- dated one-line answers shown at the top of tool / comparison / roundup / alternatives pages ----
def nicedate(d):
    import datetime as dt
    return dt.date.fromisoformat(d).strftime("%b %-d, %Y")


def _starts(t):
    """'starts at $37.60/month billed annually ($47 month-to-month)' style fragment, or None."""
    ct = t["cheapest_tier"]
    if not ct or (t.get("price_display") and t["id"] not in NUMERIC_DISPLAY):
        return None
    m, a = ct["monthly_usd"], ct["annual_monthly_usd"]
    if m and a and a < m:
        return f"starts at {money(a)}/month billed annually ({money(m)} month-to-month)"
    if m:
        return f"starts at {money(m)}/month"
    return f"starts at {money(a)}/month billed annually"


def _generic(plan):
    return plan.lower().startswith(("plans", "from", "pricing"))


def _who(t):
    """"Instantly's Outreach Growth plan" or just "Warmy" when the plan has no real name."""
    p = t["cheapest_tier"]["plan"]
    return t["name"] if _generic(p) else f"{t['name']}'s {p} plan"


def answer_line_tool(t):
    n, d = t["name"], nicedate(t["last_checked"])
    free = f"; there is also a $0 plan ({t['free_tier']})" if t["has_free_plan"] and t["free_tier"] else ""
    st = _starts(t)
    if st:
        plan = "" if _generic(t["cheapest_tier"]["plan"]) else f"; the cheapest paid plan is {t['cheapest_tier']['plan']}"
        return f"As of {d}, {n} {st}{plan}{free}."
    if t.get("price_display") and t["id"] not in NUMERIC_DISPLAY:
        s = f"As of {d}, {n} does not sell a simple monthly plan: {t['price_display'].rstrip('.')}"
        if t.get("cheapest_tier") and t.get("entry_paid"):
            ct = t["cheapest_tier"]
            plan = "" if _generic(ct["plan"]) else f" ({ct['plan']})"
            s += f"; fixed add-ons start at {money(t['entry_paid'])}/month{plan}"
        return s + f"{free}."
    if t["has_free_plan"]:
        return f"As of {d}, {n} has a free plan ({t['free_tier'] or 'Free'}), but its paid plans are not priced publicly."
    return f"As of {d}, {n} does not publish prices; you have to contact sales for a quote, and there is no free plan."


def _latest(ts):
    return nicedate(max(t["last_checked"] for t in ts))


def monthly_entry(t):
    """Cheapest positive month-to-month price, or None."""
    v = [x["monthly_usd"] for x in t.get("tiers", []) if isinstance(x.get("monthly_usd"), (int, float)) and x["monthly_usd"] > 0]
    return min(v) if v else None


def answer_line_compare(a, b):
    d = _latest([a, b])
    sa, sb = a["sort_price"], b["sort_price"]
    def frag(t):
        st = _starts(t)
        if st:
            return f"{_who(t)} {st}"
        if t.get("price_display") and t["id"] not in NUMERIC_DISPLAY:
            s = f"{t['name']} is priced as {t['price_display']}"
            if t.get("cheapest_tier") and t.get("entry_paid"):
                s += f" (fixed add-ons from {money(t['entry_paid'])}/mo)"
            return s
        if t["entry_label"].startswith("Contact"):
            return f"{t['name']} does not publish prices (contact sales)"
        if t["entry_label"].startswith("Free"):
            return f"{t['name']} has a free plan but no public paid prices"
        return f"{t['name']} is priced as {t['entry_label']}"
    s = f"As of {d}, {frag(a)}, while {frag(b)}"
    if sa is not None and sb is not None and sa != sb:
        lo = a if sa < sb else b
        ma, mb = monthly_entry(a), monthly_entry(b)
        if ma is not None and ma == mb and not (a.get("price_display") or b.get("price_display")):
            s += f"; on month-to-month billing both start at {money(ma)}, so {lo['name']} is cheaper only if you pay yearly"
        else:
            s += f"; {lo['name']} has the cheaper entry plan"
    return s + "."


def answer_line_roundup(r):
    ts = r["tools"]
    if not ts:
        return ""
    d = _latest(ts)
    label, n = r["label"], len(ts)
    priced = [x for x in ts if x["sort_price"] is not None]
    free = [x for x in ts if x["has_free_plan"]]
    if r["kind"] == "cheapest":
        if priced:
            c = min(priced, key=lambda x: x["sort_price"])
            return (f"As of {d}, the cheapest {label} option we track is {_who(c)}, which {_starts(c)}; "
                    f"{len(free)} of {n} have a free plan.")
        return f"As of {d}, none of the {n} {label} tools we track publishes a fixed monthly price; {len(free)} have a free plan."
    if r["kind"] == "free":
        fp = [x for x in free if x["sort_price"] is not None]
        s = f"As of {d}, {len(free)} {label} tools we track have a $0 plan"
        if fp:
            c = min(fp, key=lambda x: x["sort_price"])
            s += f"; the cheapest to upgrade is {c['name']}, whose first paid plan" + ("" if _generic(c["cheapest_tier"]["plan"]) else f" ({c['cheapest_tier']['plan']})") + f" {_starts(c)}"
        return s + "."
    sav = sorted([x for x in ts if x["max_saving"]], key=lambda x: -x["max_saving"]["pct"])
    if sav:
        b = sav[0]
        ms = b["max_saving"]
        return (f"As of {d}, {len(sav)} of {n} {label} tools publish a lower price for annual billing; the biggest discount is "
                f"{b['name']} {ms['plan']} at {ms['pct']}% off ({money(ms['monthly'])} → {money(ms['annual'])}/month).")
    return f"As of {d}, none of the {n} {label} tools we track publishes a separate annual price."


def answer_line_alternatives(t, alts):
    if not alts:
        return ""
    d = _latest([t] + alts)
    priced = [x for x in alts if x["sort_price"] is not None and not x["is_featured"]]
    free = [x for x in alts if x["has_free_plan"]]
    s = f"As of {d}, "
    if priced:
        c = min(priced, key=lambda x: x["sort_price"])
        s += f"the cheapest {t['name']} alternative we track is {_who(c)}, which {_starts(c)}; "
    s += f"{len(free)} of {len(alts)} alternatives have a free plan"
    st = _starts(t)
    s += f", and {t['name']} itself {st}." if st else "."
    return s
