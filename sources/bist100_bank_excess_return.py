"""
3M Excess Return: BIST Banka (BIST:XBANK) - BIST 100 (BIST:XU100).

3M Excess Return = XBANK'in son 3 aylik (63 islem gunu) getirisi
                    - XU100'un son 3 aylik getirisi
bist100_excess_return.py'deki mantigin ayni, ama bu sefer BIST 100'un
kendisi (XU100 - genel piyasa) baseline, BIST Banka (XBANK) ise
karsilastirilan taraf:
- Pozitifse: banka hisseleri genel piyasayi geride birakiyor.
- Negatifse: genel piyasa banka hisselerinden daha iyi performans
  gosteriyor.

Karsilastirma icin BIST 100 endeksinin hem TL (BIST:XU100) hem dolar
(BIST:XU100.USD) kapanis fiyati, ve BIST Banka endeksinin (BIST:XBANK)
TL kapanis fiyati da ayri eksenlerde cizgi olarak ekleniyor.

Veri kaynagi: TradingView, tvDatafeed. XU100/XBANK endeks seviyesinde
ticker'lar oldugu icin (BIST 100'un 100 tek tek hissesi degil) uzun
gecmisi guvenilir bir sekilde cekilebiliyor - diger BIST kartlarindaki
2020-10-30 sinirlamasi burada gecerli degil, veri 2019 basindan itibaren
gosteriliyor.

TR saatiyle gunde 1 kez (19:00) calisir.
"""
from datetime import timezone, timedelta

from tvDatafeed import TvDatafeed, Interval

TR_TZ = timezone(timedelta(hours=3))
RETURN_WINDOW = 63  # ~3 ay (21 islem gunu/ay * 3)
N_BARS = 2200  # 2019 basindan itibaren gosterebilmek icin (+63g getiri tamponu)
START_DATE = "2019-01-01"


def _fetch_daily_closes(tv, symbol):
    df = tv.get_hist(symbol=symbol, exchange="BIST", interval=Interval.in_daily, n_bars=N_BARS)
    if df is None or df.empty:
        return {}
    out = {}
    for ts, row in df.iterrows():
        date = ts.tz_localize("UTC").astimezone(TR_TZ).strftime("%Y-%m-%d") if ts.tzinfo is None else ts.astimezone(TR_TZ).strftime("%Y-%m-%d")
        out[date] = float(row["close"])
    return out


def fetch():
    tv = TvDatafeed()
    xu100_try = _fetch_daily_closes(tv, "XU100")
    xu100_usd = _fetch_daily_closes(tv, "XU100.USD")
    xbank_try = _fetch_daily_closes(tv, "XBANK")

    xu100_dates = sorted(xu100_try.keys())
    xbank_dates = sorted(xbank_try.keys())

    events = []
    for i, date in enumerate(xu100_dates):
        if i < RETURN_WINDOW or date < START_DATE or date not in xbank_try:
            continue
        xbank_idx = xbank_dates.index(date)
        if xbank_idx < RETURN_WINDOW:
            continue

        xu100_now, xu100_then = xu100_try[date], xu100_try[xu100_dates[i - RETURN_WINDOW]]
        xbank_now, xbank_then = xbank_try[date], xbank_try[xbank_dates[xbank_idx - RETURN_WINDOW]]

        xu100_return = (xu100_now / xu100_then - 1) * 100
        xbank_return = (xbank_now / xbank_then - 1) * 100

        event = {
            "tarih": date,
            "xu100_try": round(xu100_now, 2),
            "xbank_try": round(xbank_now, 2),
            "3ay_fark_yuzde": round(xbank_return - xu100_return, 2),
        }
        if date in xu100_usd:
            event["xu100_usd"] = round(xu100_usd[date], 3)
        events.append(event)

    return events
