"""Parsers for Mynet's server-rendered pages (stdlib only).

All markup shapes were verified against live pages fetched 2026-11-21;
offline tests run against recorded fixtures in tests/fixtures/.

Sources:
- /sitemaps/news/GoogleNews.xml: Google News sitemap (454 recent
  articles; <loc> /haber/<slug>-<12-digit-id>, <news:title>,
  <news:publication_date>, <news:keywords>)
- /haber/<slug>-<id> (also -myspor / -mykadin / -myyemek suffixed):
  article page with a schema.org NewsArticle JSON-LD block (@graph)
- finans.mynet.com/altin/: gold-price table (19 products)
- /kadin/burclar-astroloji/<sign>-burcu-gunluk-yorumu.html: one page
  per zodiac sign (12 signs), daily horoscope text in the longest <p>
- / : home page (section nav)
"""
from __future__ import annotations

import html as _html
import json
import re
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# Turkish-aware text helpers
# ---------------------------------------------------------------------------

_TR_LOWER_MAP = str.maketrans({"I": "ı", "İ": "i"})


def tr_lower(s: str) -> str:
    """Lowercase that respects Turkish dotted/dotless I.

    Python's str.lower() maps "I" -> "i" (English); Turkish needs
    "I" -> "ı" and "İ" -> "i". Without this, searching for "işçi"
    would miss "İŞÇİ" and vice versa.
    """
    return (s or "").translate(_TR_LOWER_MAP).lower()


def clean_text(s: str) -> str:
    """Unescape HTML entities, strip tags, collapse whitespace."""
    s = _html.unescape(s or "")
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# ---------------------------------------------------------------------------
# News sitemap
# ---------------------------------------------------------------------------

_NS = {
    "s": "http://www.sitemaps.org/schemas/sitemap/0.9",
    "news": "http://www.google.com/schemas/sitemap-news/0.9",
    "image": "http://www.google.com/schemas/sitemap-image/1.1",
}

_ID_RE = re.compile(r"(\d+)(?:-(?:myspor|mykadin|myyemek|myvideo))?$")


