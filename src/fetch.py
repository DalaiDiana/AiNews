"""Krok 3a — Zber. Stiahne RSS/API zdroje a znormalizuje na jednotny tvar."""
import urllib.request
import datetime as dt
import time
import yaml
import feedparser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (AINewsMonitor; +https://github.com/)"


def load_sources():
    with open(ROOT / "config" / "sources.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)["sources"]


def _fetch_url(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.read()


def _parse_date(entry):
    for key in ("published_parsed", "updated_parsed"):
        val = entry.get(key)
        if val:
            return dt.datetime.fromtimestamp(time.mktime(val), tz=dt.timezone.utc)
    return None


def fetch_all(verbose=True):
    """Vrati zoznam normalizovanych poloziek zo vsetkych zdrojov."""
    items = []
    for src in load_sources():
        try:
            raw = _fetch_url(src["url"])
            feed = feedparser.parse(raw)
            n = 0
            for e in feed.entries:
                title = (e.get("title") or "").strip()
                link = (e.get("link") or "").strip()
                if not title or not link:
                    continue
                summary = (e.get("summary") or e.get("description") or "").strip()
                items.append({
                    "title": title,
                    "url": link,
                    "summary": summary,
                    "source": src["name"],
                    "region": src.get("region", "GLOBAL"),
                    "published": (_parse_date(e) or dt.datetime.now(dt.timezone.utc)).isoformat(),
                })
                n += 1
            if verbose:
                print(f"  OK  {src['name']:26} {n:3} položiek")
        except Exception as ex:
            if verbose:
                print(f"  ERR {src['name']:26} {str(ex)[:60]}")
    return items


if __name__ == "__main__":
    got = fetch_all()
    print(f"\nSpolu: {len(got)} položiek")
