"""Krok 3c — Deduplikacia. Ten isty clanok z viacerych zdrojov => necha originalovy.

Cisto kodove (bez modelu): normalizacia URL + podobnost titulkov.
"""
import re
from urllib.parse import urlparse, parse_qsl, urlunparse
from difflib import SequenceMatcher

# parametre, ktore len sleduju kampane (vyhodime ich pri normalizacii URL)
_TRACK = {"utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
          "ref", "source", "fbclid", "gclid"}


def canonical_url(url):
    try:
        p = urlparse(url)
        q = [(k, v) for k, v in parse_qsl(p.query) if k.lower() not in _TRACK]
        netloc = p.netloc.lower().replace("www.", "")
        path = p.path.rstrip("/")
        return urlunparse(("https", netloc, path, "", "&".join(f"{k}={v}" for k, v in q), ""))
    except Exception:
        return url


def _norm_title(t):
    return re.sub(r"[^a-z0-9 ]", "", t.lower()).strip()


def _similar(a, b):
    return SequenceMatcher(None, a, b).ratio()


def dedup(items, title_threshold=0.85):
    """Necha najstarsi (= najpravdepodobnejsi originalovy) z duplikatov."""
    items = sorted(items, key=lambda x: x["published"])  # od najstarsieho
    kept = []
    seen_urls = set()
    norm_titles = []
    for it in items:
        cu = canonical_url(it["url"])
        if cu in seen_urls:
            continue
        nt = _norm_title(it["title"])
        if any(_similar(nt, prev) >= title_threshold for prev in norm_titles):
            continue
        seen_urls.add(cu)
        norm_titles.append(nt)
        it["canonical_url"] = cu
        kept.append(it)
    return kept
