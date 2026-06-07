"""Krok 6 — Zaradenie do JEDNEJ kategorie (tej najblizsej) podla DEFINICII.

Zasady:
  * Gemini triedi VYLUCNE podla definicii kategorii (config/categories.yaml).
    Ziadne ad-hoc pravidla, ziadna zvyhodnena kategoria.
  * skcz urcuje Gemini (clanok primarne o SK/CZ scene). Navyse: clanok zo
    slovenskeho/ceskeho ZDROJA (region SK/CZ) ide vzdy do skcz (pravidlo Diany).
  * github sa Geminim NEpridelluje (repa chodia zo zdroja). Gemini im vsak
    doplni TEMU (pole 'topic'), aby sa dali filtrovat.
  * Presnost > rychlost: silnejsi model (flash) a male davky.

Rezimy: keyword (zalozny, bez API) | gemini | auto (gemini ak su credentials).
"""
import os
import json
import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CREDS_PATH = ROOT / "credentials.json"
# presnost pred rychlostou: skus najprv silnejsi flash, az potom flash-lite
GEMINI_MODELS = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]
LOCATION = "global"
BATCH = 20  # mensie davky = presnejsie triedenie


def load_categories():
    with open(ROOT / "config" / "categories.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["categories"], data.get("fallback", "research")


CATS, FALLBACK = load_categories()
# Gemini triedi do vsetkych kategorii OKREM github (tu urcuje zdroj). skcz Gemini RIESI.
GEM_CATS = [c for c in CATS if c["id"] != "github"]
# tema pre GitHub repozitare (bez github a bez skcz)
TOPIC_CATS = [c for c in CATS if c["id"] not in ("github", "skcz")]


# ---------- keyword fallback (bez API) ----------
def classify_keyword(item):
    if item.get("region") in ("SK", "CZ"):
        return "skcz"
    text = (item.get("title", "") + " " + item.get("summary", "")).lower()
    best, best_score = None, 0
    for c in TOPIC_CATS:
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


def _rubric(cats):
    return "\n".join(f'- {c["id"]}: {c["definition"]}' for c in cats)


def _pick_model():
    client = _vertex_client()
    for m in GEMINI_MODELS:
        try:
            client.models.generate_content(model=m, contents="ok")
            return client, m
        except Exception:
            continue
    raise RuntimeError("žiaden Gemini model nedostupný")


def gemini_label(items, cats, cat_field="category", batch_size=BATCH,
                 allow_none=True, do_desc=True, client=None, model=None):
    """Zaradí položky do kategórie STRICTNE podľa definícií (rubric z `cats`)
    a voliteľne napíše čistý anglický popis (prepíše summary).
    Vracia použitý model. Neúspešná dávka => pôvodné hodnoty ostávajú.
    client/model sa dajú predať zvonku (ušetrí opakované overovanie modelu)."""
    if not items:
        return None
    if client is None or model is None:
        client, model = _pick_model()
    rubric = _rubric(cats)
    valid = {c["id"] for c in cats} | ({"none"} if allow_none else set())
    none_line = ('- If an item is NOT really about artificial intelligence at all, '
                 'use id "none" so it is discarded.\n' if allow_none else "")
    desc_field = (', "desc":"<a clear 1-2 sentence factual ENGLISH description, '
                  'no hype, no emojis>"' if do_desc else "")
    for i in range(0, len(items), batch_size):
        chunk = items[i:i + batch_size]
        listing = "\n".join(
            f'{j}. {it.get("title", "")} :: {(it.get("summary") or "")[:300]}'
            for j, it in enumerate(chunk))
        prompt = (
            "You are a precise AI-news classifier. Assign each item to the SINGLE best-fitting "
            "category, judged STRICTLY by the category definitions below and their stated boundaries. "
            "Use the exact id. Pick the dominant subject, not a side mention.\n"
            + none_line +
            "When writing descriptions, translate any non-English text to English.\n\n"
            "Category definitions:\n" + rubric + "\n\n"
            "Items:\n" + listing + "\n\n"
            'Return ONLY a JSON array like [{"i":0,"id":"<id>"' + desc_field +
            "}], one entry per item, no other text.")
        try:
            resp = client.models.generate_content(model=model, contents=prompt)
            txt = (resp.text or "").strip().strip("`")
            if txt.lower().startswith("json"):
                txt = txt[4:].strip()
            for row in json.loads(txt):
                j = int(row["i"])
                if not (0 <= j < len(chunk)):
                    continue
                cid = row.get("id")
                if cid in valid:
                    chunk[j][cat_field] = cid
                if do_desc:
                    d = (row.get("desc") or "").strip()
                    if d:
                        chunk[j]["summary"] = d
        except Exception:
            pass
    return model


def classify_all(items, mode="auto", describe=True):
    """mode: auto | keyword | gemini. auto = gemini ak je credentials.json.
    describe=True => Gemini pri triedení rovno napíše aj lepší anglický popis."""
    has_creds = CREDS_PATH.exists() or bool(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))
    use = mode if mode != "auto" else ("gemini" if has_creds else "keyword")
    mode_used = "keyword"
    if use == "gemini":
        try:
            for it in items:
                it.setdefault("category", FALLBACK)
            model = gemini_label(items, GEM_CATS, cat_field="category",
                                 allow_none=True, do_desc=describe)
            mode_used = f"gemini:{model}"
        except Exception as ex:
            print(f"   ! Gemini zlyhal ({str(ex)[:90]}), padám na keyword")
            for it in items:
                it["category"] = classify_keyword(it)
    else:
        for it in items:
            it["category"] = classify_keyword(it)
    # Gemini mohol nepatriace označiť ako "none" -> zahodíme (kontextové rozhodnutie)
    items = [it for it in items if it.get("category") != "none"]
    # ISTOTA: článok zo slovenského/českého ZDROJA ide vždy do skcz (pravidlo Diany)
    for it in items:
        if it.get("region") in ("SK", "CZ"):
            it["category"] = "skcz"
    return items, mode_used


def topic_github(items):
    """GitHub repozitárom doplní reálnu TÉMU (pole 'topic') + lepší popis.
    Kategória ostáva 'github'. Tichý fallback, ak Gemini nie je dostupný."""
    if not items:
        return None
    try:
        return gemini_label(items, TOPIC_CATS, cat_field="topic",
                            allow_none=False, do_desc=True)
    except Exception as ex:
        print(f"   ! GitHub topic Gemini zlyhal ({str(ex)[:80]})")
        for it in items:
            it["topic"] = classify_keyword(it)
        return None
