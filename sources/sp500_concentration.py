"""
S&P 500 (AMEX:SPY, piyasa degeri agirlikli - fiyat grafigi + 200 gunluk
ortalama icin) ile S&P 500 Esit Agirlikli Endeks (AMEX:RSP) ve Magnificent 7
(CBOE:MAGS) arasindaki 3 aylik getiri farki ("3M Excess Return: SPW - MAG7").

3M Excess Return = SPW'nin (S&P 500 Esit Agirlikli) son 3 aylik getirisi
                    - MAG7'nin (Magnificent 7) son 3 aylik getirisi
Bu, mutlak bir getiri degil, iki grubun BIRBIRINE gore performans farkidir:
- Pozitifse: "ortalama" S&P 500 hissesi (esit agirlikli) Mag7'yi geride
  birakiyor (breadth/genislik iyilesiyor).
- Negatifse: Mag7 piyasayi (esit agirlikli bazda) domine ediyor.

Fiyat grafigindeki cizgi ve arka plandaki 200-gunluk-ortalama golgelendirmesi
ise standart (piyasa degeri agirlikli) S&P 500 (SPY) uzerinden - bu ayri bir
gosterge, excess return hesabina girmiyor.

Veri kaynagi: TradingView, `tvDatafeed` kutuphanesi araciligiyla (TradingView'in
grafik websocket protokolunu kullanir, ayni sitenin kendi ticker/borsa
adlandirmasiyla - AMEX:SPY, AMEX:RSP, CBOE:MAGS - kimlik dogrulama gerektirmeden).

Onemli sinirlama: CBOE:MAGS (Roundhill Magnificent Seven ETF) islem gormeye
Nisan 2023'te basladi, ve nologin erisimde TradingView veriyi ~Kasim 2023'ten
itibaren veriyor. Bu yuzden grafik (ekteki Fidelity gorselinin aksine) 2018'e
degil, ~Aralik 2023'e kadar geri gidebiliyor - bu bir kod kisitlamasi degil,
kaynagin (TradingView nologin + MAGS'in kendi islem gecmisi) dogal siniridir.
"""
from datetime import timezone, timedelta

from tvDatafeed import TvDatafeed, Interval

TR_TZ = timezone(timedelta(hours=3))

MA_WINDOW = 200
RETURN_WINDOW = 63  # ~3 ay (21 islem gunu/ay * 3)
N_BARS = 1500  # MAGS + 200 gunluk MA + 63 gunluk getiri icin yeterli tampon


def _fetch_daily_closes(tv, symbol, exchange):
    df = tv.get_hist(symbol=symbol, exchange=exchange, interval=Interval.in_daily, n_bars=N_BARS)
    out = {}
    for ts, row in df.iterrows():
        date = ts.tz_localize("UTC").astimezone(TR_TZ).strftime("%Y-%m-%d") if ts.tzinfo is None else ts.astimezone(TR_TZ).strftime("%Y-%m-%d")
        out[date] = float(row["close"])
    return out


def fetch():
    tv = TvDatafeed()
    spy = _fetch_daily_closes(tv, "SPY", "AMEX")   # fiyat grafigi + 200g ortalama icin
    spw = _fetch_daily_closes(tv, "RSP", "AMEX")   # S&P 500 Esit Agirlikli
    mags = _fetch_daily_closes(tv, "MAGS", "CBOE")  # Magnificent 7

    spy_dates = sorted(spy.keys())
    spw_dates = sorted(spw.keys())

    # 200 gunluk hareketli ortalama (SPY, piyasa degeri agirlikli fiyat grafigi icin)
    ma200 = {}
    closes_window = []
    for date in spy_dates:
        closes_window.append(spy[date])
        if len(closes_window) > MA_WINDOW:
            closes_window.pop(0)
        if len(closes_window) == MA_WINDOW:
            ma200[date] = sum(closes_window) / MA_WINDOW

    # 3 aylik (63 islem gunu) getiri farki: SPW (esit agirlikli) - MAG7
    mags_dates = sorted(mags.keys())
    events = []
    for i, date in enumerate(mags_dates):
        if i < RETURN_WINDOW or date not in spy or date not in spw:
            continue
        if date not in ma200:
            continue
        spw_idx = spw_dates.index(date)
        if spw_idx < RETURN_WINDOW:
            continue

        spw_now, spw_then = spw[date], spw[spw_dates[spw_idx - RETURN_WINDOW]]
        mags_now, mags_then = mags[date], mags[mags_dates[i - RETURN_WINDOW]]

        spw_return = (spw_now / spw_then - 1) * 100
        mags_return = (mags_now / mags_then - 1) * 100
        pct_above_ma200 = (spy[date] / ma200[date] - 1) * 100

        events.append({
            "tarih": date,
            "spy_kapanis": round(spy[date], 2),
            "spw_kapanis": round(spw[date], 2),
            "mags_kapanis": round(mags[date], 2),
            "ma200_uzerinde_yuzde": round(pct_above_ma200, 2),
            "3ay_fark_yuzde": round(spw_return - mags_return, 2),
        })

    return events
