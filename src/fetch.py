"""Krok 3a — Zber. RSS/API zdroje + GitHub trending repozitáre. Normalizacia."""
import urllib.request
import urllib.parse
import datetime as dt
import time
import re
import json
import html as htmllib
import yaml
import feedparser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = "Mozilla/5.0 (AINewsMonitor; +https://github.com/DalaiDiana/AiNews)"
UTC = dt.timezone.utc


def load_sources():
    with open(ROOT / "config" / "sources.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)["sources"]


def _fetch_url(url, accept=None):
    headers = {"User-Agent": UA}
    if accept:
        headers["Accept"] = accept
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read()


def clean_summary(raw):
    """Odstrani HTML tagy a arXiv boilerplate, nechá len zmysluplny popis."""
    if not raw:
        return ""
    t = re.sub(r"<[^>]+>", " ", raw)
    t = htmllib.unescape(t)
    t = re.sub(r"\s+", " ", t).strip()
    t = re.sub(r"^arXiv:\S+\s*", "", t)
    t = re.sub(r"Announce Type:\s*\w+\s*", "", t, flags=re.I)
    t = re.sub(r"^Abstract:\s*", "", t, flags=re.I)
    return t.strip()


def _parse_date(entry):
    for key in ("published_parsed", "updated_parsed"):
        val = entry.get(key)
        if val:
            return dt.datetime.fromtimestamp(time.mktime(val), tz=UTC)
    return None


def _fetch_one(src):
    out = []
    try:
        feed = feedparser.parse(_fetch_url(src["url"]))
        for e in feed.entries[:60]:
            title = (e.get("title") or "").strip()
            link = (e.get("link") or "").strip()
            if not title or not link:
                continue
            out.append({
                "title": title, "url": link,
                "summary": clean_summary(e.get("summary") or e.get("description") or ""),
                "source": src["name"], "region": src.get("region", "GLOBAL"),
                "published": (_parse_date(e) or dt.datetime.now(UTC)).isoformat(),
            })
        return (src["name"], out, None)
    except Exception as ex:
        return (src["name"], [], str(ex)[:50])


def fetch_rss_all(verbose=True):
    """Normalizovane polozky zo vsetkych RSS/API zdrojov (bez GitHubu), paralelne."""
    import concurrent.futures
    srcs = [s for s in load_sources() if s.get("type") != "github"]
    items = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
        for name, got, err in pool.map(_fetch_one, srcs):
            if verbose:
                print(f"  {'OK ' if not err else 'ERR'} {name:26} {len(got) if not err else err}")
            items.extend(got)
    return items


def _github_token():
    p = ROOT / "git-token.txt"
    if p.exists():
        return p.read_text().strip()
    return None


def fetch_github_all(verbose=True, days=21):
    """Trending AI repozitare cez GitHub Search API. Vzdy kategoria 'github'."""
    items, seen = [], set()
    since = (dt.datetime.now(UTC) - dt.timedelta(days=days)).strftime("%Y-%m-%d")
    queries = ["topic:llm", "topic:ai-agents", "topic:machine-learning",
               "topic:generative-ai", "topic:artificial-intelligence"]
    tok = _github_token()
    for q in queries:
        full_q = urllib.parse.quote(f"{q} pushed:>={since}")
        url = (f"https://api.github.com/search/repositories?q={full_q}"
               f"&sort=stars&order=desc&per_page=8")
        try:
            headers = {"User-Agent": UA, "Accept": "application/vnd.github+json"}
            if tok:
                headers["Authorization"] = f"Bearer {tok}"
            req = urllib.request.Request(url, headers=headers)
            data = json.loads(urllib.request.urlopen(req, timeout=25).read())
            added = 0
            for repo in data.get("items", []):
                fn = repo["full_name"]
                if fn in seen:
                    continue
                seen.add(fn)
                try:
                    pub = dt.datetime.strptime(repo["pushed_at"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=UTC).isoformat()
                except Exception:
                    pub = dt.datetime.now(UTC).isoformat()
                items.append({
                    "title": f"{fn}  ★{repo['stargazers_count']:,}",
                    "url": repo["html_url"],
                    "summary": clean_summary(repo.get("description") or ""),
                    "source": "GitHub",
                    "region": "GLOBAL",
                    "published": pub,
                    "category": "github",
                })
                added += 1
            if verbose:
                print(f"  OK  GitHub {q:24} {added:3}")
            time.sleep(0.3)
        except Exception as ex:
            if verbose:
                print(f"  ERR GitHub {q:24} {str(ex)[:55]}")
    return items


if __name__ == "__main__":
    print(f"RSS: {len(fetch_rss_all())} | GitHub: {len(fetch_github_all())}")
