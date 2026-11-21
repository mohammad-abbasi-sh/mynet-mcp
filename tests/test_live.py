"""Live tests for mynet_mcp (real network, read-only).

Run with:  python -m pytest tests/test_live.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from mynet_mcp.server import (  # noqa: E402
    mynet_get_article,
    mynet_gold_prices,
    mynet_health,
    mynet_horoscope,
    mynet_latest_news,
    mynet_list_sections,
    mynet_search_news,
)


def test_live_latest_news():
    news = json.loads(mynet_latest_news(5))
    assert "error" not in news, news.get("error")
    assert news["count"] == 5
    assert news["news"][0]["title"]
    assert news["news"][0]["url"].startswith("https://www.mynet.com/haber/")


def test_live_search_news():
    found = json.loads(mynet_search_news("altın", 5))
    assert "error" not in found, found.get("error")
    assert found["total_matches"] >= 1
    assert found["news"][0]["title"]


def test_live_get_article_by_id():
    art = json.loads(mynet_get_article("110107322088"))
    assert "error" not in art, art.get("error")
    assert art["title"].startswith("Milas'ta 24 kaçak göçmen yakalandı")
    assert art["author"]
    assert len(art["body"]) >= 1


def test_live_get_article_by_url():
    art = json.loads(
        mynet_get_article(
            "https://www.mynet.com/haber/milasta-24-kacak-gocmen-yakalandi-110107322088"
        )
    )
    assert "error" not in art, art.get("error")
    assert art["id"] == 110107322088


def test_live_get_article_unknown_id():
    art = json.loads(mynet_get_article("123"))
    assert "error" in art


def test_live_gold_prices():
    gold = json.loads(mynet_gold_prices())
    assert "error" not in gold, gold.get("error")
    assert gold["count"] >= 15
    gram = next(g for g in gold["prices"] if g["name"] == "Gram Altın")
    assert gram["last_try"] and gram["last_try"] > 1000
    assert gram["buy_try"] <= gram["sell_try"]


def test_live_horoscope():
    horo = json.loads(mynet_horoscope("Koç"))
    assert "error" not in horo, horo.get("error")
    assert horo["sign"] == "Koç"
    assert len(horo["text"]) > 100
    horo_en = json.loads(mynet_horoscope("Aries"))
    assert "error" not in horo_en, horo_en.get("error")
    assert horo_en["sign_slug"] == "koc"


def test_live_horoscope_unknown_sign():
    horo = json.loads(mynet_horoscope("notasign"))
    assert "error" in horo


def test_live_list_sections():
    secs = json.loads(mynet_list_sections())
    assert "error" not in secs, secs.get("error")
    assert secs["count"] >= 15
    slugs = {s["slug"] for s in secs["sections"]}
    assert "haber" in slugs and "spor" in slugs


def test_live_health():
    health = json.loads(mynet_health())
    assert health["status"] == "ok", health
