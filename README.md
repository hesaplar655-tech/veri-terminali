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
    tiklayinca buyutulmus, kendi tarih araligi kaydiricili bir modalda acilir;
    Z-Score paneli (breadth'in son 6 aylik ortalamaya gore kac std sapma
    uzakta oldugu) da bu modalin altinda.
  - `index_breadth.py` - S&P 500, Nasdaq Composite ve Russell 2000 icin "%
    uyeler 50/200 gunluk ortalamanin uzerinde" (INDEX:S5FI/S5TH,
    INDEX:NCFI/NCTH, INDEX:R2FI/R2TH). S&P 500 disindaki ticker'lar da
    TradingView'in sembol arama API'sinden bulunup tvDatafeed ile
    dogrulandi. Sayfasi `templates/index_breadth.html` icinde iki ust uste
    grafik (50g, 200g), uc endeks de lejanttan acilir/kapanir, her grafigin
    kendi bagimsiz tarih araligi kaydiricisi var (biri digerini zoomlamaz).
  - `rsi_breadth.py` - S&P 500 uyelerinin yuzde kacinin 14 gunluk RSI'i 70'in
    uzerinde (asiri alim) ve yuzde kacinin 30'un altinda (asiri satim)
    oldugu. Bu veri TradingView'de arastirildi (sembol arama API'si + tahmin
    edilebilir ticker kaliplari - S5RH, S5RSI, S5OB vb.) ama bulunamadi;
    bunun yerine ham kapanis fiyatlarini Yahoo Finance chart API'sinden
    (query1.finance.yahoo.com, hizli, kimlik dogrulama gerektirmiyor) tum
    503 S&P 500 uyesi icin cekip RSI'i kendimiz hesapliyoruz (Wilder'in
    yumusatma yontemi, EWM alpha=1/14). Uye listesi Wikipedia'nin "List of
    S&P 500 companies" tablosundan aliniyor. 503 hisse icin cekim ~2-3
    dakika suruyor ama neredeyse tamami ag bekleme suresi (CPU degil),
    PythonAnywhere'in CPU-saniye kotasini pratikte zorlamiyor;
    `daily_at_tr="23:00"` ile gunde 1 kez calisir. Karsilastirma icin S&P 500
    (SPCFD:SPX) gunluk kapanis fiyati da her zamanki tercih olan
    TradingView'den (tvDatafeed) cekilip ikinci eksende cizgi olarak
    ekleniyor. Sayfasi `templates/rsi_breadth.html` icinde dual-axis
    Bloomberg tarzi grafik (turkuaz: SPX fiyati sag eksen; mavi: >70
    yukarida, turuncu: <30 asagida negatif eksende gosteriliyor ama deger
    her zaman pozitif yuzde, sol eksen), hepsi lejanttan acilir/kapanir,
    tarih araligi kaydiricisi ve genislik/yukseklik girisi var.
  - `bist100_rsi_breadth.py` - `rsi_breadth.py` ile ayni mantik (BIST 100
    icin), ama ham fiyat verisi TradingView'den (tvDatafeed) cekiliyor -
    BIST 100'un sadece 100 uyesi oldugu icin (S&P 500'un 503'u yerine)
    kullanicinin standart tercihi olan TradingView burada performans
    sorunu yaratmiyor. Uye listesi icin Wikipedia'daki gibi otomatik
    guncellenen bir kaynak bulunamadi; TradingView'in kendi bilesen sayfasi
    (tr.tradingview.com/symbols/BIST-XU100/components/) ve Midas
    (getmidas.com/canli-borsa/xu100-bist-100-hisseleri) ile capraz
    kontrol edilip koda sabit olarak yazildi - BIST 100 bilesimi ceyreklik
    degisebildigi icin bu liste zamanla hafifce eskiyebilir. RSI(14)
    Wilder'in yumusatma yontemiyle hesaplaniyor. Karsilastirma icin BIST
    100 endeksinin hem TL (BIST:XU100) hem dolar (BIST:XU100.USD) kapanis
    fiyati da TradingView'den cekilip iki ayri sag eksende cizgi olarak
    ekleniyor. `daily_at_tr="23:00"`. Sayfasi
    `templates/bist100_rsi_breadth.html` icinde `rsi_breadth.html` ile
    ayni gorsel dil (mavi/turuncu RSI barlari sol eksen), artik iki
    endeks fiyat cizgisi (TL turkuaz, USD mor) ayri sag eksenlerde,
    hepsi lejanttan acilir/kapanir. BIST 100 uye listesi, gunluk seri
    cekme ve XU100 (TL/USD) yardimcilari `bist100_common.py`'de -
    `bist100_breadth.py` ile paylasiliyor.
  - `bist100_breadth.py` - `sp500_breadth.py`'nin BIST 100 hali: BIST 100
    hisselerinin yuzde kacinin 200 gunluk hareketli ortalamasinin uzerinde
    oldugu ("genislik/breadth"). Ham fiyat verisi TradingView'den
    (tvDatafeed) cekiliyor, ayni uye listesi ve yardimcilar
    `bist100_common.py`'den geliyor. Karsilastirma icin BIST 100
    endeksinin hem TL hem USD kapanis fiyati ayri sag eksenlerde cizgi
    olarak ekleniyor. `daily_at_tr="23:00"`. Sayfasi
    `templates/bist100_breadth.html` icinde `sp500_breadth.html` ile ayni
    gorsel dil (mavi cubuklar sol eksen 0-100), iki endeks fiyat cizgisi
    (TL turkuaz, USD mor) ayri sag eksenlerde, hepsi lejanttan
    acilir/kapanir.
  - `bist100_ma_breadth.py` - BIST 100 hisselerinin yuzde kacinin 50
    gunluk ve yuzde kacinin 200 gunluk ortalamasinin uzerinde oldugu, ayni
    grafikte iki cizgi olarak. Her hisse icin kapanis serisi tek seferde
    cekilip (`bist100_common.py`) hem 50g hem 200g ortalama ayni seriden
    hesaplaniyor - ekstra ag istegi yok. `daily_at_tr="23:00"`. Sayfasi
    `templates/bist100_ma_breadth.html` icinde tek grafik (turkuaz 50g,
    mor 200g, 0-100 eksen), lejanttan acilir/kapanir.
  - `bist100_sector_drawdown.py` - 32 BIST sektor endeksinin (BIST:XUSIN,
    BIST:XBANK, BIST:XUMAL vb. - kullanicinin verdigi ticker'lar, hepsi
    tvDatafeed ile dogrulandi) kendi o ana kadarki zirvesine gore % geri
    cekilmesi (`market_relative.py`'deki mantigin BIST sektorlerine
    uygulanmis hali). `daily_at_tr="23:00"`. Sayfasi
    `templates/bist100_sector_drawdown.html` icinde `sector_breadth.html`
    ile ayni izgara + tiklayinca buyuyen modal UX'i (32 kart, her biri tek
    cizgili bir geri cekilme grafigi), ama Z-Score paneli yok - sadece bu
    kartin ihtiyaci olan tek metrik gosteriliyor.
  - `bist100_excess_return.py` - `sp500_concentration.py`'deki 3 aylik
    excess return mantiginin BIST'e uygulanmis hali: BIST 100'un
    (BIST:XU100) 3 aylik (63 islem gunu) getirisi eksi BIST TUM'un
    (BIST:XTUMY) 3 aylik getirisi. XU100/XTUMY endeks seviyesinde
    ticker'lar oldugu icin (100 tek tek hisse degil) diger BIST
    kartlarindaki 2020-10-30 sinirlamasi burada yok - veri 2019 basindan
    itibaren gosteriliyor. Karsilastirma icin XU100'un hem TL hem USD
    kapanis fiyati da ayri eksenlerde cizgi olarak ekleniyor.
    `daily_at_tr="19:00"`. Sayfasi `templates/bist100_excess_return.html`
    icinde `sp500_concentration.html` ile benzer gorsel dil (yesil/kirmizi
    fark cubuklari sag eksen + fiyat cizgileri sol eksenler), ama 200g MA
    golgelendirmesi yok (istenmedi).
  - `bist100_bank_excess_return.py` - ayni excess return mantigi, bu
    sefer BIST Banka (BIST:XBANK) - BIST 100 (BIST:XU100): XBANK'in 3
    aylik getirisi eksi XU100'un 3 aylik getirisi. Karsilastirma icin
    XU100 (TL/USD) ve XBANK (TL) kapanis fiyatlari ayri eksenlerde cizgi
    olarak ekleniyor. Endeks seviyesinde ticker'lar oldugu icin veri 2019
    basindan itibaren. `daily_at_tr="19:00"`. Sayfasi
    `templates/bist100_bank_excess_return.html`, `bist100_excess_return.html`
    ile ayni gorsel dil, uc fiyat cizgisi (turkuaz XU100 TL, mor XU100
    USD, sari XBANK TL).
  - `enflasyon_karsilastirma.py` - piyasa verisi degil, resmi enflasyon
    istatistigi: yillik % TUFE (TUIK), KKTC TUFE, ITO Ucretliler
    Gecinme Endeksi, kullanicinin verdigi referans gorseldeki 3 seriyle
    ayni. Her kurumun kendi (belgelenmemis) veri kaynagindan cekiliyor:
    - TUIK: TCMB EVDS3'un web arayuzunun kullandigi ic servis
      (POST evds3.tcmb.gov.tr/igmevdsms-dis/fe, seri TP.GENENDEKS.T1,
      formulas=3) - tarayicida "Tablo Olustur" tiklanip ag istekleri
      izlenerek bulundu, kimlik dogrulama gerekmiyor. EVDS'in resmi API
      key gerektiren REST servisi (/service/evds/) artik sadece SPA
      kabugu donduruyor, kullanilamiyor.
    - KKTC: istatistik.gov.ct.tr'nin "Tablolar (MS EXCEL)" sayfasindaki
      guncel arsiv .xls dosyasi (dosya adi her ay degisiyor, sayfadan
      otomatik bulunuyor), xlrd ile okunuyor.
    - ITO: ististatistik.ito.org.tr'nin ic AJAX endpoint'i
      (POST view/rapor05/index.php, IndeksId=3), tum yillari tek
      istekte donduruyor. NOT: pandas.read_html "11,17" gibi virgullu
      ondalik sayilari binlik ayiraci sanip 1117'ye cevirdigi icin
      (dogrulanmis bug) tablo duz regex ile ayikliyor.
    Uc kurum da farkli tarihlerde yayimladigi icin (TUIK/KKTC ~ayin
    3-5'i, ITO ayin 1'i) sabit bir "ayin X. gunu" kurali yerine diger
    BIST kartlariyla ayni sekilde gunde 1 kez kontrol ediliyor
    (`daily_at_tr="19:00"`) - fetch() her zaman o an mevcut olan en
    guncel veriyi cektigi icin, hangi kurum ne zaman yayimlarsa
    yayimlasin bir sonraki gunluk kontrolde kart otomatik guncellenir.
    Sayfasi `templates/enflasyon_karsilastirma.html` icinde dort cizgili
    tek grafik (kirmizi TUIK, mavi KKTC, yesil ITO 1995=100, turuncu
    kesikli ITO 2023=100 - ITO'nun guncel basin bultenlerinde one cikan
    yeni endeksi, farkli metodoloji/sepet, gecmisi sadece 2024'ten
    itibaren; ikisi de gosteriliyor cunku farkli ama gecerli iki resmi
    seri), lejanttan acilir/kapanir.
  - `fx_dxy_us10y_correlation.py` - DXY (TVC:DXY, dolar endeksi) ile ABD
    10 yillik tahvil faizi (TVC:US10Y) arasindaki 30/60/90 gunluk kayan
    pencereli Pearson korelasyonu, TradingView (tvDatafeed) uzerinden.
    Korelasyon ham fiyat/faiz seviyeleri degil gunluk % getiriler
    uzerinden hesaplaniyor (trend kaynakli yaniltici korelasyonu onlemek
    icin - iki seri de uzun sureli ayni yonde surukleniyorsa ham
    seviyeler yaniltici sekilde yuksek korelasyon gosterebilir).
    `daily_at_tr="23:45"` - 23:00 degil, cunku ABD tahvil piyasasi
    kapanisi tam 23:00 TR'ye denk geliyor ve TradingView o gunun son
    gunluk barini o saatte henuz yayinlamamis olabiliyor (SP500
    kartlarindaki ayni duzeltme). Kendi grubu "FX Gostergeleri" altinda
    listeleniyor. Sayfasi `templates/fx_dxy_us10y_correlation.html`
    icinde uc cizgili tek grafik (turkuaz 30g, sari 60g, mor 90g),
    y ekseni sabit -1..+1, sifir cizgisi vurgulu.
  - `sp500_mag7_momentum_correlation.py` - Magnificent 7 (CBOE:MAGS) ile
    momentum faktoru (CBOE:MTUM) arasindaki 21 seanslik kayan pencereli
    Pearson korelasyonu, TradingView (tvDatafeed) uzerinden, gunluk %
    getiriler uzerinden hesaplanip (fx_dxy_us10y_correlation.py ile ayni
    yontem). Veri MAGS'in islem gormeye basladigi 2023 Kasim'inden
    itibaren mevcut - fetch() ikisinin ortak en erken tarihinden baslar.
    `daily_at_tr="23:45"` (ABD borsa kapanisi + tampon, ayni gerekce).
    Kendi grubu "SP500 Korelasyonlar" altinda listeleniyor. Sayfasi
    `templates/sp500_mag7_momentum_correlation.html` icinde tek dolgulu
    (filled area) cizgi grafik, y ekseni sabit -1..+1, sifir cizgisi
    vurgulu.
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
