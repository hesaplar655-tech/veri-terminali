# Veri Terminali

**Canli site:** https://efe111.pythonanywhere.com/ (PythonAnywhere Developer plan,
always-on task olarak `scheduler.py` calisiyor)
**Kod:** https://github.com/hesaplar655-tech/veri-terminali

## Yapi
- `sources/` - her veri kaynagi icin bir dosya + `fetch()` fonksiyonu. `sources/__init__.py`
  icindeki `SOURCES` listesine kaydedilir (baslik, frekans).
  - `ekonomik_takvim.py` - TradingView'in genel widget API'sinden
    (`economic-calendar.tradingview.com/events`) TR/US/EU/GB/AU/JP icin veri
    ceker. Sadece bir `Referer` header'i yeterli, kimlik dogrulama gerekmiyor.
    investing.com Cloudflare arkasinda oldugu icin dogrudan kazinamiyor;
    doviz.com kazinabiliyordu ama hicbir zaman "Beklenti" (forecast)
    vermiyordu ve keyfi tarih araligi desteklemiyordu (ay siniri sorunu
    vardi). TradingView tek istekte ay sinirini asan herhangi bir tarih
    araligini, Turkiye dahil tum ulkeler icin forecast+actual+previous ile
    donduruyor. Tum olay adlari Ingilizce (Turkiye dahil - ceviri yapilmiyor,
    kullanicinin tercihiyle).
  - `sp500_concentration.py` - AMEX:SPY ve CBOE:MAGS icin TradingView'den
    (`tvDatafeed` kutuphanesi, TradingView'in grafik websocket protokolu,
    kimlik dogrulama gerekmeden) gunluk kapanis fiyati ceker; SPY'nin 200
    gunluk ortalamaya gore konumunu ve SPY-MAGS arasindaki 3 aylik getiri
    farkini hesaplar. CBOE:MAGS 2023 Nisan'da islem gormeye basladigi ve
    nologin erisim ~Kasim 2023'ten itibaren veri verdigi icin grafik daha
    eskiye gidemiyor - kaynagin dogal siniri. `daily_at_tr="23:00"` ile
    Turkiye saatiyle gunde 1 kez calisir. Sayfasi
    `templates/sp500_concentration.html` icinde Chart.js ile ozel bir dual-axis
    grafik (fiyat + 3 aylik fark, 200g ortalamaya gore arka plan golgelendirme,
    lejanttan acilir/kapanir, genislik/yukseklik girisiyle boyutu ayarlanabilir).
  - `sp500_breadth.py` - SPCFD:SPX (fiyat) ve INDEX:S5TH (S&P 500 hisselerinin
    200g ortalamanin uzerinde olan yuzdesi, "genislik/breadth") icin
    TradingView'den gunluk veri ceker, 2019-01-01'den itibaren. `daily_at_tr=
    "23:00"`. Sayfasi `templates/sp500_breadth.html` icinde dual-axis grafik
    (fiyat cizgisi + breadth bar chart), lejanttan acilir/kapanir, genislik/
    yukseklik girisiyle boyutu ayarlanabilir.
  - `market_relative.py` - SPCFD:SPX, CFI:US100 (Nasdaq) ve AMEX:RSP (S&P 500
    Esit Agirlikli) icin saatlik veri ceker (`interval_unit="hours"`), her
    birini kendi o ana kadarki zirvesine gore % geri cekilme (rolling
    drawdown) olarak normalize eder. CFI:US100'un nologin saatlik gecmisi en
    kisa olani (~Ocak 2025) - ortak baslangic noktasi buna gore. Sayfasi
    `templates/market_relative.html` icinde uc cizgili (tek eksen) grafik,
    hepsi lejanttan acilir/kapanir.
  - `sector_breadth.py` - S&P 500 + 11 GICS sektor ETF'i (AMEX:XLY, XLP, XLE,
    XLF, XLV, XLI, XLK, XLB, XLRE, XLC, XLU) icin gunluk mum verisi + o
    sektordeki hisselerin % kaci 20 gunluk ortalamanin uzerinde (breadth).
    Breadth ticker'lari (INDEX:SYTW, SPTW, SETW, SFTW, SVTW, SITW, SKTW,
    SBTW, SSTW, SLTW, SUTW, S&P 500 icin S5TW) TradingView'in kendi sembol
    arama API'sinden (symbol-search.tradingview.com, Barchart kaynakli)
    bulundu - resmi/belgelenmis degil, sembol arama sonuclarindan tespit
    edildi ve tvDatafeed ile dogrulandi. Sayfasi `templates/sector_breadth.html`
    icinde 12 kartlik bir izgara (chartjs-chart-financial ile gercek mum
    grafik + breadth cizgisi, ikisi de lejanttan acilir/kapanir); bir karta
    tiklayinca buyutulmus, kendi tarih araligi kaydiricili bir modalda acilir.
- `static/date-range-slider.js` - grafik kartlarinin altina eklenen, yeniden
  kullanilabilir cift tutamacli tarih araligi kaydiricisi (mini onizleme +
  Chart.js x ekseni zoom).
