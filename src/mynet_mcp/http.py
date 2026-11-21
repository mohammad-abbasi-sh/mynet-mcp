"""HTTP layer for mynet_mcp.

Data source: Mynet (https://www.mynet.com) — one of Türkiye's biggest
internet portals (founded 1999; news, sports, finance, horoscope,
recipes, video, games). No login, no API key. Everything used here was
verified live 2026-11-21:

- GET https://www.mynet.com/sitemaps/news/GoogleNews.xml — Google News
  sitemap, 454 recent articles with <loc>
  (/haber/<slug>-<12-digit-id>), <news:title>, <news:publication_date>
  and <news:keywords>. Source for latest_news and (keyword scan)
  search_news. The site's own search (/haber/arama/) is disallowed in
  robots.txt, so search is a scan of this sitemap — same honest
  approach as trthaber-mcp / memurlar-mcp.
- GET https://www.mynet.com/haber/<slug>-<id> (also -myspor / -mykadin
  / -myyemek suffixed URLs) — server-rendered article carrying a
  schema.org NewsArticle JSON-LD block (@graph): headline, articleBody,
  datePublished, author (Person), plus og:description / og:image.
  A bare numeric id does NOT resolve (GET /haber/<id> is a 404) — the
  tool resolves ids through the news sitemap first.
- GET https://finans.mynet.com/altin/ — live gold prices: a table of
  19 gold products (Gram, Çeyrek, Yarım, Cumhuriyet, Gremse, Ons…,
  incl. Kapalıçarşı rows) with Son (last), Alış (buy), Satış (sell),
  % change and update time; plus 3 featured cards (Gram/Çeyrek/Ons).
- GET https://www.mynet.com/kadin/burclar-astroloji/<sign>-burcu-gunluk-yorumu.html
  — one page per zodiac sign (12 signs); <title> carries the sign +
  date ("Koç Burcu Günlük Yorumu 21 Kasım 2026") and the longest <p>
  is the daily horoscope text.
- GET https://www.mynet.com/ — home page (health check + section nav).

Transport uses curl-cffi Chrome impersonation with a plain-requests
fallback (the proven Turkey-factory pattern), even though the site
currently answers plain HTTP 200. Requests are kept gentle (one at a
time, ~0.5s apart) and read-only.
"""
from __future__ import annotations

import re
import time

from curl_cffi import requests as _creq
import requests as _plain

BASE = "https://www.mynet.com"
FINANS_BASE = "https://finans.mynet.com"
TIMEOUT = 30.0
MIN_INTERVAL = 0.5  # seconds between requests — be polite

_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}

_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)

_last_fetch = 0.0


class MynetError(RuntimeError):
    pass


def _throttle() -> None:
    global _last_fetch
    wait = MIN_INTERVAL - (time.monotonic() - _last_fetch)
    if wait > 0:
        time.sleep(wait)
    _last_fetch = time.monotonic()


_PROFILES = ("chrome120", "chrome131", "safari17_0")
_MAX_ATTEMPTS = 2  # one retry with the next profile
_RETRY_BACKOFF = 1.0  # seconds between attempts
_profile_idx = 0  # sticky: profile that last succeeded


def _request(url: str, headers: dict, timeout: float = TIMEOUT):
    """GET with fingerprint rotation.

    Starts at the sticky profile (chrome120 on a fresh process), retries
    once with the next profile on HTTP 403/429 or a transport error, then
    returns the last response (so the caller raises the specific 403/429
    error) or raises a network error if every attempt failed at the
    transport.
    """
    global _profile_idx
    last_exc: Exception | None = None
    for k in range(_MAX_ATTEMPTS):
        profile = _PROFILES[(_profile_idx + k) % len(_PROFILES)]
        try:
            resp = _creq.get(url, impersonate=profile, headers=headers, timeout=timeout)
        except Exception as e:
            last_exc = e
            if k + 1 < _MAX_ATTEMPTS:
                time.sleep(_RETRY_BACKOFF)
                continue
            raise MynetError(f"network error fetching {url}: {e}") from e
        if resp.status_code in (403, 429):
            if k + 1 < _MAX_ATTEMPTS:
                time.sleep(_RETRY_BACKOFF)
                continue
            return resp
        _profile_idx = (_profile_idx + k) % len(_PROFILES)
        return resp
    raise MynetError(f"network error fetching {url}: {last_exc}") from last_exc


def _get_text(url: str) -> str:
    """GET a URL, return the decoded text body.

    Raises MynetError with a human-readable message for HTTP errors.
    """
    _throttle()
    headers = dict(_HEADERS)
    try:
        resp = _request(url, headers)
        status, raw = resp.status_code, resp.content
    except Exception:
        # Fallback transport: plain requests with a browser UA.
        try:
            resp = _plain.get(url, headers={**headers, "User-Agent": _UA}, timeout=TIMEOUT)
            status, raw = resp.status_code, resp.content
        except MynetError:
            raise
        except Exception as e:
            raise MynetError(f"network error fetching {url}: {e}") from e
    if status == 403:
        raise MynetError(
            "www.mynet.com refused the request (HTTP 403, bot wall)"
            " — try again later"
        )
    if status == 429:
        raise MynetError(
            "www.mynet.com rate-limited the request (HTTP 429)"
            " — try again later"
        )
    if status == 404:
        raise MynetError(f"www.mynet.com has no page at {url} (HTTP 404)")
    if status != 200:
        raise MynetError(f"www.mynet.com returned HTTP {status} for {url}")
    return raw.decode("utf-8", errors="replace")


def fetch_news_sitemap() -> str:
    """The Google News sitemap (454 recent articles)."""
    return _get_text(f"{BASE}/sitemaps/news/GoogleNews.xml")


def fetch_article_page(url: str) -> str:
    """One server-rendered article page."""
    return _get_text(url)


def fetch_gold_page() -> str:
    """The finans.mynet.com gold-prices page."""
    return _get_text(f"{FINANS_BASE}/altin/")


def fetch_horoscope_page(sign_slug: str) -> str:
    """One sign's daily-horoscope page."""
    return _get_text(f"{BASE}/kadin/burclar-astroloji/{sign_slug}-burcu-gunluk-yorumu.html")


def fetch_home_page() -> str:
    """The Mynet home page (health check + section nav)."""
    return _get_text(f"{BASE}/")


def health_check() -> dict:
    """Two polite probes: the home page and the news sitemap.

    Returns {"status": "ok"|"blocked"|"error", "http_status": int|None,
    "url": ..., "detail": ...}. Used by the `mynet_health` tool and
    the daily smoke CI.
    """
    url = f"{BASE}/"
    try:
        home = fetch_home_page()
        if "Mynet" not in home:
            return {
                "status": "error",
                "http_status": 200,
                "url": url,
                "detail": "home page returned 200 but no Mynet content",
            }
        news = fetch_news_sitemap()
        if "<news:title>" not in news and "<news:news>" not in news:
            return {
                "status": "error",
                "http_status": 200,
                "url": f"{BASE}/sitemaps/news/GoogleNews.xml",
                "detail": "news sitemap returned 200 but no news entries",
            }
    except MynetError as e:
        msg = str(e)
        if "403" in msg:
            return {"status": "blocked", "http_status": 403, "url": url, "detail": msg}
        if "429" in msg:
            return {"status": "blocked", "http_status": 429, "url": url, "detail": msg}
        return {"status": "error", "http_status": None, "url": url, "detail": msg}
    return {"status": "ok", "http_status": 200, "url": url}
