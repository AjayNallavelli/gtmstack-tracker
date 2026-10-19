#!/usr/bin/env python3
"""Check every internal link/asset in dist/ resolves to a built file. Usage: python scripts/check_links.py [dist]"""
import sys, re
from pathlib import Path
from urllib.parse import urlparse
from bs4 import BeautifulSoup
dist = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "dist")
import json, os
_site = json.loads((Path(__file__).resolve().parent.parent / "site.json").read_text())
BASE = urlparse(os.environ.get("SITE_URL", _site["base_url"])).path.rstrip("/")
bad, n, ext_sponsored_missing = [], 0, []
for f in dist.rglob("*.html"):
    s = BeautifulSoup(f.read_text(), "lxml")
    for tag, attr in (("a", "href"), ("link", "href"), ("script", "src"), ("img", "src")):
        for el in s.find_all(tag):
            u = el.get(attr)
            if not u or u.startswith(("mailto:", "#", "javascript:")):
                continue
            p = urlparse(u)
            if p.scheme in ("http", "https"):
                # affiliate links must be rel=sponsored
                if (el.find_next_sibling("span", class_="tag-aff") is not None or el.find_next_sibling("span", class_="tag-feat") is not None) and "sponsored" not in (el.get("rel") or []):
                    ext_sponsored_missing.append((str(f), u))
                continue
            n += 1
            if p.path.startswith("/") and BASE:
                if not (p.path == BASE or p.path.startswith(BASE + "/")):
                    bad.append((str(f.relative_to(dist)), u + "  (missing base path)")); continue
                p = p._replace(path=p.path[len(BASE):] or "/")
            path = p.path if p.path.startswith("/") else str((Path("/") / f.parent.relative_to(dist) / p.path))
            target = dist / path.lstrip("/")
            if path.endswith("/"):
                target = target / "index.html"
            if not target.exists():
                bad.append((str(f.relative_to(dist)), u))
print(f"checked {n} internal links across {len(list(dist.rglob('*.html')))} pages; broken: {len(bad)}; affiliate/featured links missing rel=sponsored: {len(ext_sponsored_missing)}")
for b in bad[:50]:
    print("  BROKEN", b)
sys.exit(1 if bad or ext_sponsored_missing else 0)