- `storage.py` - veriyi `data/<key>.json` olarak yazar/okur.
- `scheduler.py` - surekli calisan process; her kaynagi kendi frekansinda tetikler.
  PythonAnywhere'de bir **Always-on task** olarak calistirilir.
- `app.py` - Flask uygulamasi:
  - `/` - giris sayfasi: bugunun tarihi + gecen hafta ile onumuzdeki hafta
    arasi (bugun-7 .. bugun+6, 14 gun, bugun dahil, her gun icin ayri blok)
    ekonomik takvim, "Devam Et" butonu.
  - `/panel` - diger veri kaynaklarinin kart goruntusu (ekonomik takvim disinda).
  - `/sayfa/<key>` - bir kartin detay sayfasi (su an ham JSON basiyor, ozellestirilecek).
- `templates/`, `static/` - sayfa goruntusu.

### Bilinen kaynak sinirlamalari
- **Beklenti kapsam orani:** TradingView'in ucretsiz widget feed'i her olay
  icin forecast vermiyor (kucuk/niche gostergelerde bos kalabiliyor).
  Pratikte olaylarin ~%35-40'inda beklenti geliyor (doviz.com/ForexFactory
  kombinasyonuna gore belirgin iyilesme, ve artik Turkiye'yi de kapsiyor).
- Bu, TradingView'in resmi/belgelenmis bir public API'si degil - widget'in
  kendi arka uc endpoint'i. Ileride Referer kontrolu veya rate limit
  sikilastirilabilir; boyle bir durumda hata scheduler loglarinda gorunur.

## Yeni bir sayfa/veri kaynagi eklemek
1. `sources/<isim>.py` olustur, icine bir `fetch()` fonksiyonu yaz (dict/list donsun).
2. `sources/__init__.py` -> `SOURCES` listesine bir `Source(...)` satiri ekle:
   - duzenli aralik icin `interval_unit` + `interval_value`, VEYA
   - TR saatiyle gunde 1 kez icin `daily_at_tr="HH:MM"`.
3. Gerekirse `templates/page.html`'i o veri icin ozellestir (varsayilan ham JSON
   basar), ya da ozel bir sayfa istiyorsan yeni bir template yazip `app.py`
   icindeki `CUSTOM_TEMPLATES` sozlugune `key: "template.html"` ekle.
4. `python scheduler.py` calistirinca yeni kaynak da otomatik islenir.

## Canli siteyi guncellemek (PythonAnywhere)
```bash
# PythonAnywhere Bash konsolunda:
cd ~/veri-terminali
git pull
venv/bin/pip install -r requirements.txt   # yeni bagimlilik eklendiyse
```
Sonra **Web** sekmesinden **Reload**, **Tasks** sekmesinden always-on task'i
**Restart** et (kod veya zamanlama degistiyse).

## Yerelde calistirma
```bash
python -m venv .venv
.venv/Scripts/activate   # Windows
pip install -r requirements.txt

# Terminal 1: veriyi cek/guncelle
python scheduler.py

# Terminal 2: siteyi goster
python app.py
```
Tarayicida http://127.0.0.1:5000 adresine gidin.

## PythonAnywhere'e kurulum (ucretli plan)
1. **Files**: bu klasoru `Files` sekmesinden yukleyin ya da bir Bash konsolunda
   `git clone` edin (proje git'e baglanirsa).
2. **Konsoldan**: sanal ortam kurun ve bagimliliklari yukleyin:
   ```bash
   cd ~/veri-terminali
   python3.10 -m venv venv
   pip install -r requirements.txt
   ```
3. **Web** sekmesi -> "Add a new web app" -> Manual configuration -> Python 3.10 -> Flask.
   - Virtualenv yolunu `/home/<kullaniciadi>/veri-terminali/venv` olarak ayarlayin.
   - WSGI dosyasini (`/var/www/<kullaniciadi>_pythonanywhere_com_wsgi.py`) su sekilde duzenleyin:
     ```python
     import sys
     path = '/home/<kullaniciadi>/veri-terminali'
     if path not in sys.path:
         sys.path.insert(0, path)

     from app import app as application
     ```
4. **Tasks** sekmesi -> **Always-on tasks** (sadece ucretli planlarda gorunur) ->
   komut olarak:
   ```bash
   /home/<kullaniciadi>/veri-terminali/venv/bin/python /home/<kullaniciadi>/veri-terminali/scheduler.py
   ```
5. Web app'i reload edin. `data/` klasoru scheduler tarafindan doldurulunca sayfalar
   otomatik gorunur.

## Notlar
- `data/*.json` git'e girmiyor (`.gitignore`), sunucuda scheduler tarafindan uretiliyor.
- Her kaynagin frekansi bagimsizdir; scheduler tek process olarak hepsini yonetir.
- Domain baglaninca sadece PythonAnywhere'in "Web" sekmesinden custom domain
  ayarlanmasi yeterli, kod tarafinda degisiklik gerekmiyor.