def _sitemap_items(xml_text: str) -> list[dict]:
    """Parse the Google News sitemap into item dicts (newest first)."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        raise ValueError(f"could not parse sitemap XML: {e}") from e
    items: list[dict] = []
    for url_el in root.findall("s:url", _NS):
        loc_el = url_el.find("s:loc", _NS)
        news_el = url_el.find("news:news", _NS)
        if loc_el is None or loc_el.text is None or news_el is None:
            continue
        loc = loc_el.text.strip()
        title_el = news_el.find("news:title", _NS)
        date_el = news_el.find("news:publication_date", _NS)
        kw_el = news_el.find("news:keywords", _NS)
        img_el = url_el.find("image:image/image:loc", _NS)
        m = _ID_RE.search(loc.rstrip("/"))
        items.append(
            {
                "id": int(m.group(1)) if m else None,
                "title": (title_el.text or "").strip() if title_el is not None else "",
                "url": loc,
                "published_at": (date_el.text or "").strip() if date_el is not None else "",
                "keywords": (kw_el.text or "").strip() if kw_el is not None else "",
                "image": (img_el.text or "").strip() if img_el is not None else "",
            }
        )
    return items


def parse_news_sitemap(xml_text: str) -> list[dict]:
    """454 recent articles from the Google News sitemap (newest first)."""
    return _sitemap_items(xml_text)


def find_by_id(items: list[dict], article_id: int) -> dict | None:
    """The sitemap item whose id matches (sitemap is the id index)."""
    for it in items:
        if it.get("id") == article_id:
            return it
    return None


def search_items(items: list[dict], query: str) -> list[dict]:
    """Turkish-aware substring filter over title + keywords.

    The query is split on whitespace; every word must appear (in title
    or keywords). Returns matches in the original (newest-first) order.
    """
    words = [tr_lower(w) for w in (query or "").split() if w.strip()]
    if not words:
        return list(items)
    out = []
    for it in items:
        hay = tr_lower(f"{it.get('title', '')} {it.get('keywords', '')}")
        if all(w in hay for w in words):
            out.append(it)
    return out


# ---------------------------------------------------------------------------
# Article page — NewsArticle JSON-LD (@graph)
# ---------------------------------------------------------------------------

def _news_article_node(html_text: str) -> dict:
    """The NewsArticle node of the page's JSON-LD @graph.

    Raises ValueError when no NewsArticle block is found.
    """
    for m in re.finditer(
        r'<script type="application/ld\+json">(.*?)</script>', html_text, re.S
    ):
        try:
            data = json.loads(m.group(1))
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        graph = data.get("@graph") or []
        for node in graph:
            if isinstance(node, dict) and node.get("@type") == "NewsArticle":
                return node
        if data.get("@type") == "NewsArticle":
            return data
    raise ValueError("no NewsArticle JSON-LD found — page layout may have changed")


def _og(html_text: str, prop: str) -> str:
    m = re.search(
        r'<meta property="og:%s" content="([^"]*)"' % re.escape(prop), html_text
    )
    return _html.unescape(m.group(1)) if m else ""


def parse_article_page(html_text: str, url: str = "") -> dict:
    """Parse one article page via its NewsArticle JSON-LD.

    Raises ValueError when the page has no recognizable article (e.g. a
    404 page or a changed layout).
    """
    node = _news_article_node(html_text)
    headline = (node.get("headline") or "").strip()
    if not headline:
        raise ValueError("no article headline found — page layout may have changed")
    body_raw = node.get("articleBody") or ""
    body = [p.strip() for p in body_raw.splitlines() if p.strip()]
    author = node.get("author") or {}
    image = node.get("image") or {}
    if isinstance(image, dict):
        image = image.get("url", "")
    article_id = None
    m = _ID_RE.search((url or "").rstrip("/"))
    if m:
        article_id = int(m.group(1))
    return {
        "id": article_id,
        "title": headline,
        "url": url or node.get("url", ""),
        "summary": _og(html_text, "description") or (node.get("description") or ""),
        "published_at": node.get("datePublished", ""),
        "updated_at": node.get("dateModified", ""),
        "author": author.get("name", "") if isinstance(author, dict) else str(author),
        "source": "Mynet",
        "image": image or _og(html_text, "image"),
        "body": body,
        "body_text": "\n\n".join(body),
    }


# ---------------------------------------------------------------------------
# Gold prices (finans.mynet.com/altin/)
# ---------------------------------------------------------------------------

_GOLD_ROW_RE = re.compile(
    r'<tr[^>]*>\s*<td>\s*<a[^>]*href="https://finans\.mynet\.com/altin/[^"]*"[^>]*'
    r'title="([^"]*)"[^>]*>.*?</a>\s*</td>\s*'
    r'<td[^>]*>([^<]*)</td>\s*'
    r'<td[^>]*>([^<]*)</td>\s*'
    r'<td[^>]*>([^<]*)</td>\s*'
    r'<td[^>]*>.*?<span[^>]*class="ft-change[^"]*"[^>]*>([^<]*)</span>.*?</td>\s*'
    r'<td[^>]*>([^<]*)</td>',
    re.S,
)

_CHANGE_RE = re.compile(r"([+-]?)\s*%?\s*([0-9]+[,.][0-9]+)")


def _parse_tr_number(s: str) -> float | None:
    """Turkish-formatted number ("5.731,95") -> float; None if unparsable."""
    s = (s or "").strip().replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def parse_gold_page(html_text: str) -> list[dict]:
    """The 19 gold products on the altin page (name, last/buy/sell, change, updated).

    Raises ValueError when the table is missing (layout change / block).
    """
    out: list[dict] = []
    for m in _GOLD_ROW_RE.finditer(html_text):
        name, last, buy, sell, change_raw, updated = (
            _html.unescape(g) for g in m.groups()
        )
        change = None
        cm = _CHANGE_RE.search(change_raw.replace("▼", "").replace("▲", ""))
        if cm:
            sign = -1.0 if change_raw.strip().startswith("▼") else 1.0
            change = sign * float(cm.group(2).replace(",", "."))
        out.append(
            {
                "name": clean_text(name),
                "last_try": _parse_tr_number(last),
                "buy_try": _parse_tr_number(buy),
                "sell_try": _parse_tr_number(sell),
                "change_pct": change,
                "updated": clean_text(updated),
                "currency": "USD" if "USD" in name or "Ons Altın / USD" in name else "TRY",
            }
        )
    if not out:
        raise ValueError("no gold-price rows found — page layout may have changed")
    return out


# ---------------------------------------------------------------------------
# Horoscope (one page per sign)
# ---------------------------------------------------------------------------

_SIGNS_TR = {
    "koc": "Koç",
    "boga": "Boğa",
    "ikizler": "İkizler",
    "yengec": "Yengeç",
    "aslan": "Aslan",
    "basak": "Başak",
    "terazi": "Terazi",
    "akrep": "Akrep",
    "yay": "Yay",
    "oglak": "Oğlak",
    "kova": "Kova",
    "balik": "Balık",
}

_SIGNS_EN = {
    "aries": "koc",
    "taurus": "boga",
    "gemini": "ikizler",
    "cancer": "yengec",
    "leo": "aslan",
    "virgo": "basak",
    "libra": "terazi",
    "scorpio": "akrep",
    "sagittarius": "yay",
    "capricorn": "oglak",
    "aquarius": "kova",
    "pisces": "balik",
}


def resolve_sign(value: str) -> str:
    """A Turkish or English sign name -> the URL slug (koc, boga, ...).

    Accepts "Koç", "koc", "aries", "Aries" etc. Raises ValueError on
    an unknown sign.
    """
    v = tr_lower((value or "").strip())
    if v in _SIGNS_TR:
        return v
    if v in _SIGNS_EN:
        return _SIGNS_EN[v]
    # also accept the Turkish display name lowercased
    for slug, name in _SIGNS_TR.items():
        if tr_lower(name) == v:
            return slug
    raise ValueError(
        f"unknown zodiac sign {value!r}: use one of "
        + ", ".join(_SIGNS_TR.values())
        + " (or the English names)"
    )


def parse_horoscope_page(html_text: str, sign_slug: str) -> dict:
    """One sign's daily horoscope: date from <title>, text = longest <p>.

    Raises ValueError when the page has no recognizable horoscope.
    """
    title_m = re.search(r"<title>([^<]*)</title>", html_text)
    title = clean_text(title_m.group(1)) if title_m else ""
    date_m = re.search(
        r"Günlük Yorumu\s+(.+)$", title
    )
    paragraphs = []
    for m in re.finditer(r"<p[^>]*>(.*?)</p>", html_text, re.S):
        txt = clean_text(m.group(1))
        if len(txt) > 40:
            paragraphs.append(txt)
    if not paragraphs:
        raise ValueError("no horoscope text found — page layout may have changed")
    # The daily text is the longest paragraph; the "Favorilerime ekle"
    # help paragraph is much shorter and is filtered by length anyway.
    text = max(paragraphs, key=len)
    return {
        "sign": _SIGNS_TR.get(sign_slug, sign_slug),
        "sign_slug": sign_slug,
        "date": date_m.group(1).strip() if date_m else "",
        "title": title,
        "text": text,
    }


# ---------------------------------------------------------------------------
# Sections (home page nav)
# ---------------------------------------------------------------------------

_SECTION_SKIP = {
    "iletisim", "yardim", "yasal-uyari", "gizlilik-politikasi",
    "editoryal-ilkeler", "iletisim-bilgileri", "rss",
}

_SECTION_RE = re.compile(
    r'<a[^>]*href="(https://www\.mynet\.com/([a-z][a-z0-9-]*)/?)"[^>]*>'
    r"\s*([^<]{2,30}?)\s*</a>",
    re.S,
)


def parse_sections(html_text: str) -> list[dict]:
    """The portal's main sections from the home-page nav (deduped).

    Only single-segment /<section>/ links with a short Turkish label;
    utility links (contact, help, legal) are excluded.
    """
    out: list[dict] = []
    seen: set[str] = set()
    for m in _SECTION_RE.finditer(html_text):
        url, slug, label = m.group(1), m.group(2), clean_text(m.group(3))
        if slug in _SECTION_SKIP or slug in seen:
            continue
        if not label or label.lower().startswith("http"):
            continue
        seen.add(slug)
        out.append({"slug": slug, "label": label, "url": url})
    return out


# ---------------------------------------------------------------------------
# URL resolution for tool inputs
# ---------------------------------------------------------------------------

def resolve_article_url(value: str) -> str:
    """Accept a full article URL or a /haber/... (or -myspor etc.) path.

    A bare numeric id does NOT resolve on mynet.com (/haber/<id> is a
    404) — the server resolves ids through the news sitemap first
    (see server.mynet_get_article).
    """
    value = (value or "").strip()
    if value.startswith("/"):
        return "https://www.mynet.com" + value
    if value.startswith("http"):
        return value
    raise ValueError(
        f"cannot resolve article from {value!r}: pass a full mynet.com "
        "article URL, or a numeric id (resolved via the news sitemap)"
    )
