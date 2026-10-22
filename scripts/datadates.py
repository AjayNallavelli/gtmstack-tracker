"""Per-tool "data last changed" ledger (data/data_dates.json), used for truthful sitemap <lastmod>.

A tool's record in data/tools.json is fingerprinted (pricing fields only). When the fingerprint differs
from the ledger, the ledger date moves to `today`. snapshot.py calls update() on every daily run, so the
date is committed with the daily data; build.py calls it too so a local build reflects manual edits.
"""
import hashlib, json
from pathlib import Path

PATH = Path(__file__).resolve().parent.parent / "data" / "data_dates.json"
FIELDS = ("name", "description", "categories", "pricing_status", "billing_note", "verification_note",
          "tiers", "has_free_plan", "price_display", "starting_price_usd", "pricing_url")


def fingerprint(t):
    return hashlib.sha256(json.dumps({k: t.get(k) for k in FIELDS}, sort_keys=True).encode()).hexdigest()[:16]


def load():
    return json.loads(PATH.read_text()) if PATH.exists() else {}


def update(tools, today, write=True):
    led = load()
    changed = False
    for t in tools:
        fp = fingerprint(t)
        cur = led.get(t["id"])
        if not cur or cur.get("hash") != fp:
            led[t["id"]] = {"hash": fp, "date": today}
            changed = True
    if changed and write:
        PATH.write_text(json.dumps(dict(sorted(led.items())), indent=1) + "\n")
    return {k: v["date"] for k, v in led.items()}
