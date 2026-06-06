"""Hlavny beh — spaja vsetky kroky. Spusta sa rano (cron / GitHub Actions).

  python3 src/pipeline.py
"""
import sys
import datetime as dt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fetch
import filter as flt
import dedup
import classify
import store


def run(max_age_days=None, classify_mode="auto"):
    # prvy beh (prazdny archiv) = backfill 10 dni; dalsie denne behy = 1 den
    if max_age_days is None:
        import json as _json
        try:
            initial = len(_json.load(open(store.ARCHIVE))) == 0
        except Exception:
            initial = True
        max_age_days = 10 if initial else 1
    print(f"== AI News Monitor — beh {dt.datetime.now():%Y-%m-%d %H:%M} (okno {max_age_days} dní) ==")
    print("1) Zber RSS/API:")
    raw = fetch.fetch_rss_all()
    print(f"   stiahnuté: {len(raw)}")

    print("2) Filter (24h + AI relevancia):")
    fresh = flt.filter_items(raw, max_age_days=max_age_days)
    print(f"   po filtri: {len(fresh)}")

    print("3) Deduplikácia:")
    uniq = dedup.dedup(fresh)
    print(f"   po dedupe: {len(uniq)}")

    print("4) Zaradenie do kategórií (Gemini / keyword):")
    classified, mode = classify.classify_all(uniq, mode=classify_mode)
    print(f"   režim triediča: {mode}")

    print("5) GitHub trending repozitáre:")
    gh = dedup.dedup(fetch.fetch_github_all())
    print(f"   repozitárov: {len(gh)}")

    all_items = classified + gh

    print("6) Uloženie + dashboard:")
    new_count, total = store.update(all_items)
    print(f"   nové: {new_count}, v archíve spolu: {total}")
    print("Hotovo. dashboard/data.json + data.js aktualizované.")
    return new_count, total


if __name__ == "__main__":
    run()
