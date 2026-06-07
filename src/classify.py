"""Krok 6 — Zaradenie do JEDNEJ kategorie (tej najblizsej).

Rezimy:
  * keyword  — bez API, skore podla klucovych slov (zalozny).
  * gemini   — Gemini (Vertex AI, service account credentials.json), davkove
               triedenie podla definicii. Aktivuje sa, ak existuje credentials.json
               (alebo GOOGLE_APPLICATION_CREDENTIALS).

Pozn.: kategoria 'github' sa sem NEpridelluje — repozitare prichadzaju
priamo z GitHub zdroja, takze do GitHubu uz nepadaju omylom clanky.
"""
import os
import re
import json
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CREDS_PATH = ROOT / "credentials.json"
GEMINI_MODELS = ["gemini-2.5-flash-lite", "gemini-2.5-flash"]
LOCATION = "global"


def load_categories():
    with open(ROOT / "config" / "categories.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["categories"], data.get("fallback", "research")


CATS, FALLBACK = load_categories()
# triedič nepoužíva github (repá majú vlastný zdroj) ani skcz (to sa určuje regiónom)
CLS_CATS = [c for c in CATS if c["id"] not in ("github", "skcz")]


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


# ---------- Gemini (Vertex AI, service account) ----------
def _vertex_client():
    from google import genai
    if CREDS_PATH.exists() and not os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(CREDS_PATH)
    proj = None
    if CREDS_PATH.exists():
        proj = json.load(open(CREDS_PATH))["project_id"]
    proj = proj or os.environ.get("GOOGLE_CLOUD_PROJECT")
    return genai.Client(vertexai=True, project=proj, location=LOCATION)


def _rubric():
    return "\n".join(f'- {c["id"]}: {c["definition"]}' for c in CLS_CATS)


def classify_gemini(items, batch_size=40):
    client = _vertex_client()
    model = None
    for m in GEMINI_MODELS:
        try:
            client.models.generate_content(model=m, contents="ok")
            model = m
            break
        except Exception:
            continue
    if not model:
        raise RuntimeError("žiaden Gemini model nedostupný")

    rubric = _rubric()
    valid = {c["id"] for c in CLS_CATS}
    out = [FALLBACK] * len(items)
    for i in range(0, len(items), batch_size):
        chunk = items[i:i + batch_size]
        listing = "\n".join(
            f'{j}. {it["title"]} :: {it["summary"][:200]}' for j, it in enumerate(chunk))
        prompt = (
            "You are a precise AI-news classifier. Assign each article to the SINGLE best-fitting "
            "category by its MAIN subject. Use the exact id from the list. Rules:\n"
            "- Pick the dominant topic, not a side mention.\n"
            "- A new/updated model or its capabilities -> models. Funding/acquisition/revenue -> business.\n"
            "- Company/lab corporate news (leadership, strategy, partnerships) -> bigplayers.\n"
            "- Agents/MCP/LangChain/dev frameworks -> agents. Chips/GPU/datacenter/energy -> infra.\n"
            "- Benchmarks/leaderboards/evals -> benchmarks. Laws/regulation/policy -> legislation.\n"
            "- Safety/alignment/ethics -> ethics. Robots/humanoids -> robotics. Self-driving/drones -> autonomous.\n\n"
            "Categories:\n" + rubric + "\n\n"
            "Articles:\n" + listing + "\n\n"
            'Return ONLY a JSON array like [{"i":0,"id":"models"}, ...] — no other text, one entry per article.')
        resp = client.models.generate_content(model=model, contents=prompt)
        txt = (resp.text or "").strip().strip("`")
        if txt.lower().startswith("json"):
            txt = txt[4:].strip()
        try:
            for row in json.loads(txt):
                idx = i + int(row["i"])
                if 0 <= idx < len(items) and row.get("id") in valid:
                    out[idx] = row["id"]
        except Exception:
            pass
    return out, model


_CZSK_CHARS = re.compile(r"[ěřůľĺŕ]", re.I)  # znaky typické pre češtinu/slovenčinu


def _is_czsk(it):
    if it.get("region") in ("SK", "CZ"):
        return True
    # jazyková detekcia: 3+ česko/slovenských znakov => je to CZ/SK článok
    text = (it.get("title", "") + " " + it.get("summary", ""))
    return len(_CZSK_CHARS.findall(text)) >= 3


def _force_skcz(items):
    # SK/CZ (podľa regiónu ALEBO jazyka) ide VŽDY len do kategórie skcz
    for it in items:
        if _is_czsk(it):
            it["category"] = "skcz"


def classify_all(items, mode="auto"):
    """mode: auto | keyword | gemini. auto = gemini ak je credentials.json."""
    has_creds = CREDS_PATH.exists() or bool(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
    use = mode if mode != "auto" else ("gemini" if has_creds else "keyword")
    mode_used = "keyword"
    if use == "gemini":
        try:
            cats, model = classify_gemini(items)
            for it, cid in zip(items, cats):
                it["category"] = cid
            mode_used = f"gemini:{model}"
        except Exception as ex:
            print(f"   ! Gemini zlyhal ({str(ex)[:90]}), padám na keyword")
            for it in items:
                it["category"] = classify_keyword(it)
    else:
        for it in items:
            it["category"] = classify_keyword(it)
    _force_skcz(items)
    return items, mode_used
