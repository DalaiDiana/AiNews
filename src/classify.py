"""Krok 6 — Zaradenie do JEDNEJ kategorie.

Dva rezimy:
  * keyword (default, bez API) — lacny pred-MVP fallback, skore podla klucovych slov.
  * gemini (ked je nastaveny kluc) — davkove triedenie cez Gemini Flash-Lite
    podla definicii kategorii. Kod je pripraveny, aktivuje sa az s klucom.

Pravidlo: kazdy clanok = prave jedna kategoria (tá najblizsia).
"""
import os
import json
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load_categories():
    with open(ROOT / "config" / "categories.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["categories"], data.get("fallback", "research")


CATS, FALLBACK = load_categories()


# ---------- Rezim 1: keyword fallback (bez API) ----------
def classify_keyword(item):
    text = (item["title"] + " " + item["summary"]).lower()
    best, best_score = None, 0
    for c in CATS:
        score = sum(1 for k in c.get("keywords", []) if k.lower() in text)
        if score > best_score:
            best, best_score = c["id"], score
    # SK/CZ ma prioritu podla regionu zdroja
    if item.get("region") in ("SK", "CZ"):
        return "skcz"
    return best or FALLBACK


# ---------- Rezim 2: Gemini Flash-Lite (davkovo) ----------
GEMINI_MODEL = "gemini-flash-lite-latest"


def _rubric():
    lines = ["Kategórie (vráť presne jedno id pre každý článok):"]
    for c in CATS:
        lines.append(f'- {c["id"]}: {c["definition"]}')
    return "\n".join(lines)


def classify_gemini_batch(items, batch_size=40):
    """Aktivne len ak je nastavena Gemini autentifikacia.
    GOOGLE_APPLICATION_CREDENTIALS (service account) alebo GEMINI_API_KEY.
    """
    try:
        import google.generativeai as genai
    except ImportError:
        raise RuntimeError("Chyba balík google-generativeai (pozri requirements.txt)")

    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key:
        genai.configure(api_key=api_key)
    # (service account cesta cez GOOGLE_APPLICATION_CREDENTIALS rieši Vertex variant)

    model = genai.GenerativeModel(GEMINI_MODEL)
    rubric = _rubric()
    results = {}
    for i in range(0, len(items), batch_size):
        chunk = items[i:i + batch_size]
        listing = "\n".join(
            f'{j}. {it["title"]} :: {it["summary"][:200]}' for j, it in enumerate(chunk)
        )
        prompt = (
            "Si presný klasifikátor AI správ. Pre každý článok vyber NAJBLIŽŠIU jednu kategóriu.\n\n"
            f"{rubric}\n\n"
            "Články:\n" + listing + "\n\n"
            'Vráť IBA JSON pole v tvare [{"i":0,"id":"models"}, ...] bez ďalšieho textu.'
        )
        resp = model.generate_content(prompt)
        txt = resp.text.strip().strip("`")
        if txt.startswith("json"):
            txt = txt[4:].strip()
        for row in json.loads(txt):
            results[i + int(row["i"])] = row["id"]
    valid = {c["id"] for c in CATS}
    return [results.get(k, FALLBACK) if results.get(k) in valid else FALLBACK
            for k in range(len(items))]


def classify_all(items, mode="auto"):
    """mode: auto | keyword | gemini. auto = gemini ak je kluc, inak keyword."""
    has_key = bool(os.environ.get("GEMINI_API_KEY") or
                   os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
    use = mode if mode != "auto" else ("gemini" if has_key else "keyword")
    if use == "gemini":
        cats = classify_gemini_batch(items)
        for it, cid in zip(items, cats):
            it["category"] = cid
        return items, "gemini"
    for it in items:
        it["category"] = classify_keyword(it)
    return items, "keyword"
