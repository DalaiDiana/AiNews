"""Hlavny beh — spaja vsetky kroky. Spusta sa rano (cron / GitHub Actions).

  python src/pipeline.py
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


def run(max_age_days=1, classify_mode="auto"):
    print(f"== AI News Monitor — beh {dt.datetime.now():%Y-%m-%d %H:%M} ==")
    print("1) Zber:")
    raw = fetch.fetch_all()
    print(f"   stiahnuté: {len(raw)}")

    print("2) Filter (24h + AI relevancia):")
    fresh = flt.filter_items(raw, max_age_days=max_age_days)
    print(f"   po filtri: {len(fresh)}")

    print("3) Deduplikácia:")
    uniq = dedup.dedup(fresh)
    print(f"   po dedupe: {len(uniq)}")

    print("4) Zaradenie do kategórií:")
    classified, mode = classify.classify_all(uniq, mode=classify_mode)
    print(f"   režim triediča: {mode}")

    print("5) Uloženie + dashboard:")
    new_count, total = store.update(classified)
    print(f"   nové: {new_count}, v archíve spolu: {total}")
    print("Hotovo. dashboard/data.json aktualizovaný.")
    return new_count, total


if __name__ == "__main__":
    run()
