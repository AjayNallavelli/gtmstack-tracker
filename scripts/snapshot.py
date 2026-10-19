#!/usr/bin/env python3
"""GTMStack Tracker - daily pricing snapshot + diff.

Usage:  python scripts/snapshot.py [--only id1,id2] [--date YYYY-MM-DD] [--workers 6]

For every tool in data/tools.json it fetches the pricing page, extracts and
normalizes the visible text, stores a dated snapshot in data/snapshots/<date>/,
and diffs the extracted price points / pricing lines against the previous
snapshot for that tool. Differences are appended to data/changes.json.
"""
import argparse, concurrent.futures as cf, datetime as dt, difflib, hashlib, json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
SNAP = DATA / "snapshots"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"
CUR = r"(?:US\$|\$|€|£|₹)"
PRICE_RE = re.compile(CUR + r"\s?\d[\d,]*(?:\.\d+)?(?:\s?[kKmM]\b)?")
PRICE_HINT = re.compile(CUR + r"|\b(per (user|seat|month|mailbox)|/mo\b|/month|billed|annually|monthly|contact sales|custom pricing|talk to sales|free)\b", re.I)
CHROME_BINS = ["google-chrome", "chromium", "chromium-browser", "google-chrome-stable"]


def find_chrome():
    if os.environ.get("CHROME_BIN") and shutil.which(os.environ["CHROME_BIN"]):
        return shutil.which(os.environ["CHROME_BIN"])
    for b in CHROME_BINS:
        p = shutil.which(b)
        if p:
            return p
    return None


def fetch_http(url):
    r = requests.get(url, headers={"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}, timeout=30)
    r.raise_for_status()
    return r.text


def fetch_chrome(url, chrome):
    with tempfile.TemporaryDirectory() as prof:
        out = subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", f"--user-data-dir={prof}",
                              "--virtual-time-budget=15000", f"--user-agent={UA}", "--lang=en-US", "--dump-dom", url],
                             capture_output=True, text=True, timeout=90)
    if len(out.stdout) < 500:
        raise RuntimeError("chrome returned empty DOM")
    return out.stdout


def html_to_lines(html):
    s = BeautifulSoup(html, "lxml")
    for t in s(["script", "style", "noscript", "svg", "header", "footer", "nav", "iframe", "template"]):
        t.decompose()
    raw = [re.sub(r"\s+", " ", l).strip() for l in s.get_text("\n").split("\n")]
    raw = [l for l in raw if l]
    # glue split prices: "$" / "49" / ".00" -> "$49.00"
    lines, i = [], 0
    while i < len(raw):
        l = raw[i]
        if re.fullmatch(CUR, l) and i + 1 < len(raw) and re.fullmatch(r"\d[\d,]*", raw[i + 1]):
            l = l + raw[i + 1]; i += 1
            if i + 1 < len(raw) and re.fullmatch(r"\.\d+", raw[i + 1]):
                l += raw[i + 1]; i += 1
        if not lines or lines[-1] != l:
            lines.append(l)
        i += 1
    return lines


def normalize(lines):
    """Return (pricing_lines, price_tokens). Pricing lines are short lines that carry a
    currency amount or pricing keyword, plus the previous line as label context."""
    keep = []
    for i, l in enumerate(lines):
        if len(l) > 220:
            continue
        if PRICE_HINT.search(l):
            if i > 0 and len(lines[i - 1]) <= 80 and (not keep or keep[-1] != lines[i - 1]):
                keep.append(lines[i - 1])
            if not keep or keep[-1] != l:
                keep.append(l)
    tokens = sorted({re.sub(r"\s", "", m.group(0)) for l in keep for m in PRICE_RE.finditer(l)})
    return keep, tokens


def snapshot_tool(tool, chrome):
    url, method = tool["pricing_url"], tool.get("fetch_method", "http")
    err = None
    html = None
    order = ["chrome", "http"] if method == "chrome" else ["http", "chrome"]
    for m in order:
        try:
            if m == "chrome":
                if not chrome:
                    continue
                html = fetch_chrome(url, chrome)
            else:
                html = fetch_http(url)
            lines = html_to_lines(html)
            if len(lines) < 5:
                raise RuntimeError("too little text")
            used = m
            break
        except Exception as e:  # try next method
            err = f"{m}: {e}"[:300]
            html = None
    if html is None:
        return {"id": tool["id"], "status": "error", "error": err}
    plines, tokens = normalize(lines)
    return {"id": tool["id"], "status": "ok", "method": used, "url": url, "text": "\n".join(lines),
            "pricing_lines": plines, "price_tokens": tokens,
            "hash": hashlib.sha256("\n".join(plines).encode()).hexdigest()[:16]}


