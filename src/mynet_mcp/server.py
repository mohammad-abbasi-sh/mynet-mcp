"""MCP server: unofficial read-only access to Mynet (Turkish portal: news, gold prices, daily horoscope, sections)."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from mcp.server.fastmcp import FastMCP

from . import http as _http
from . import parse as _P

mcp = FastMCP("mynet-mcp")

INSTRUCTIONS = """\
Unofficial read-only MCP server for Mynet (www.mynet.com) — one of \
Türkiye's biggest internet portals (founded 1999): news \
(mynet_latest_news, mynet_search_news, mynet_get_article), live gold \
prices from finans.mynet.com (mynet_gold_prices), daily horoscope for \
all 12 zodiac signs (mynet_horoscope) and the portal's sections \
(mynet_list_sections). News lists come from the site's Google News \
sitemap (454 recent articles with title, date and keywords); article \
pages are server-rendered with a schema.org NewsArticle block (title, \
author, published/updated stamps, full body). Search is a \
Turkish-aware keyword scan of the sitemap (the site's own search is \
disallowed in robots.txt). A bare numeric article id does not resolve \
on mynet.com (/haber/<id> is a 404), so ids are resolved through the \
news sitemap first. Gold prices are the live table on \
finans.mynet.com/altin/ (Gram, Çeyrek, Yarım, Cumhuriyet, Gremse, Ons \
— incl. Kapalıçarşı rows) with last/buy/sell prices in TRY (Ons/USD \
in USD), daily change and update time. No login, no API key. \
Read-only; transport uses Chrome TLS impersonation with a \
plain-requests fallback; requests are spaced ~0.5s apart. Built by \
Mohammad Abbasi (mohammad-abbasi-sh) — https://almanibama.ir · \
https://mabbasi.ir — Turkey MCP factory.\
"""

_SOURCE = "www.mynet.com"
_DISCLAIMER = (
    "Unofficial read-only Mynet data from the site's public sitemap "
    "and pages; verify on the official site before acting on it. Gold "
    "prices are indicative market prices, not investment advice."
)


def _envelope() -> dict:
    return {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "source": _SOURCE,
        "disclaimer": _DISCLAIMER,
    }


def _ok(payload: dict) -> str:
    return json.dumps({**_envelope(), **payload}, ensure_ascii=False)


def _err(e: Exception) -> str:
    return _ok({"error": str(e)})


def _limit(limit: int) -> int:
    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 10
    return max(1, min(limit, 50))


@mcp.tool()
def mynet_latest_news(limit: int = 10) -> str:
    """Latest news from Mynet (newest first).

    limit: how many items to return (1-50, default 10). Returns each
    article's id, title, URL, publication date, keywords and image —
    sourced from the site's Google News sitemap (454 recent articles).
    Use mynet_get_article for the full text of one article."""
    try:
        items = _P.parse_news_sitemap(_http.fetch_news_sitemap())
        return _ok({"count": len(items[: _limit(limit)]), "news": items[: _limit(limit)]})
    except (ValueError, _http.MynetError) as e:
        return _err(e)


@mcp.tool()
def mynet_search_news(query: str, limit: int = 10) -> str:
    """Search recent Mynet news by keyword (Turkish-aware).

    query: one or more words, e.g. "deprem" or "altın fiyatları" —
    every word must appear in the title or keywords (Turkish
    dotted/dotless I handled). limit: max results (1-50, default 10).
    Searches the 454 most recent articles in the site's news sitemap;
    the site's own search is disallowed in robots.txt, so this is a
    scan of the sitemap, not a full-archive search."""
    try:
        query = (query or "").strip()
        if not query:
            raise ValueError("query must not be empty")
        items = _P.parse_news_sitemap(_http.fetch_news_sitemap())
        found = _P.search_items(items, query)
        return _ok(
            {
                "query": query,
                "count": len(found[: _limit(limit)]),
                "total_matches": len(found),
                "news": found[: _limit(limit)],
            }
        )
    except (ValueError, _http.MynetError) as e:
        return _err(e)


@mcp.tool()
def mynet_get_article(article: str) -> str:
    """Full text of one Mynet news article.

    article: a numeric article id (e.g. "110107322088", resolved
    through the news sitemap — a bare id does not resolve on the site
    itself) or a full article URL
    (https://www.mynet.com/haber/...-110107322088, also -myspor /
    -mykadin / -myyemek suffixed URLs). Returns title, URL, summary,
    published/updated stamps, author, headline image and the full body
    text (paragraphs in order)."""
    try:
        value = (article or "").strip()
        if not value:
            raise ValueError("article must not be empty")
        if value.isdigit():
            items = _P.parse_news_sitemap(_http.fetch_news_sitemap())
            hit = _P.find_by_id(items, int(value))
            if hit is None:
                raise ValueError(
                    f"no article with id {value} in the 454 most recent "
                    "news items — pass a full article URL instead"
                )
            url = hit["url"]
        else:
            url = _P.resolve_article_url(value)
        page = _http.fetch_article_page(url)
        return _ok(_P.parse_article_page(page, url))
    except (ValueError, _http.MynetError) as e:
        return _err(e)


@mcp.tool()
def mynet_gold_prices() -> str:
    """Live gold prices from finans.mynet.com (TRY, Ons/USD in USD).

    Returns the 19 gold products on the altin page — Gram, Çeyrek,
    Yarım, Tam, Cumhuriyet, Gremse, Ons and more, including
    Kapalıçarşı (Grand Bazaar) rows — each with last price, buy
    (Alış), sell (Satış), daily change in percent and update time.
    No arguments."""
    try:
        items = _P.parse_gold_page(_http.fetch_gold_page())
        return _ok({"count": len(items), "prices": items})
    except (ValueError, _http.MynetError) as e:
        return _err(e)


@mcp.tool()
def mynet_horoscope(sign: str) -> str:
    """Today's daily horoscope for one zodiac sign.

    sign: a Turkish sign name ("Koç", "Boğa", "İkizler", "Yengeç",
    "Aslan", "Başak", "Terazi", "Akrep", "Yay", "Oğlak", "Kova",
    "Balık") or the English name ("Aries", "Taurus", ...). Returns the
    sign, the date the horoscope is for, and the full daily text."""
    try:
        slug = _P.resolve_sign(sign)
        page = _http.fetch_horoscope_page(slug)
        return _ok(_P.parse_horoscope_page(page, slug))
    except (ValueError, _http.MynetError) as e:
        return _err(e)


@mcp.tool()
def mynet_list_sections() -> str:
    """Mynet's main portal sections (slug -> Turkish label).

    Parsed from the home-page navigation: Haber, Spor, Magazin,
    Yazarlar, Astroloji, Hava Durumu, Sağlık, Video, Yemek, Kadın,
    Trend, Eğitim, Anket, Test, Aktüel, Vitrin, Resmi İlanlar and
    more, each with its URL."""
    try:
        sections = _P.parse_sections(_http.fetch_home_page())
        return _ok({"count": len(sections), "sections": sections})
    except (ValueError, _http.MynetError) as e:
        return _err(e)


@mcp.tool()
def mynet_health() -> str:
    """Check whether Mynet is reachable right now.

    Returns status ok (HTTP 200), blocked (HTTP 403/429 — bot wall or
    rate limit) or error, plus the HTTP status and the probed URL.
    Two polite requests (home page + news sitemap); it fetches no
    article or horoscope content."""
    return _ok(_http.health_check())


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    import sys

    sys.exit(main())
