"""
DXY (TVC:DXY - dolar endeksi) ile ABD 2 yillik tahvil faizi (TVC:US02Y)
arasindaki 30/60/90 gunluk rolling (kayan pencereli) Pearson korelasyonu.

Korelasyon, iki serinin GUNLUK YUZDE DEGISIMLERI (getirileri) uzerinden
hesaplaniyor - ham fiyat/getiri seviyeleri uzerinden degil. Bunun nedeni:
iki trend halindeki seri (orn. ikisi de uzun sureli yukselirken) ham
seviyeler uzerinden hesaplanan korelasyon yaniltici sekilde yuksek
cikabilir (spurious correlation); gunluk getiriler uzerinden hesaplamak
gercek eszamanli hareket iliskisini yansitir - piyasa analizinde
standart yontem budur (bkz. fx_dxy_us10y_correlation.py ile ayni yontem).

Deger 0 = gunluk hareketler arasinda iliski yok, +1 = DXY yukselirken
US02Y faizi de her zaman yukseliyor (tam pozitif iliski), -1 = DXY
yukselirken US02Y her zaman dusuyor (tam negatif/ters iliski). 2 yillik
faiz, 10 yillik faizden farkli olarak Fed politika beklentilerine (kisa
vadeli faiz kararlarina) daha duyarlidir - bu yuzden ayri bir kart.

Veri kaynagi: TradingView, tvDatafeed (kimlik dogrulama gerektirmeden).

TR saatiyle gunde 1 kez (23:45) calisir - 23:00 yerine 23:45 kullaniliyor
cunku ABD borsa/tahvil piyasasi kapanisi tam 23:00 TR'ye denk geliyor ve
TradingView o gunun son gunluk barini o saatte henuz yayinlamamis
olabiliyor (bkz. rsi_breadth.py ve sp500 kartlarindaki ayni duzeltme).
"""
from datetime import timezone, timedelta

from tvDatafeed import TvDatafeed, Interval

TR_TZ = timezone(timedelta(hours=3))
N_BARS = 1500  # birkac yillik gunluk veri + korelasyon pencereleri icin tampon
PENCERELER = (30, 60, 90)


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
    dxy = _fetch_daily_closes(tv, "DXY", "TVC")
    us02y = _fetch_daily_closes(tv, "US02Y", "TVC")

    ortak_tarihler = sorted(set(dxy) & set(us02y))
    if len(ortak_tarihler) < max(PENCERELER) + 5:
        return []

    dxy_getiri = _gunluk_getiri(dxy, ortak_tarihler)
    us02y_getiri = _gunluk_getiri(us02y, ortak_tarihler)

    events = []
    for i, tarih in enumerate(ortak_tarihler):
        if i == 0:
            continue  # ilk gunun getirisi yok
        event = {
            "tarih": tarih,
            "dxy_kapanis": round(dxy[tarih], 3),
            "us02y_kapanis": round(us02y[tarih], 3),
        }
        for pencere in PENCERELER:
            if i < pencere:  # pencere ilk (getirisi olmayan) gune tasmasin
                continue
            x = dxy_getiri[i + 1 - pencere:i + 1]
            y = us02y_getiri[i + 1 - pencere:i + 1]
            korelasyon = _pearson(x, y)
            if korelasyon is not None:
                event[f"korelasyon_{pencere}g"] = round(korelasyon, 3)
        events.append(event)

    return events
