"""
S&P 500 ve 11 GICS sektor ETF'i (State Street Select Sector SPDR'lar) icin
gunluk mum verisi + o sektordeki hisselerin yuzde kaci 20 gunluk ortalamanin
uzerinde (breadth gostergesi), TradingView'den.

Fiyat (mum grafik) ticker'lari - kullanicinin verdigi:
  S&P 500: SPCFD:SPX (onceki kartlarda kullanilan)
  Consumer Discretionary: AMEX:XLY | Consumer Staples: AMEX:XLP
  Energy: AMEX:XLE | Financials: AMEX:XLF | Health Care: AMEX:XLV
  Industrials: AMEX:XLI | Information Technology: AMEX:XLK
  Materials: AMEX:XLB | Real Estate: AMEX:XLRE
  Communication Services: AMEX:XLC | Utilities: AMEX:XLU

"% 20 gunluk ortalama uzerinde" (breadth) ticker'lari - TradingView'in kendi
sembol arama API'sinden (symbol-search.tradingview.com) bulundu. Barchart
kaynakli INDEX ticker'lari, S&P 500'un tamami icin zaten INDEX:S5TW ("S&P 500
Stocks Above 20-Day Average") var oldugu bilindigi icin, sektor bazinda
esdegerlerini "<sektor adi> Stocks Above 20-Day" gibi sorgularla arayip
teker teker dogruladik (tvDatafeed ile gercek veri cekilerek):
  S&P 500: INDEX:S5TW
  Consumer Discretionary: INDEX:SYTW | Consumer Staples: INDEX:SPTW
  Energy: INDEX:SETW | Financials: INDEX:SFTW | Health Care: INDEX:SVTW
  Industrials: INDEX:SITW | Information Technology: INDEX:SKTW
  Materials: INDEX:SBTW | Real Estate: INDEX:SSTW
  Communication Services: INDEX:SLTW (eski adiyla "Telecom Services")
  Utilities: INDEX:SUTW

Not: Bu ticker'lar TradingView'in resmi/belgelenmis bir API'si degil,
sembol arama sonuclarindan tespit edildi - ileride kaynak tarafinda
degisirse (sembol kaldirilir/yeniden adlandirilirsa) fetch() o sektor icin
hata verip loglar, digerlerini etkilemez.
"""
from datetime import timezone, timedelta

from tvDatafeed import TvDatafeed, Interval

TR_TZ = timezone(timedelta(hours=3))
N_BARS = 700  # ~2.5 yillik gunluk veri icin tampon

SECTORS = [
    {"key": "spx", "title": "S&P 500", "fiyat": ("SPX", "SPCFD"), "genislik": ("S5TW", "INDEX")},
    {"key": "xly", "title": "Consumer Discretionary", "fiyat": ("XLY", "AMEX"), "genislik": ("SYTW", "INDEX")},
    {"key": "xlp", "title": "Consumer Staples", "fiyat": ("XLP", "AMEX"), "genislik": ("SPTW", "INDEX")},
    {"key": "xle", "title": "Energy", "fiyat": ("XLE", "AMEX"), "genislik": ("SETW", "INDEX")},
    {"key": "xlf", "title": "Financials", "fiyat": ("XLF", "AMEX"), "genislik": ("SFTW", "INDEX")},
    {"key": "xlv", "title": "Health Care", "fiyat": ("XLV", "AMEX"), "genislik": ("SVTW", "INDEX")},
    {"key": "xli", "title": "Industrials", "fiyat": ("XLI", "AMEX"), "genislik": ("SITW", "INDEX")},
    {"key": "xlk", "title": "Information Technology", "fiyat": ("XLK", "AMEX"), "genislik": ("SKTW", "INDEX")},
    {"key": "xlb", "title": "Materials", "fiyat": ("XLB", "AMEX"), "genislik": ("SBTW", "INDEX")},
    {"key": "xlre", "title": "Real Estate", "fiyat": ("XLRE", "AMEX"), "genislik": ("SSTW", "INDEX")},
    {"key": "xlc", "title": "Communication Services", "fiyat": ("XLC", "AMEX"), "genislik": ("SLTW", "INDEX")},
    {"key": "xlu", "title": "Utilities", "fiyat": ("XLU", "AMEX"), "genislik": ("SUTW", "INDEX")},
]


def _fetch_ohlc(tv, symbol, exchange):
    df = tv.get_hist(symbol=symbol, exchange=exchange, interval=Interval.in_daily, n_bars=N_BARS)
    out = {}
    for ts, row in df.iterrows():
        ts_tr = ts.tz_localize("UTC").astimezone(TR_TZ) if ts.tzinfo is None else ts.astimezone(TR_TZ)
        d = ts_tr.strftime("%Y-%m-%d")
        out[d] = {
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
        }
    return out


def _fetch_close(tv, symbol, exchange):
    df = tv.get_hist(symbol=symbol, exchange=exchange, interval=Interval.in_daily, n_bars=N_BARS)
    out = {}
    for ts, row in df.iterrows():
        ts_tr = ts.tz_localize("UTC").astimezone(TR_TZ) if ts.tzinfo is None else ts.astimezone(TR_TZ)
        out[ts_tr.strftime("%Y-%m-%d")] = float(row["close"])
    return out


def fetch():
    tv = TvDatafeed()
    sonuc = {}

    for sektor in SECTORS:
        fiyat_sym, fiyat_exch = sektor["fiyat"]
        genislik_sym, genislik_exch = sektor["genislik"]
        try:
            ohlc = _fetch_ohlc(tv, fiyat_sym, fiyat_exch)
            genislik = _fetch_close(tv, genislik_sym, genislik_exch)
        except Exception:
            continue  # bir sektor basarisiz olursa digerlerini etkilemesin

        ortak_tarihler = sorted(set(ohlc.keys()) & set(genislik.keys()))
        seri = []
        for tarih in ortak_tarihler:
            bar = ohlc[tarih]
            seri.append({
                "tarih": tarih,
                "acilis": round(bar["open"], 2),
                "yuksek": round(bar["high"], 2),
                "dusuk": round(bar["low"], 2),
                "kapanis": round(bar["close"], 2),
                "genislik_yuzde": round(genislik[tarih], 2),
            })

        sonuc[sektor["key"]] = {
            "title": sektor["title"],
            "fiyat_ticker": f"{fiyat_exch}:{fiyat_sym}",
            "genislik_ticker": f"{genislik_exch}:{genislik_sym}",
            "seri": seri,
        }

    return sonuc
