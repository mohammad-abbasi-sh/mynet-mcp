# mynet-mcp 🇹🇷

mcp-name: io.github.mohammad-abbasi-sh/mynet-mcp

سرور MCP غیررسمی و **فقط‌خواندنی** برای **Mynet** (سایت www.mynet.com) — یکی از بزرگ‌ترین پورتال‌های اینترنتی ترکیه (از ۱۹۹۹): **اخبار تازه** (۴۵۴ خبر اخیر، جست‌وجوی کلیدواژه، متن کامل خبر)، **قیمت زندهٔ طلا** از سایت finans.mynet.com (۱۹ محصول — گرم، ربع، نیم، جمهوری، گرمسه، اونس، شامل ردیف‌های بازار سرپوشیدهٔ استانبول)، **فال روزانه** برای هر ۱۲ نشان زودیاک، و **بخش‌های** پورتال.

> بخشی از پروژهٔ «کارخانهٔ MCP ترکیه». وابسته به Mynet نیست. داده‌ها از نقشهٔ سایت عمومی و صفحات سرور-رندرشدهٔ خود Mynet می‌آیند — بدون ورود، بدون کلید API، فقط‌خواندنی. قیمت‌های طلا قیمت‌های نشانگر بازارند، نه توصیهٔ سرمایه‌گذاری.

## برای ایجنت‌های هوش مصنوعی

- **اخبار**: `mynet_latest_news` تازه‌ترین تیترها را از نقشهٔ سایت Google News می‌آورد (۴۵۴ خبر اخیر با شناسه، تیتر، نشانی، تاریخ انتشار، کلیدواژه‌ها و تصویر). `mynet_search_news` در همان نقشهٔ سایت با کلیدواژه جست‌وجو می‌کند — `"deprem"`، `"altın fiyatları"` — با حساسیت به ترکی (I نقطه‌دار/بی‌نقطه رعایت می‌شود، پس `"İSTANBUL"` با `"İstanbul"` مطابقت دارد)؛ هر کلمه باید در تیتر یا کلیدواژه‌ها باشد.
- **متن خبر**: `mynet_get_article` یک شناسهٔ عددی (`"110107322088"` — از طریق نقشهٔ سایت خبر حل می‌شود؛ شناسهٔ تنها در خود سایت حل نمی‌شود، `/haber/<id>` خطای ۴۰۴ می‌دهد) یا نشانی کامل می‌گیرد و تیتر، خلاصه، زمان انتشار/به‌روزرسانی، نویسنده، تصویر سرخط و متن کامل خبر (پاراگراف‌ها به ترتیب) را برمی‌گرداند. برای نشانی‌های با پسوند `-myspor` / `-mykadin` / `-myyemek` هم کار می‌کند.
- **طلا**: `mynet_gold_prices` ۱۹ محصول طلا را از صفحهٔ finans.mynet.com/altin/ برمی‌گرداند — هرکدام با آخرین قیمت، خرید (Alış)، فروش (Satış)، تغییر روزانه به درصد و زمان به‌روزرسانی. قیمت‌ها به لیر ترکیه‌اند، به‌جز اونس/دلار که به دلار است. آرگومان نمی‌گیرد.
- **فال**: `mynet_horoscope` نام ترکی نشان (`"Koç"`، `"Boğa"`، …) یا نام انگلیسی (`"Aries"`، `"Taurus"`، …) را می‌گیرد و نشان، تاریخی که فال برای آن است و متن کامل فال روزانه را برمی‌گرداند.
- **بخش‌ها**: `mynet_list_sections` بخش‌های اصلی پورتال را برمی‌گرداند (نام کوتاه ← برچسب ترکی)، مثلاً `"haber"` (خبر)، `"spor"` (ورزش)، `"magazin"` (مجله)، `"yemek"` (غذا)، `"kadin"` (زن).
- هر پاسخ شامل `fetched_at` (به وقت UTC) و `source: www.mynet.com` است.

## نصب

```bash
uvx mynet-mcp
```

یا به پیکربندی کلاینت MCP خود اضافه کنید (مثلاً Claude Desktop):

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

