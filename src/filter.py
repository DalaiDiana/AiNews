"""Krok 3b — Filter. Necha len cerstve (poslednych N dni) a AI-relevantne polozky."""
import datetime as dt
import re
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Siroky AI pred-filter (lacny, kodovy). Cielom je vyhodit zjavny sum,
# nie byt presny - presne triedenie robi az model.
AI_TERMS = [
    "ai", "a.i.", "artificial intelligence", "machine learning", " ml ", "llm",
    "neural", "deep learning", "model", "gpt", "claude", "gemini", "llama",
    "openai", "anthropic", "deepmind", "nvidia", "agent", "robot", "humanoid",
    "chatbot", "generative", "diffusion", "transformer", "inference", "dataset",
    "autonomous", "self-driving", "computer vision", "speech", "multimodal",
]


def _load_keywords():
    with open(ROOT / "config" / "categories.yaml", encoding="utf-8") as f:
        cats = yaml.safe_load(f)["categories"]
    kws = set()
    for c in cats:
        for k in c.get("keywords", []):
            kws.add(k.lower())
    return kws


_EXTRA = _load_keywords()


def is_ai_relevant(item):
    text = (item["title"] + " " + item["summary"]).lower()
    if any(t in text for t in AI_TERMS):
        return True
    return any(k in text for k in _EXTRA)


def filter_items(items, max_age_days=1):
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=max_age_days)
    out = []
    for it in items:
        try:
            pub = dt.datetime.fromisoformat(it["published"])
        except Exception:
            continue
        if pub < cutoff:
            continue
        if not is_ai_relevant(it):
            continue
        out.append(it)
    return out
