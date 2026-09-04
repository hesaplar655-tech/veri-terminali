"""
Magnificent 7 (CBOE:MAGS - Roundhill Magnificent Seven ETF) ile momentum
faktoru (CBOE:MTUM - iShares MSCI USA Momentum Factor ETF) arasindaki
21 seans (gunluk islem gunu) rolling Pearson korelasyonu.

Korelasyon, iki serinin GUNLUK YUZDE DEGISIMLERI (getirileri) uzerinden
hesaplaniyor - ham fiyat seviyeleri uzerinden degil (bkz.
fx_dxy_us10y_correlation.py'deki ayni rasyonel: trend kaynakli
yaniltici korelasyonu onlemek icin).

Deger +1 = MAGS ve MTUM gunluk hareketleri tam ayni yonde, -1 = tam ters
yonde, 0 = iliski yok. MAGS ETF'i 2023 Nisan'inda islem gormeye
basladigi icin veri o tarihten itibaren mevcut - fetch() ikisinin ortak
en erken tarihinden baslar (n_bars yeterince buyuk tutularak tum tarihce
cekiliyor).

Veri kaynagi: TradingView, tvDatafeed (kimlik dogrulama gerektirmeden).

TR saatiyle gunde 1 kez (23:45) calisir - 23:00 yerine 23:45 kullaniliyor
cunku ABD borsasi kapanisi tam 23:00 TR'ye denk geliyor ve TradingView o
gunun son gunluk barini o saatte henuz yayinlamamis olabiliyor (bkz.
rsi_breadth.py ve diger SP500 kartlarindaki ayni duzeltme).
"""
from datetime import timezone, timedelta

from tvDatafeed import TvDatafeed, Interval

TR_TZ = timezone(timedelta(hours=3))
N_BARS = 3000  # MAGS'in tum islem gecmisini kapsamasi icin bol tampon
PENCERE = 21  # seans (gunluk islem gunu)


def _fetch_daily_closes(tv, symbol, exchange):
    df = tv.get_hist(symbol=symbol, exchange=exchange, interval=Interval.in_daily, n_bars=N_BARS)
    if df is None or df.empty:
        return {}
    out = {}
    for ts, row in df.iterrows():
        d = ts.tz_localize("UTC").astimezone(TR_TZ).strftime("%Y-%m-%d") if ts.tzinfo is None else ts.astimezone(TR_TZ).strftime("%Y-%m-%d")
        out[d] = float(row["close"])
    return out


def _gunluk_getiri(kapanislar, tarihler):
    """Sirali tarih listesine karsilik gelen gunluk % degisim listesi (ilk deger None)."""
    getiriler = [None]
    for i in range(1, len(tarihler)):
        onceki, simdi = kapanislar[tarihler[i - 1]], kapanislar[tarihler[i]]
        getiriler.append((simdi / onceki - 1) * 100 if onceki else None)
    return getiriler


def _pearson(x, y):
    n = len(x)
    if n < 2:
        return None
    ort_x = sum(x) / n
    ort_y = sum(y) / n
    kov = sum((a - ort_x) * (b - ort_y) for a, b in zip(x, y))
    var_x = sum((a - ort_x) ** 2 for a in x)
    var_y = sum((b - ort_y) ** 2 for b in y)
    if var_x == 0 or var_y == 0:
        return None
    return kov / (var_x ** 0.5 * var_y ** 0.5)


def fetch():
    tv = TvDatafeed()
    mags = _fetch_daily_closes(tv, "MAGS", "CBOE")
    mtum = _fetch_daily_closes(tv, "MTUM", "CBOE")

    ortak_tarihler = sorted(set(mags) & set(mtum))
    if len(ortak_tarihler) < PENCERE + 5:
        return []

    mags_getiri = _gunluk_getiri(mags, ortak_tarihler)
    mtum_getiri = _gunluk_getiri(mtum, ortak_tarihler)

    events = []
    for i, tarih in enumerate(ortak_tarihler):
        if i == 0:
            continue  # ilk gunun getirisi yok
        event = {
            "tarih": tarih,
            "mags_kapanis": round(mags[tarih], 3),
            "mtum_kapanis": round(mtum[tarih], 3),
        }
        if i >= PENCERE:  # pencere ilk (getirisi olmayan) gune tasmasin
            x = mags_getiri[i + 1 - PENCERE:i + 1]
            y = mtum_getiri[i + 1 - PENCERE:i + 1]
            korelasyon = _pearson(x, y)
            if korelasyon is not None:
                event["korelasyon_21s"] = round(korelasyon, 3)
        events.append(event)

    return events
