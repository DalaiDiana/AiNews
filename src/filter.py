"""Krok 3b — Filter. Necha len cerstve (poslednych N dni) a NAOZAJ AI-relevantne polozky.

AI relevanciu urcuje slovnik v config/ai_terms.yaml (lahko rozsiritelny).
Nepouziva kluc. slova kategorii (tie obsahuju napr. nazvy krajin -> prepustali by vsetko).
"""
import datetime as dt
import re
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_terms():
    with open(ROOT / "config" / "ai_terms.yaml", encoding="utf-8") as f:
        d = yaml.safe_load(f)
    wb = d.get("word_boundary", [])
    sub = d.get("substring", [])
    wb_re = re.compile(r"\b(?:" + "|".join(re.escape(t) for t in wb) + r")\b", re.IGNORECASE)
    sub_re = re.compile("|".join(re.escape(t) for t in sub), re.IGNORECASE)
    return wb_re, sub_re


_WB_RE, _SUB_RE = _load_terms()


def is_ai_relevant(item):
    text = item["title"] + " " + item["summary"]
    return bool(_WB_RE.search(text) or _SUB_RE.search(text))


def filter_since(items, since):
    """Necha len AI-relevantne polozky s casom publikovania > since (datetime, aware)."""
    out = []
    for it in items:
        try:
            pub = dt.datetime.fromisoformat(it["published"])
        except Exception:
            continue
        if pub <= since:
            continue
        if not is_ai_relevant(it):
            continue
        out.append(it)
    return out


def filter_items(items, max_age_days=1):
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=max_age_days)
    return filter_since(items, cutoff)
