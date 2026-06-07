"""Krok 7 — Ulozisko. JSON archiv, expirovanie po N dnoch, pocty 'N new'."""
import json
import re
import datetime as dt
import yaml
from pathlib import Path


def _sources_total():
    """Počet sledovaných zdrojov (zo sources.yaml) + GitHub."""
    try:
        n = len(yaml.safe_load(open(Path(__file__).resolve().parent.parent / "config" / "sources.yaml"))["sources"])
        return n + 1  # +GitHub repá
    except Exception:
        return 0


def _tkey(t):
    # normalizovaný kľúč z titulku — rozpozná tú istú správu aj keď sa zmení URL
    # (napr. rotujúce Google News odkazy)
    return re.sub(r"[^a-z0-9 ]", "", (t or "").lower()).strip()[:70]

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ARCHIVE = DATA / "archive.json"           # vsetky polozky za poslednych N dni
DASHBOARD_DATA = ROOT / "dashboard" / "data.json"  # to, co cita web

RETENTION_DAYS = 10
STATE = DATA / "state.json"  # pamätá si čas posledného behu (UTC)


def get_last_run():
    try:
        return json.load(open(STATE)).get("last_run")
    except Exception:
        return None


def set_last_run(iso):
    DATA.mkdir(exist_ok=True)
    json.dump({"last_run": iso}, open(STATE, "w"))


def _load_archive():
    if ARCHIVE.exists():
        with open(ARCHIVE, encoding="utf-8") as f:
            return json.load(f)
    return []


def _prune(items):
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=RETENTION_DAYS)
    out = []
    for it in items:
        try:
            if dt.datetime.fromisoformat(it["published"]) >= cutoff:
                out.append(it)
        except Exception:
            pass
    return out


def update(new_items):
    """Prida nove polozky do archivu (bez duplikatov podla canonical_url),
    odstrani stare a zapise archive.json aj dashboard/data.json."""
    archive = _load_archive()
    seen_urls = {it.get("canonical_url", it["url"]) for it in archive}
    seen_titles = {_tkey(it["title"]) for it in archive}
    fresh = 0
    today = dt.date.today().isoformat()
    for it in new_items:
        key = it.get("canonical_url", it["url"])
        tk = _tkey(it["title"])
        if key in seen_urls or (tk and tk in seen_titles):
            continue  # už ho máme (podľa URL alebo titulku) -> nie je nový
        it["added"] = today
        archive.append(it)
        seen_urls.add(key)
        if tk:
            seen_titles.add(tk)
        fresh += 1

    archive = _prune(archive)
    DATA.mkdir(exist_ok=True)
    with open(ARCHIVE, "w", encoding="utf-8") as f:
        json.dump(archive, f, ensure_ascii=False, indent=2)

    _write_dashboard(archive, fresh)
    return fresh, len(archive)


def _write_dashboard(archive, fresh_total):
    today = dt.date.today().isoformat()
    cats = {}
    for it in archive:
        c = it.get("category", "research")
        cats.setdefault(c, {"items": [], "new": 0})
        cats[c]["items"].append(it)
        if it.get("added") == today:
            cats[c]["new"] += 1
    for c in cats:
        cats[c]["items"].sort(key=lambda x: x["published"], reverse=True)
    payload = {
        "generated": dt.datetime.now(dt.timezone.utc).isoformat(),
        "today": today,
        "total_new": sum(c["new"] for c in cats.values()),
        "total_items": len(archive),
        "sources_total": _sources_total(),
        "categories": cats,
    }
    DASHBOARD_DATA.parent.mkdir(exist_ok=True)
    with open(DASHBOARD_DATA, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    # data.js — aby fungoval obyčajný dvojklik (file:// blokuje fetch JSON-u)
    with open(DASHBOARD_DATA.parent / "data.js", "w", encoding="utf-8") as f:
        f.write("window.AINM_DATA = " + json.dumps(payload, ensure_ascii=False) + ";")
