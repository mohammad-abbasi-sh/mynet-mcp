"""Daily smoke probe (CI): latest news + one article + gold + horoscope + health.

Run with:  python tests/smoke_live.py
Exit 0 = site reachable, exit 1 = blocked/error (visible in CI).
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
)


def main() -> int:
    try:
        news = json.loads(mynet_latest_news(5))
        assert "error" not in news, news.get("error")
        assert news["count"] == 5
        assert news["news"][0]["title"]
        art = json.loads(mynet_get_article("110107322088"))
        assert "error" not in art, art.get("error")
        assert art["title"].startswith("Milas'ta 24 kaçak göçmen yakalandı")
        assert len(art["body"]) >= 1
        gold = json.loads(mynet_gold_prices())
        assert "error" not in gold, gold.get("error")
        assert gold["count"] >= 15
        horo = json.loads(mynet_horoscope("Koç"))
        assert "error" not in horo, horo.get("error")
        assert horo["sign"] == "Koç"
        health = json.loads(mynet_health())
        assert health["status"] == "ok", health
        print(
            f"SMOKE OK: news[0]={news['news'][0]['title'][:60]} | "
            f"article body={len(art['body'])} blocks | "
            f"gold={gold['count']} products | horoscope={horo['date']}"
        )
        return 0
    except Exception as e:  # noqa: BLE001 — smoke must report, not crash
        print(f"SMOKE FAIL: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
