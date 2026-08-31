"""
3M Excess Return: BIST 100 (BIST:XU100) - BIST TUM (BIST:XTUMY).

3M Excess Return = XU100'un son 3 aylik (63 islem gunu) getirisi
                    - XTUMY'nin son 3 aylik getirisi
sp500_concentration.py'deki mantigin BIST'e uygulanmis hali - mutlak bir
getiri degil, BIST 100'un (buyuk/likit sirketler) BIST TUM'a (butun
piyasa) gore performans farki:
- Pozitifse: BIST 100 genel piyasayi geride birakiyor (buyuk sirketler
  one cikiyor).
- Negatifse: genel piyasa (kucuk/orta olcekli sirketler dahil) BIST
  100'den daha iyi performans gosteriyor.

Karsilastirma icin BIST 100 endeksinin hem TL (BIST:XU100) hem dolar
(BIST:XU100.USD) kapanis fiyati da ayri eksenlerde cizgi olarak
ekleniyor.

Veri kaynagi: TradingView, tvDatafeed. XU100/XTUMY endeks seviyesinde
ticker'lar oldugu icin (BIST 100'un 100 tek tek hissesi degil) uzun
gecmisi guvenilir bir sekilde cekilebiliyor - diger BIST kartlarindaki
2020-10-30 sinirlamasi burada gecerli degil, veri 2019 basindan itibaren
gosteriliyor.

TR saatiyle gunde 1 kez (23:00) calisir.
"""
from datetime import timezone, timedelta

from tvDatafeed import TvDatafeed, Interval

TR_TZ = timezone(timedelta(hours=3))
RETURN_WINDOW = 63  # ~3 ay (21 islem gunu/ay * 3)
N_BARS = 2200  # 2019 basindan itibaren gosterebilmek icin (+63g getiri tamponu)
START_DATE = "2019-01-01"


def _fetch_daily_closes(tv, symbol):
    df = tv.get_hist(symbol=symbol, exchange="BIST", interval=Interval.in_daily, n_bars=N_BARS)
    out = {}
    for ts, row in df.iterrows():
        date = ts.tz_localize("UTC").astimezone(TR_TZ).strftime("%Y-%m-%d") if ts.tzinfo is None else ts.astimezone(TR_TZ).strftime("%Y-%m-%d")
        out[date] = float(row["close"])
    return out


def fetch():
    tv = TvDatafeed()
    xu100_try = _fetch_daily_closes(tv, "XU100")
    xu100_usd = _fetch_daily_closes(tv, "XU100.USD")
    xtumy = _fetch_daily_closes(tv, "XTUMY")

    xu100_dates = sorted(xu100_try.keys())
    xtumy_dates = sorted(xtumy.keys())

    events = []
    for i, date in enumerate(xu100_dates):
        if i < RETURN_WINDOW or date < START_DATE or date not in xtumy:
            continue
        xtumy_idx = xtumy_dates.index(date)
        if xtumy_idx < RETURN_WINDOW:
            continue

        xu100_now, xu100_then = xu100_try[date], xu100_try[xu100_dates[i - RETURN_WINDOW]]
        xtumy_now, xtumy_then = xtumy[date], xtumy[xtumy_dates[xtumy_idx - RETURN_WINDOW]]

        xu100_return = (xu100_now / xu100_then - 1) * 100
        xtumy_return = (xtumy_now / xtumy_then - 1) * 100

        event = {
            "tarih": date,
            "xu100_try": round(xu100_now, 2),
            "3ay_fark_yuzde": round(xu100_return - xtumy_return, 2),
        }
        if date in xu100_usd:
            event["xu100_usd"] = round(xu100_usd[date], 3)
        events.append(event)

    return events
