"""Buyer-intent helpers for the static build: derived pricing facts, FAQ text, roundups and alternatives.

Everything here is derived from data/tools.json only. Nothing is invented: when a vendor does not publish a
price the text says so ("contact sales"), and usage-based / non-USD pricing is quoted verbatim from price_display.
"""
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
    t["faq"] = tool_faq(t)
    t["summary"] = tool_summary(t)


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
    return [
        {"q": f"Does {n} have a free plan?", "a": answer_free(t)},
        {"q": f"How much does {n} cost per month?", "a": answer_cost(t)},
        {"q": f"Is {n} cheaper if you pay annually?", "a": answer_annual(t)},
        {"q": f"When was {n} pricing last checked?",
         "a": f"{t['last_checked']}, from the official pricing page ({t['pricing_url']}). We re-check it automatically every day and log any change."},
    ]


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
    if priced:
        c = min(priced, key=lambda x: x["sort_price"])
        a = f"Among the {len(alts)} alternatives we track, {c['name']} has the lowest listed paid entry price: {c['entry_label']}."
        if t["sort_price"] is not None:
            cheaper = [x for x in priced if x["sort_price"] < t["sort_price"]]
            a += f" {len(cheaper)} alternative{'s' if len(cheaper) != 1 else ''} list a lower entry price than {n} ({t['entry_label']})."
        out.append({"q": f"What is the cheapest {n} alternative?", "a": a})
    out.append({"q": f"Is there a free alternative to {n}?",
                "a": (f"Yes. {len(free)} alternative{'s' if len(free) != 1 else ''} list a $0 tier: {names(free)}." if free
                      else f"None of the {len(alts)} alternatives we track lists a $0 tier.")})
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
        return f"As of {d}, {n} does not sell a simple monthly plan: {t['price_display'].rstrip('.')}{free}."
    if t["has_free_plan"]:
        return f"As of {d}, {n} has a free plan ({t['free_tier'] or 'Free'}), but its paid plans are not priced publicly."
    return f"As of {d}, {n} does not publish prices; you have to contact sales for a quote, and there is no free plan."


def _latest(ts):
    return nicedate(max(t["last_checked"] for t in ts))


def answer_line_compare(a, b):
    d = _latest([a, b])
    sa, sb = a["sort_price"], b["sort_price"]
    def frag(t):
        st = _starts(t)
        if st:
            return f"{_who(t)} {st}"
        if t["entry_label"].startswith("Contact"):
            return f"{t['name']} does not publish prices (contact sales)"
        if t["entry_label"].startswith("Free"):
            return f"{t['name']} has a free plan but no public paid prices"
        return f"{t['name']} is priced as {t['entry_label']}"
    s = f"As of {d}, {frag(a)}, while {frag(b)}"
    if sa is not None and sb is not None and sa != sb:
        lo = a if sa < sb else b
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