def latest_previous(tool_id, today):
    if not SNAP.exists():
        return None
    for d in sorted((p.name for p in SNAP.iterdir() if p.is_dir()), reverse=True):
        if d < today and (SNAP / d / f"{tool_id}.json").exists():
            return json.loads((SNAP / d / f"{tool_id}.json").read_text())
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--rebaseline", action="store_true",
                    help="store snapshots as a fresh baseline without logging diffs (e.g. first run from a new region)")
    ap.add_argument("--baseline-marker", default="",
                    help="path to a marker file; if it does not exist, run in --rebaseline mode and create it")
    a = ap.parse_args()
    marker = Path(a.baseline_marker) if a.baseline_marker else None
    if marker and not marker.is_absolute():
        marker = ROOT / marker
    if marker and not marker.exists():
        a.rebaseline = True
        print(f"Baseline marker {marker} missing -> re-baseline run (no diffs will be logged)")
    tools = json.loads((DATA / "tools.json").read_text())["tools"]
    if a.only:
        ids = set(a.only.split(","))
        tools = [t for t in tools if t["id"] in ids]
    chrome = find_chrome()
    print(f"Snapshotting {len(tools)} tools for {a.date} (chrome: {chrome or 'not found'})")
    outdir = SNAP / a.date
    outdir.mkdir(parents=True, exist_ok=True)
    changes_path = DATA / "changes.json"
    changes = json.loads(changes_path.read_text()) if changes_path.exists() else []
    if not a.rebaseline:
        # drop entries previously written for this same date (idempotent re-runs)
        changes = [c for c in changes if c["date"] != a.date]
    has_baseline = {c["tool_id"] for c in changes if c["type"] == "baseline"}
    new = []
    with cf.ThreadPoolExecutor(a.workers) as ex:
        results = list(ex.map(lambda t: snapshot_tool(t, chrome), tools))
    names = {t["id"]: t["name"] for t in tools}
    for r in results:
        tid = r["id"]
        prev = latest_previous(tid, a.date)
        if r["status"] != "ok":
            print(f"  ! {tid}: {r['error']}")
            if a.rebaseline:
                continue  # keep whatever snapshot we already have
            (outdir / f"{tid}.json").write_text(json.dumps({"id": tid, "date": a.date, "status": "error", "error": r["error"]}, indent=1))
            new.append({"date": a.date, "tool_id": tid, "tool": names[tid], "type": "fetch_failed", "summary": "Pricing page could not be fetched; will retry tomorrow."})
            continue
        (outdir / f"{tid}.txt").write_text(r["text"])
        meta = {k: r[k] for k in ("id", "status", "method", "url", "hash", "price_tokens", "pricing_lines")}
        meta["date"] = a.date
        (outdir / f"{tid}.json").write_text(json.dumps(meta, indent=1, ensure_ascii=False))
        print(f"  ok {tid:18s} {r['method']:6s} {len(r['price_tokens'])} price points")
        if a.rebaseline:
            if tid not in has_baseline:
                changes = [c for c in changes if not (c["tool_id"] == tid and c["type"] == "fetch_failed")]
                new.append({"date": a.date, "tool_id": tid, "tool": names[tid], "type": "baseline",
                            "summary": f"Tracking started: {len(r['price_tokens'])} price points captured from the pricing page.",
                            "price_points": r["price_tokens"]})
            continue
        if prev is None or prev.get("status") != "ok":
            new.append({"date": a.date, "tool_id": tid, "tool": names[tid], "type": "baseline",
                        "summary": f"Tracking started: {len(r['price_tokens'])} price points captured from the pricing page.",
                        "price_points": r["price_tokens"]})
            continue
        if prev["hash"] == r["hash"]:
            continue
        added = sorted(set(r["price_tokens"]) - set(prev["price_tokens"]))
        removed = sorted(set(prev["price_tokens"]) - set(r["price_tokens"]))
        diff = [l for l in difflib.unified_diff(prev["pricing_lines"], r["pricing_lines"], lineterm="", n=0)
                if l[:1] in "+-" and not l.startswith(("+++", "---"))][:40]
        if added or removed:
            parts = []
            if added: parts.append("new price points " + ", ".join(added[:8]))
            if removed: parts.append("removed " + ", ".join(removed[:8]))
            new.append({"date": a.date, "tool_id": tid, "tool": names[tid], "type": "price_change",
                        "summary": "Pricing page changed: " + "; ".join(parts) + ".", "added": added, "removed": removed,
                        "previous_date": prev["date"], "diff": diff})
        else:
            new.append({"date": a.date, "tool_id": tid, "tool": names[tid], "type": "copy_change",
                        "summary": "Pricing page wording/plan text changed (no price points changed).",
                        "previous_date": prev["date"], "diff": diff})
    changes = new + changes
    changes.sort(key=lambda c: c["date"], reverse=True)
    changes_path.write_text(json.dumps(changes, indent=1, ensure_ascii=False))
    if a.rebaseline and marker:
        marker.write_text(json.dumps({"rebaselined_on": a.date, "reason": "first run from CI region"}, indent=1) + "\n")
    print(f"Wrote {len(new)} change entries ({sum(c['type']=='price_change' for c in new)} price changes) to {changes_path}")


if __name__ == "__main__":
    main()
