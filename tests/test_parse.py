"""Offline tests for mynet_mcp parsers (recorded fixtures, no network).

Fixtures (recorded 2026-11-21 from www.mynet.com / finans.mynet.com):
- sitemap-news.xml — Google News sitemap, 454 recent articles
- article-110107322088.html — "Milas'ta 24 kaçak göçmen yakalandı"
  (Güncel, 21 Nov 2026, author Devrim Karadağ, 3 body blocks)
- gold-prices.html — finans.mynet.com/altin/ (19 gold products)
- horoscope-koc.html — "Koç Burcu Günlük Yorumu 21 Kasım 2026"
- home.html — the home page (29 sections in the nav)

Run with:  python -m pytest tests/test_parse.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mynet_mcp import parse as P  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"


def _read(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


# --- sitemap ----------------------------------------------------------------

def test_news_sitemap_count_and_first():
    items = P.parse_news_sitemap(_read("sitemap-news.xml"))
    assert len(items) == 454
    first = items[0]
    assert first["id"] == 110107322088
    assert first["title"] == "Milas'ta 24 kaçak göçmen yakalandı"
    assert first["url"] == (
        "https://www.mynet.com/haber/milasta-24-kacak-gocmen-yakalandi-110107322088"
    )
    assert first["published_at"] == "2026-11-21T12:18:06+03:00"
    assert first["keywords"] == "haber, Güncel"
    # newest first, oldest last
    assert items[-1]["published_at"] == "2026-11-19T12:20:27+03:00"


def test_search_turkish_aware():
    items = P.parse_news_sitemap(_read("sitemap-news.xml"))
    assert len(P.search_items(items, "ALTIN")) == 5
    # every word must match; dotted/dotless I handled
    found = P.search_items(items, "Istanbul")
    assert all("istanbul" in P.tr_lower(f"{i['title']} {i['keywords']}") for i in found)
    assert P.search_items(items, "zzzznomatch") == []


def test_find_by_id():
    items = P.parse_news_sitemap(_read("sitemap-news.xml"))
    hit = P.find_by_id(items, 110107322088)
    assert hit is not None
    assert hit["title"] == "Milas'ta 24 kaçak göçmen yakalandı"
    assert P.find_by_id(items, 123) is None


def test_sitemap_bad_xml():
    try:
        P.parse_news_sitemap("<not xml")
    except ValueError:
        return
    raise AssertionError("expected ValueError for bad XML")


# --- article ----------------------------------------------------------------

def test_article_page():
    art = P.parse_article_page(
        _read("article-110107322088.html"),
        "https://www.mynet.com/haber/milasta-24-kacak-gocmen-yakalandi-110107322088",
    )
    assert art["id"] == 110107322088
    assert art["title"].startswith("Milas'ta 24 kaçak göçmen yakalandı")
    assert art["author"] == "Devrim Karadağ"
    assert art["published_at"] == "2026-11-21T12:18:58+03:00"
    assert art["image"].startswith("https://imgrosetta.mynet.com.tr/")
    assert len(art["body"]) == 3
    assert art["body"][0].startswith("Sahil Güvenlik Komutanlığı")
    assert "24 kaçak göçmeni yakaladı" in art["body_text"]


def test_article_page_no_jsonld():
    try:
        P.parse_article_page("<html><head><title>x</title></head><body>no ld</body></html>")
    except ValueError:
        return
    raise AssertionError("expected ValueError for a page without NewsArticle JSON-LD")


# --- gold -------------------------------------------------------------------

def test_gold_page_count_and_rows():
    gold = P.parse_gold_page(_read("gold-prices.html"))
    assert len(gold) == 19
    gram = gold[1]
    assert gram["name"] == "Gram Altın"
    assert gram["last_try"] == 5731.95
    assert gram["buy_try"] == 5730.97
    assert gram["sell_try"] == 5731.95
    assert gram["change_pct"] == -3.48
    assert gram["updated"] == "20 Kas - 23:59"
    assert gram["currency"] == "TRY"
    ons = gold[2]
    assert ons["name"] == "Ons Altın / USD"
    assert ons["currency"] == "USD"
    assert ons["last_try"] == 3525.42
    # Kapalıçarşı rows present
    assert any("Kapalı" in g["name"] for g in gold)
    # all rows have numeric prices
    assert all(g["last_try"] and g["buy_try"] and g["sell_try"] for g in gold)


def test_gold_page_no_table():
    try:
        P.parse_gold_page("<html><body>no table here</body></html>")
    except ValueError:
        return
    raise AssertionError("expected ValueError for a page without gold rows")


# --- horoscope --------------------------------------------------------------

def test_horoscope_page():
    horo = P.parse_horoscope_page(_read("horoscope-koc.html"), "koc")
    assert horo["sign"] == "Koç"
    assert horo["sign_slug"] == "koc"
    assert horo["date"] == "21 Kasım 2026"
    assert horo["text"].startswith("Cesaretin ve kararlılığın bugün ön planda")


def test_resolve_sign():
    assert P.resolve_sign("Koç") == "koc"
    assert P.resolve_sign("koc") == "koc"
    assert P.resolve_sign("Aries") == "koc"
    assert P.resolve_sign("pisces") == "balik"
    assert P.resolve_sign("BALIK") == "balik"
    try:
        P.resolve_sign("notasign")
    except ValueError:
        return
    raise AssertionError("expected ValueError for an unknown sign")


# --- sections ---------------------------------------------------------------

def test_sections():
    secs = P.parse_sections(_read("home.html"))
    assert len(secs) == 29
    slugs = {s["slug"] for s in secs}
    for want in ("haber", "spor", "magazin", "yemek", "kadin", "video"):
        assert want in slugs
    assert "iletisim" not in slugs  # utility links excluded
    assert secs[0]["label"] == "HABER"


# --- url resolution ---------------------------------------------------------

def test_resolve_article_url():
    assert P.resolve_article_url(
        "https://www.mynet.com/haber/x-110107322088"
    ) == "https://www.mynet.com/haber/x-110107322088"
    assert P.resolve_article_url("/haber/x-110107322088") == (
        "https://www.mynet.com/haber/x-110107322088"
    )
    try:
        P.resolve_article_url("110107322088")
    except ValueError:
        return
    raise AssertionError("expected ValueError for a bare numeric id")