## ابزارها

| ابزار | چه می‌کند؟ |
| --- | --- |
| `mynet_latest_news` | تازه‌ترین اخبار (از جدید به قدیم، از نقشهٔ سایت خبر) |
| `mynet_search_news` | جست‌وجوی کلیدواژه در ۴۵۴ خبر اخیر |
| `mynet_get_article` | متن کامل یک خبر (شناسه یا نشانی) |
| `mynet_gold_prices` | قیمت زندهٔ طلا: ۱۹ محصول با آخرین/خرید/فروش + تغییر روزانه |
| `mynet_horoscope` | فال امروز یک نشان زودیاک (نام ترکی یا انگلیسی) |
| `mynet_list_sections` | بخش‌های اصلی پورتال (نام کوتاه ← برچسب ترکی) |
| `mynet_health` | آیا Mynet الان در دسترس است؟ |

## نمونه

تازه‌ترین اخبار، ۲۱ نوامبر ۲۰۲۶:

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

قیمت طلا، ۲۱ نوامبر ۲۰۲۶:

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

فال `"Koç"`، ۲۱ نوامبر ۲۰۲۶:

```json
{ "sign": "Koç", "sign_slug": "koc", "date": "21 Kasım 2026",
  "title": "Koç Burcu Günlük Yorumu 21 Kasım 2026",
  "text": "Cesaretin ve kararlılığın bugün ön planda. Yeni projelere atılmak için harika bir zaman. …" }
```

## نکات

- جست‌وجو **اسکن نقشهٔ سایت خبر** است (۴۵۴ خبر اخیر)، نه جست‌وجوی کامل آرشیو: جست‌وجوی خود سایت (`/haber/arama/`) در robots.txt مسدود است، پس API جست‌وجویی برای فراخوانی وجود ندارد.
- شناسهٔ عددی تنها در mynet.com **حل نمی‌شود** (`/haber/<id>` خطای ۴۰۴ می‌دهد) — `mynet_get_article` شناسه‌ها را نخست از نقشهٔ سایت خبر حل می‌کند؛ برای خبرهای قدیمی‌ترِ بیرون از پنجرهٔ نقشهٔ سایت، نشانی کامل بدهید.
- متن خبرها از بلوک JSON-LD از نوع NewsArticle در صفحه (`articleBody`) می‌آید؛ صفحه‌های فال JSON-LD ندارند، پس متن روزانه بلندترین پاراگراف صفحه است.
- قیمت‌های طلا جدول زندهٔ صفحهٔ finans.mynet.com/altin/ است؛ مهر زمانی «updated» مال خود سایت است (مثلاً «20 Kas - 23:59» برای بسته‌شدن روزانه، «12:11» برای ردیف‌های بازار سرپوشیده).
- صفحه‌های مخصوص اعضا و سرویس‌های شخصی (ورود e-okul، بازی‌ها) **پوشش داده نمی‌شوند** — این سرور فقط محتوای عمومی را به‌صورت فقط‌خواندنی ارائه می‌دهد.
- انتقال با جعل TLS کروم و پشتیبان درخواست ساده انجام می‌شود؛ درخواست‌ها با فاصلهٔ حدود ۰٫۵ ثانیه فرستاده می‌شوند.

## توسعه

```bash
python -m venv .venv && .venv/bin/pip install -e . pytest
.venv/bin/python -m pytest tests/test_parse.py -v   # آفلاین، با نمونه‌های ضبط‌شده
.venv/bin/python -m pytest tests/test_live.py -v    # زنده، در برابر www.mynet.com
.venv/bin/python tests/smoke_live.py                # بررسی روزانهٔ CI
```

## مجوز

[PolyForm Noncommercial 1.0.0](https://polyformproject.org/licenses/noncommercial/1.0.0/) — برای استفادهٔ شخصی و غیرتجاری رایگان است؛ استفادهٔ تجاری نیازمند مجوز جداگانه است.

Built by [Mohammad Abbasi](https://github.com/mohammad-abbasi-sh) — [Almanibama](https://almanibama.ir) · [mabbasi.ir](https://mabbasi.ir)
