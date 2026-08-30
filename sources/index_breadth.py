"""
S&P 500, Nasdaq Composite ve Russell 2000 icin "% uyelerin 50 gunluk /
200 gunluk hareketli ortalamanin uzerinde oldugu" (breadth) verisi,
TradingView'den.

Ticker'lar - kullanicinin verdigi S&P 500 (INDEX:S5FI, INDEX:S5TH) disindakiler
TradingView'in sembol arama API'sinden (symbol-search.tradingview.com,
Barchart kaynakli) bulundu ve tvDatafeed ile dogrulandi:
  S&P 500:          50g INDEX:S5FI | 200g INDEX:S5TH
  Nasdaq Composite:  50g INDEX:NCFI | 200g INDEX:NCTH
  Russell 2000:      50g INDEX:R2FI | 200g INDEX:R2TH

Bu ticker'lar TradingView'in resmi/belgelenmis bir public API'si degil -
sembol arama sonuclarindan tespit edildi. Ileride kaldirilir/degisirse
fetch() hata verir, scheduler loglarinda gorunur.
"""
from datetime import timezone, timedelta

from tvDatafeed import TvDatafeed, Interval

TR_TZ = timezone(timedelta(hours=3))
N_BARS = 2000  # birkaç yillik gunluk veri icin tampon

TICKERS = {
    "50g": {"spx": "S5FI", "nasdaq": "NCFI", "russell": "R2FI"},
    "200g": {"spx": "S5TH", "nasdaq": "NCTH", "russell": "R2TH"},
}


def _fetch_close(tv, symbol):
    df = tv.get_hist(symbol=symbol, exchange="INDEX", interval=Interval.in_daily, n_bars=N_BARS)
    out = {}
    for ts, row in df.iterrows():
        ts_tr = ts.tz_localize("UTC").astimezone(TR_TZ) if ts.tzinfo is None else ts.astimezone(TR_TZ)
        out[ts_tr.strftime("%Y-%m-%d")] = float(row["close"])
    return out


def fetch():
    tv = TvDatafeed()
    veri = {}
    for pencere, semboller in TICKERS.items():
        seriler = {ad: _fetch_close(tv, sym) for ad, sym in semboller.items()}
        ortak_tarihler = sorted(set.intersection(*(set(s.keys()) for s in seriler.values())))
        veri[pencere] = [
            {
                "tarih": tarih,
                "spx": round(seriler["spx"][tarih], 2),
                "nasdaq": round(seriler["nasdaq"][tarih], 2),
                "russell": round(seriler["russell"][tarih], 2),
            }
            for tarih in ortak_tarihler
        ]
    return veri
