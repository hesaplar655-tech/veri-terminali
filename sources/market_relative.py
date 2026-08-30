"""
S&P 500 (SPCFD:SPX), Nasdaq (CFI:US100) ve S&P 500 Esit Agirlikli (AMEX:RSP)
icin saatlik veriyi TradingView'den ceker ve her birini kendi o ana kadarki
zirvesine (rolling all-time-high) gore % geri cekilme (drawdown) olarak
gosterir - referans gorseldeki "Dow/S&P 500/Nasdaq" grafiginin ayni mantigi
(deger 0 = yeni zirve, negatif = zirveden ne kadar asagida). Burada Dow
yerine RSP kullaniliyor, kullanicinin verdigi ticker'lara gore.

Veri kaynagi: TradingView, `tvDatafeed` kutuphanesi araciligiyla (kimlik
dogrulama gerektirmeden).

Onemli sinirlama: uc ticker'in nologin erisimde saatlik veri gecmisi farkli -
CFI:US100 en kisasi (~Ocak 2025'e kadar), SPCFD:SPX ve AMEX:RSP daha eskiye
(Ocak 2023) gidebiliyor. Grafik ucunun ortak baslangic noktasi olan CFI:US100
ile sinirli - bu bir kod kisitlamasi degil, kaynagin dogal siniri.

Saatlik bar zaman damgalari ticker'lar arasinda farkli dakikalarda
hizalaniyor (orn. :01 vs :30), o yuzden eslestirme saat-bucket'ina
(YYYY-MM-DD HH:00) yuvarlanarak yapiliyor.
"""
from datetime import timezone, timedelta

from tvDatafeed import TvDatafeed, Interval

TR_TZ = timezone(timedelta(hours=3))
N_BARS = 20000  # nologin erisimde ulasilabilecek maksimuma yakin bir tampon


def _fetch_hourly(tv, symbol, exchange):
    df = tv.get_hist(symbol=symbol, exchange=exchange, interval=Interval.in_1_hour, n_bars=N_BARS)
    out = {}
    for ts, row in df.iterrows():
        ts_tr = ts.tz_localize("UTC").astimezone(TR_TZ) if ts.tzinfo is None else ts.astimezone(TR_TZ)
        bucket = ts_tr.strftime("%Y-%m-%d %H:00")
        out[bucket] = float(row["close"])  # ayni saat icinde birden fazla bar varsa sonuncusu kalir
    return out


def fetch():
    tv = TvDatafeed()
    spx = _fetch_hourly(tv, "SPX", "SPCFD")
    us100 = _fetch_hourly(tv, "US100", "CFI")
    rsp = _fetch_hourly(tv, "RSP", "AMEX")

    ortak_saatler = sorted(set(spx.keys()) & set(us100.keys()) & set(rsp.keys()))
    if not ortak_saatler:
        return []

    events = []
    spx_zirve = us100_zirve = rsp_zirve = float("-inf")
    for saat in ortak_saatler:
        spx_zirve = max(spx_zirve, spx[saat])
        us100_zirve = max(us100_zirve, us100[saat])
        rsp_zirve = max(rsp_zirve, rsp[saat])
        events.append({
            "zaman": saat,
            "spx_yuzde": round((spx[saat] / spx_zirve - 1) * 100, 3),
            "us100_yuzde": round((us100[saat] / us100_zirve - 1) * 100, 3),
            "rsp_yuzde": round((rsp[saat] / rsp_zirve - 1) * 100, 3),
        })

    return events
