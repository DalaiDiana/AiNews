"""Krok 6 — Zaradenie do JEDNEJ kategorie (tej najblizsej).

Rezimy:
  * keyword  — bez API, skore podla klucovych slov (zalozny).
  * gemini   — Gemini Flash-Lite, davkove triedenie podla definicii.
               Aktivuje sa, ak je nastaveny GEMINI_API_KEY.

Pozn.: kategoria 'github' sa sem NEpridelluje — repozitare prichadzaju
priamo z GitHub zdroja (fetch_github_all). Triedic ostatne zdroje nezaradi
do githubu, takze do GitHubu uz nepadaju omylom clanky (napr. arXiv).
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
# triedic nepouziva github (repá maju vlastny zdroj)
CLS_CATS = [c for c in CATS if c["id"] != "github"]


# ---------- keyword fallback ----------
def classify_keyword(item):
    if item.get("region") in ("SK", "CZ"):
        return "skcz"
    text = (item["title"] + " " + item["summary"]).lower()
    best, best_score = None, 0
    for c in CLS_CATS:
        score = sum(1 for k in c.get("keywords", []) if k.lower() in text)
        if score > best_score:
            best, best_score = c["id"], score
    return best or FALLBACK


# ---------- Gemini Flash-Lite (davkovo) ----------
GEMINI_MODEL = "gemini-flash-lite-latest"


def _rubric():
    lines = []
    for c in CLS_CATS:
        lines.append(f'- {c["id"]}: {c["definition"]}')
    return "\n".join(lines)


def classify_gemini(items, batch_size=40):
    from google import genai
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    rubric = _rubric()
    valid = {c["id"] for c in CLS_CATS}
    out = [FALLBACK] * len(items)
    for i in range(0, len(items), batch_size):
        chunk = items[i:i + batch_size]
        listing = "\n".join(
            f'{j}. {it["title"]} :: {it["summary"][:200]}' for j, it in enumerate(chunk))
        prompt = (
            "You are a precise AI-news classifier. For each article pick the SINGLE closest category id.\n\n"
            "Categories:\n" + rubric + "\n\n"
            "Articles:\n" + listing + "\n\n"
            'Return ONLY a JSON array like [{"i":0,"id":"models"}, ...] — no other text.')
        resp = client.models.generate_content(model=GEMINI_MODEL, contents=prompt)
        txt = resp.text.strip().strip("`")
        if txt.lower().startswith("json"):
            txt = txt[4:].strip()
        try:
            for row in json.loads(txt):
                idx = i + int(row["i"])
                if 0 <= idx < len(items) and row.get("id") in valid:
                    out[idx] = row["id"]
        except Exception:
            pass
    return out


def classify_all(items, mode="auto"):
    """mode: auto | keyword | gemini. auto = gemini ak je GEMINI_API_KEY."""
    has_key = bool(os.environ.get("GEMINI_API_KEY"))
    use = mode if mode != "auto" else ("gemini" if has_key else "keyword")
    if use == "gemini":
        try:
            cats = classify_gemini(items)
            for it, cid in zip(items, cats):
                it["category"] = cid
            return items, "gemini"
        except Exception as ex:
            print(f"   ! Gemini zlyhal ({str(ex)[:80]}), padam na keyword")
    for it in items:
        it["category"] = classify_keyword(it)
    return items, "keyword"
