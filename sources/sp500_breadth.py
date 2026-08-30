"""
S&P 500 (SPCFD:SPX) fiyati ile S5TH (INDEX:S5TH - S&P 500 hisselerinin
200 gunluk ortalamasinin uzerinde olan yuzdesi, "breadth/genislik" gostergesi)
- Fidelity'nin "Late 1990's vs Current Cycle" grafiginin "Current Cycle"
panelindeki mantik.

Veri kaynagi: TradingView, `tvDatafeed` kutuphanesi araciligiyla (kimlik
dogrulama gerektirmeden, sitenin kendi ticker/borsa adlandirmasiyla -
SPCFD:SPX, INDEX:S5TH).

Grafik 2019-01-01'den itibaren gosteriliyor (kullanicinin istegi); her iki
ticker da TradingView'da 2018 sonuna kadar veri verdigi icin bu tarihte bir
kaynak sinirlamasi yok.
"""
from datetime import timezone, timedelta

from tvDatafeed import TvDatafeed, Interval

TR_TZ = timezone(timedelta(hours=3))

START_DATE = "2019-01-01"
N_BARS = 2200  # 2019 basindan bugune + tampon


def _fetch_daily(tv, symbol, exchange):
    df = tv.get_hist(symbol=symbol, exchange=exchange, interval=Interval.in_daily, n_bars=N_BARS)
    out = {}
    for ts, row in df.iterrows():
        d = ts.tz_localize("UTC").astimezone(TR_TZ).strftime("%Y-%m-%d") if ts.tzinfo is None else ts.astimezone(TR_TZ).strftime("%Y-%m-%d")
        out[d] = float(row["close"])
    return out


def fetch():
    tv = TvDatafeed()
    spx = _fetch_daily(tv, "SPX", "SPCFD")
    s5th = _fetch_daily(tv, "S5TH", "INDEX")

    dates = sorted(set(spx.keys()) & set(s5th.keys()))
    dates = [d for d in dates if d >= START_DATE]

    events = []
    for d in dates:
        events.append({
            "tarih": d,
            "spx_kapanis": round(spx[d], 2),
            "s5th_yuzde": round(s5th[d], 2),
        })

    return events
