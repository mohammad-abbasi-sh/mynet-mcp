# mynet-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/mynet-mcp

Unofficial **read-only** MCP server for **Mynet** (www.mynet.com) — one of Türkiye's biggest internet portals (founded 1999): **latest news** (454 recent articles, keyword search, full article text), **live gold prices** from finans.mynet.com (19 products — Gram, Çeyrek, Yarım, Cumhuriyet, Gremse, Ons, incl. Kapalıçarşı rows), **daily horoscope** for all 12 zodiac signs, and the portal's **sections**.

> Part of the "Turkey MCP factory". Not affiliated with Mynet. Data comes from Mynet's own public sitemap and server-rendered pages — no login, no API key, read-only. Gold prices are indicative market prices, not investment advice.

## For AI agents

- **News**: `mynet_latest_news` returns the newest headlines from the site's Google News sitemap (454 recent articles with id, title, URL, publication date, keywords and image). `mynet_search_news` scans the same sitemap by keyword — `"deprem"`, `"altın fiyatları"` — Turkish-aware (dotted/dotless I handled, so `"İSTANBUL"` matches `"İstanbul"`); every word must match the title or keywords.
- **Article**: `mynet_get_article` takes a numeric id (`"110107322088"`, resolved through the news sitemap — a bare id does not resolve on the site itself, `/haber/<id>` is a 404) or a full URL and returns title, summary, published/updated stamps, author, headline image and the full body (paragraphs in order). Also works for `-myspor` / `-mykadin` / `-myyemek` suffixed URLs.
- **Gold**: `mynet_gold_prices` returns the 19 gold products on finans.mynet.com/altin/ — each with last price, buy (Alış), sell (Satış), daily change in percent and update time. Prices are in TRY, except Ons/USD in USD. No arguments.
- **Horoscope**: `mynet_horoscope` takes a Turkish sign name (`"Koç"`, `"Boğa"`, …) or the English name (`"Aries"`, `"Taurus"`, …) and returns the sign, the date the horoscope is for, and the full daily text.
- **Sections**: `mynet_list_sections` returns the portal's main sections (slug → Turkish label), e.g. `"haber"` (Haber), `"spor"` (Spor), `"magazin"` (Magazin), `"yemek"` (Yemek), `"kadin"` (Kadın).
- Every response carries `fetched_at` (UTC) and `source: www.mynet.com`.

## Install

```bash
uvx mynet-mcp
```

Or add to your MCP client config (e.g. Claude Desktop):

```json
{
  "mcpServers": {
    "mynet": {
      "command": "uvx",
      "args": ["mynet-mcp"]
    }
  }
}
```

## Tools

| Tool | What it does |
| --- | --- |
| `mynet_latest_news` | Latest news (newest first, from the news sitemap) |
| `mynet_search_news` | Keyword search over the 454 most recent news articles |
| `mynet_get_article` | Full text of one news article (id or URL) |
| `mynet_gold_prices` | Live gold prices: 19 products with last/buy/sell + daily change |
| `mynet_horoscope` | Today's daily horoscope for one zodiac sign (TR or EN name) |
| `mynet_list_sections` | The portal's main sections (slug → Turkish label) |
| `mynet_health` | Is Mynet reachable right now? |

## Example

Latest news, 21 November 2026:

```json
{ "count": 2,
  "news": [
    { "id": 110107322088, "title": "Milas'ta 24 kaçak göçmen yakalandı",
      "url": "https://www.mynet.com/haber/milasta-24-kacak-gocmen-yakalandi-110107322088",
      "published_at": "2026-11-21T12:18:06+03:00", "keywords": "haber, Güncel",
      "image": "" },
    { "id": 110107322087, "title": "Bilecik merkezli tefecilik operasyonuna 4 tutuklama",
      "url": "https://www.mynet.com/haber/bilecik-merkezli-tefecilik-operasyonuna-4-tutuklama-110107322087",
      "published_at": "2026-11-21T12:16:51+03:00", "keywords": "haber, Güncel" } ] }
```

Gold prices, 21 November 2026:

```json
{ "count": 19,
  "prices": [
    { "name": "Gram Altın", "last_try": 5731.95, "buy_try": 5730.97,
      "sell_try": 5731.95, "change_pct": -3.48, "updated": "20 Kas - 23:59",
      "currency": "TRY" },
    { "name": "Çeyrek Altın", "last_try": 9371.73, "buy_try": 9169.55,
      "sell_try": 9371.73, "change_pct": -3.48, "updated": "20 Kas - 23:59",
      "currency": "TRY" } ] }
```

Horoscope for `"Koç"`, 21 November 2026:

```json
{ "sign": "Koç", "sign_slug": "koc", "date": "21 Kasım 2026",
  "title": "Koç Burcu Günlük Yorumu 21 Kasım 2026",
  "text": "Cesaretin ve kararlılığın bugün ön planda. Yeni projelere atılmak için harika bir zaman. …" }
```

## Caveats

- Search is a **scan of the news sitemap** (454 recent articles), not a full-archive search: the site's own search (`/haber/arama/`) is disallowed in robots.txt, so there is no search API to call.
- A bare numeric article id does **not** resolve on mynet.com (`/haber/<id>` is a 404) — `mynet_get_article` resolves ids through the news sitemap first; pass a full URL for older articles outside the sitemap window.
- Article bodies come from the page's NewsArticle JSON-LD (`articleBody`); horoscope pages have no JSON-LD, so the daily text is the longest paragraph on the page.
- Gold prices are the live table on finans.mynet.com/altin/; the "updated" stamp is the site's own (e.g. "20 Kas - 23:59" for the daily close, "12:11" for Kapalıçarşı rows).
- Member-only pages and personal services (e-okul login, games) are **not** covered — this server is read-only public content only.
- Transport uses Chrome TLS impersonation with a plain-requests fallback; requests are spaced ~0.5s apart.

## Development

```bash
python -m venv .venv && .venv/bin/pip install -e . pytest
.venv/bin/python -m pytest tests/test_parse.py -v   # offline, recorded fixtures
.venv/bin/python -m pytest tests/test_live.py -v    # live, against www.mynet.com
.venv/bin/python tests/smoke_live.py                # daily CI probe
```

## License

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/) — free for personal and non-commercial use; commercial use needs a separate license.

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
