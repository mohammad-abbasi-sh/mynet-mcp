# mynet-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/mynet-mcp

**Mynet** (www.mynet.com) için resmi olmayan, **salt okunur** MCP sunucusu — Türkiye'nin en büyük internet portallarından biri (1999'dan beri): **güncel haberler** (454 son haber, anahtar kelime araması, haber metni), **canlı altın fiyatları** (finans.mynet.com — Gram, Çeyrek, Yarım, Cumhuriyet, Gremse, Ons dahil 19 ürün, Kapalıçarşı satırlarıyla), **günlük burç yorumları** (12 burç) ve portalın **bölümleri**.

> "Turkey MCP factory" projesinin bir parçasıdır. Mynet ile bağlantısı yoktur. Veriler Mynet'in kendi herkese açık site haritasından ve sunucu taraflı sayfalarından gelir — giriş yok, API anahtarı yok, salt okunur. Altın fiyatları gösterge niteliğindeki piyasa fiyatlarıdır, yatırım tavsiyesi değildir.

## Yapay zekâ ajanları için

- **Haberler**: `mynet_latest_news`, sitenin Google Haberler site haritasındaki en yeni başlıkları döndürür (454 son haber; kimlik, başlık, URL, yayın tarihi, anahtar kelimeler ve görsel). `mynet_search_news` aynı site haritasında anahtar kelimeyle arar — `"deprem"`, `"altın fiyatları"` — Türkçe duyarlıdır (noktalı/noktasız I işlenir, yani `"İSTANBUL"`, `"İstanbul"` ile eşleşir); her kelimenin başlıkta veya anahtar kelimelerde geçmesi gerekir.
- **Haber detayı**: `mynet_get_article` sayısal kimlik (`"110107322088"` — haber site haritası üzerinden çözülür; çıplak kimlik sitenin kendisinde çözülmez, `/haber/<id>` 404 verir) veya tam URL alır; başlık, özet, yayın/güncelleme zamanları, yazar, manşet görseli ve haber metninin tamamını (paragraflar sırasıyla) döndürür. `-myspor` / `-mykadin` / `-myyemek` son ekli URL'lerde de çalışır.
- **Altın**: `mynet_gold_prices`, finans.mynet.com/altin/ sayfasındaki 19 altın ürününü döndürür — her biri son fiyat, alış, satış, günlük yüzde değişim ve güncelleme saatiyle. Fiyatlar TL'dir; Ons/USD, USD cinsindendir. Argüman almaz.
- **Burç**: `mynet_horoscope` Türkçe burç adı (`"Koç"`, `"Boğa"`, …) veya İngilizce adı (`"Aries"`, `"Taurus"`, …) alır; burcu, yorumun ait olduğu tarihi ve günlük yorum metninin tamamını döndürür.
- **Bölümler**: `mynet_list_sections` portalın ana bölümlerini döndürür (kısa ad → Türkçe etiket), örn. `"haber"` (Haber), `"spor"` (Spor), `"magazin"` (Magazin), `"yemek"` (Yemek), `"kadin"` (Kadın).
- Her yanıt `fetched_at` (UTC) ve `source: www.mynet.com` taşır.

## Kurulum

```bash
uvx mynet-mcp
```

Veya MCP istemcinizin yapılandırmasına ekleyin (ör. Claude Desktop):

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

## Araçlar

| Araç | Ne yapar? |
| --- | --- |
| `mynet_latest_news` | En yeni haberler (yeniden eskiye, haber site haritasından) |
| `mynet_search_news` | 454 son haber arasında anahtar kelime araması |
| `mynet_get_article` | Bir haberin tam metni (kimlik veya URL) |
| `mynet_gold_prices` | Canlı altın fiyatları: 19 ürün, son/alış/satış + günlük değişim |
| `mynet_horoscope` | Bir burcun bugünkü yorumu (TR veya EN ad) |
| `mynet_list_sections` | Portalın ana bölümleri (kısa ad → Türkçe etiket) |
| `mynet_health` | Mynet şu an erişilebilir mi? |

## Örnek

21 Kasım 2026 tarihli en yeni haberler:

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

21 Kasım 2026 tarihli altın fiyatları:

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

21 Kasım 2026 tarihli `"Koç"` burç yorumu:

```json
{ "sign": "Koç", "sign_slug": "koc", "date": "21 Kasım 2026",
  "title": "Koç Burcu Günlük Yorumu 21 Kasım 2026",
  "text": "Cesaretin ve kararlılığın bugün ön planda. Yeni projelere atılmak için harika bir zaman. …" }
```

## Uyarılar

- Arama, **haber site haritasının taranmasıdır** (454 son haber), tam arşiv araması değildir: sitenin kendi araması (`/haber/arama/`) robots.txt'de engellidir, çağrılacak bir arama API'si yoktur.
- Çıplak sayısal haber kimliği mynet.com'da **çözülmez** (`/haber/<id>` 404 verir) — `mynet_get_article` kimlikleri önce haber site haritasından çözer; site haritası penceresinin dışındaki eski haberler için tam URL verin.
- Haber metinleri sayfadaki NewsArticle JSON-LD bloğundan (`articleBody`) gelir; burç sayfalarında JSON-LD yoktur, günlük yorum sayfadaki en uzun paragraftır.
- Altın fiyatları finans.mynet.com/altin/ sayfasındaki canlı tablodur; "updated" damgası sitenin kendisinindir (örn. günlük kapanış için "20 Kas - 23:59", Kapalıçarşı satırları için "12:11").
- Üyelere özel sayfalar ve kişisel hizmetler (e-okul girişi, oyunlar) **kapsanmaz** — bu sunucu yalnızca herkese açık içeriği salt okunur olarak sunar.
- Aktarım, düz istek yedeğiyle Chrome TLS kimlik bürünmesi kullanır; istekler ~0,5 sn arayla yapılır.

## Geliştirme

```bash
python -m venv .venv && .venv/bin/pip install -e . pytest
.venv/bin/python -m pytest tests/test_parse.py -v   # çevrimdışı, kayıtlı örnekler
.venv/bin/python -m pytest tests/test_live.py -v    # canlı, www.mynet.com'a karşı
.venv/bin/python tests/smoke_live.py                # günlük CI denetimi
```

## Lisans

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/) — kişisel ve ticari olmayan kullanım için ücretsizdir; ticari kullanım ayrı bir lisans gerektirir.

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
