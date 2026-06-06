"""Krok 3c — Deduplikacia. Ten isty clanok z viacerych zdrojov => necha originalovy.

Cisto kodove (bez modelu) a rychle (O(n)): normalizacia URL + kluc z titulku.
"""
import re
from urllib.parse import urlparse, parse_qsl, urlunparse

_TRACK = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
          "ref", "source", "fbclid", "gclid", "oc"}


def canonical_url(url):
    try:
        p = urlparse(url)
        q = [(k, v) for k, v in parse_qsl(p.query) if k.lower() not in _TRACK]
        netloc = p.netloc.lower().replace("www.", "")
        path = p.path.rstrip("/")
        return urlunparse(("https", netloc, path, "", "&".join(f"{k}={v}" for k, v in q), ""))
    except Exception:
        return url


def _title_key(t):
    # normalizovaný kľúč z titulku (prvých ~70 znakov) — zachytí rovnaké/skoro rovnaké titulky
    return re.sub(r"[^a-z0-9 ]", "", t.lower()).strip()[:70]


def dedup(items):
    """Necha najstarsi (= najpravdepodobnejsi originalovy) z duplikatov. O(n)."""
    items = sorted(items, key=lambda x: x["published"])  # od najstarsieho
    kept = []
    seen_urls = set()
    seen_titles = set()
    for it in items:
        cu = canonical_url(it["url"])
        tk = _title_key(it["title"])
        if cu in seen_urls or (tk and tk in seen_titles):
            continue
        seen_urls.add(cu)
        if tk:
            seen_titles.add(tk)
        it["canonical_url"] = cu
        kept.append(it)
    return kept
