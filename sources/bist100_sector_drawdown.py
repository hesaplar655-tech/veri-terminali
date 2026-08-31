"""
BIST 100 icindeki 32 sektor endeksinin (BIST:XUSIN, BIST:XBANK vb.) kendi
o ana kadarki zirvesine (rolling peak) gore % geri cekilme (drawdown)
gostergesi - market_relative.py'deki mantigin BIST sektorlerine uygulanmis
hali (deger 0 = yeni zirve, negatif = zirveden ne kadar asagida).
Karsilastirma icin BIST 100'un kendisi de (hem TL BIST:XU100 hem dolar
BIST:XU100.USD) ayni izgarada birer kart olarak ekleniyor.

Ticker'lar kullanicinin verdigi TradingView sektor endeksi kodlari,
hepsinin basina "BIST:" ekleniyor (orn. BIST:XBANK). Hepsi tvDatafeed ile
dogrulandi.

START_DATE (bist100_common.py, su an 2020-10-30): diger BIST kartlariyla
tutarli olsun diye ayni tarih kullanildi. Zirve hesaplamasi START_DATE'ten
once cekilen veriyi de kapsiyor (N_BARS genis bir pencere), boylece
gosterilen ilk gunlerde de gercek yakin donem zirvesine gore dogru bir
geri cekilme degeri var - sadece goruntulenen aralik START_DATE'ten
baslatiliyor.

Her sektor icin ayri bir grafik karti (izgara + tiklayinca buyuyen modal),
sector_breadth.html ile ayni UX. TR saatiyle gunde 1 kez (23:00) calisir.
"""
from datetime import timezone, timedelta

from tvDatafeed import TvDatafeed, Interval

from sources.bist100_common import START_DATE

TR_TZ = timezone(timedelta(hours=3))
N_BARS = 2200  # genis bir gecmis penceresi, zirve hesaplamasi icin

SECTORS = [
    {"key": "xu100_try", "title": "BIST 100 (XU100, TL)", "sembol": "XU100"},
    {"key": "xu100_usd", "title": "BIST 100 (XU100, USD)", "sembol": "XU100.USD"},
    {"key": "xusin", "title": "BIST Sinai", "sembol": "XUSIN"},
    {"key": "xuhiz", "title": "BIST Hizmetler", "sembol": "XUHIZ"},
    {"key": "xumal", "title": "BIST Mali", "sembol": "XUMAL"},
    {"key": "xutek", "title": "BIST Teknoloji", "sembol": "XUTEK"},
    {"key": "xbank", "title": "BIST Banka", "sembol": "XBANK"},
    {"key": "xakur", "title": "BIST Araci Kurumlar", "sembol": "XAKUR"},
    {"key": "xblsm", "title": "BIST Bilisim", "sembol": "XBLSM"},
    {"key": "xelkt", "title": "BIST Elektrik", "sembol": "XELKT"},
    {"key": "xfink", "title": "BIST Fin. Kir. Faktoring", "sembol": "XFINK"},
    {"key": "xgmyo", "title": "BIST Gayrimenkul Y.O.", "sembol": "XGMYO"},
    {"key": "xgida", "title": "BIST Gida Icecek", "sembol": "XGIDA"},
    {"key": "xgsyo", "title": "BIST Girisim Sermayesi Y.O.", "sembol": "XGSYO"},
    {"key": "xhold", "title": "BIST Holding ve Yatirim", "sembol": "XHOLD"},
    {"key": "xiltm", "title": "BIST Iletisim", "sembol": "XILTM"},
    {"key": "xinsa", "title": "BIST Insaat", "sembol": "XINSA"},
    {"key": "xkmya", "title": "BIST Kimya Petrol Plastik", "sembol": "XKMYA"},
    {"key": "xknkl", "title": "BIST Konaklama", "sembol": "XKNKL"},
    {"key": "xmadn", "title": "BIST Madencilik", "sembol": "XMADN"},
    {"key": "xyort", "title": "BIST Menkul Kiym. Y.O.", "sembol": "XYORT"},
    {"key": "xmana", "title": "BIST Metal Ana", "sembol": "XMANA"},
    {"key": "xmesy", "title": "BIST Metal Esya Makina", "sembol": "XMESY"},
    {"key": "xkagt", "title": "BIST Orman Kagit Basim", "sembol": "XKAGT"},
    {"key": "xptic", "title": "BIST Perakende Ticaret", "sembol": "XPTIC"},
    {"key": "xsgrt", "title": "BIST Sigorta", "sembol": "XSGRT"},
    {"key": "xspor", "title": "BIST Spor", "sembol": "XSPOR"},
    {"key": "xtast", "title": "BIST Tas Toprak", "sembol": "XTAST"},
    {"key": "xteks", "title": "BIST Tekstil Deri", "sembol": "XTEKS"},
    {"key": "xtcrt", "title": "BIST Ticaret", "sembol": "XTCRT"},
    {"key": "xttic", "title": "BIST Toptan Ticaret", "sembol": "XTTIC"},
    {"key": "xtrzm", "title": "BIST Turizm", "sembol": "XTRZM"},
    {"key": "xulas", "title": "BIST Ulastirma", "sembol": "XULAS"},
    {"key": "xyihz", "title": "BIST Yiyecek ve Icecek Hizmetleri", "sembol": "XYIHZ"},
]


def _gunluk_kapanis(tv, sembol):
    df = tv.get_hist(symbol=sembol, exchange="BIST", interval=Interval.in_daily, n_bars=N_BARS)
    if df is None or df.empty:
        return None
    out = {}
    for ts, row in df.iterrows():
        d = ts.tz_localize("UTC").astimezone(TR_TZ).strftime("%Y-%m-%d") if ts.tzinfo is None else ts.astimezone(TR_TZ).strftime("%Y-%m-%d")
        out[d] = float(row["close"])
    return out


def fetch():
    tv = TvDatafeed()
    sonuc = {}

    for sektor in SECTORS:
        try:
            kapanislar = _gunluk_kapanis(tv, sektor["sembol"])
        except Exception:
            continue  # bir sektor basarisiz olursa digerlerini etkilemesin
        if not kapanislar:
            continue

        tarihler = sorted(kapanislar.keys())
        seri = []
        zirve = float("-inf")
        for tarih in tarihler:
            fiyat = kapanislar[tarih]
            zirve = max(zirve, fiyat)
            if tarih < START_DATE:
                continue
            seri.append({
                "tarih": tarih,
                "kapanis": round(fiyat, 2),
                "drawdown_yuzde": round((fiyat / zirve - 1) * 100, 3),
            })

        if seri:
            sonuc[sektor["key"]] = {
                "title": sektor["title"],
                "ticker": f"BIST:{sektor['sembol']}",
                "seri": seri,
            }

    return sonuc
