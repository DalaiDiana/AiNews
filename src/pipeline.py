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


def run(classify_mode="auto"):
    UTC = dt.timezone.utc
    now = dt.datetime.now(UTC)
    # okno = od posledného behu po teraz (≈12 h). Prvý beh (bez stavu) = posledných 12 h.
    last = store.get_last_run()
    try:
        since = dt.datetime.fromisoformat(last) if last else now - dt.timedelta(hours=12)
    except Exception:
        since = now - dt.timedelta(hours=12)
    hrs = round((now - since).total_seconds() / 3600, 1)
    print(f"== AI News Monitor — beh {now:%Y-%m-%d %H:%M} UTC (okno od {since:%Y-%m-%d %H:%M} UTC, {hrs} h) ==")
    print("1) Zber RSS/API:")
    raw = fetch.fetch_rss_all()
    print(f"   stiahnuté: {len(raw)}")

    print("2) Filter (nové od posledného behu + AI relevancia):")
    fresh = flt.filter_since(raw, since)
    print(f"   po filtri: {len(fresh)}")

    print("3) Deduplikácia:")
    uniq = dedup.dedup(fresh)
    print(f"   po dedupe: {len(uniq)}")

    print("4) Zaradenie do kategórií + popisy (Gemini podľa definícií / keyword):")
    classified, mode = classify.classify_all(uniq, mode=classify_mode)
    print(f"   režim triediča: {mode}")

    print("5) GitHub trending repozitáre (+ téma cez Gemini):")
    gh = dedup.dedup(fetch.fetch_github_all())
    classify.topic_github(gh)
    print(f"   repozitárov: {len(gh)}")

    all_items = classified + gh

    print("6) Uloženie + dashboard:")
    new_count, total = store.update(all_items)
    store.set_last_run(now.isoformat())  # zapamätaj čas behu pre ďalšie okno
    print(f"   nové: {new_count}, v archíve spolu: {total}")
    print("Hotovo. dashboard/data.json + data.js aktualizované.")
    return new_count, total


if __name__ == "__main__":
    run()
