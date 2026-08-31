"""
BIST 100 kartlari (bist100_rsi_breadth.py, bist100_breadth.py) arasinda
paylasilan sabitler ve yardimci fonksiyonlar.

BIST 100 uye listesi: TradingView'in kendi bilesen sayfasi
(tr.tradingview.com/symbols/BIST-XU100/components/) + Midas
(getmidas.com/canli-borsa/xu100-bist-100-hisseleri) ile capraz kontrol
edilerek asagida sabit olarak tanimlandi - Wikipedia'nin S&P 500 tablosu
gibi otomatik guncellenen, girisi gerektirmeyen bir kaynak BIST 100 icin
bulunamadi. BIST 100 bilesimi ceyreklik donemlerde (Ocak-Mart, Nisan-
Haziran, Temmuz-Eylul, Ekim-Aralik) degisebilir; bu liste zaman icinde
hafifce eskiyebilir.
"""
from datetime import timezone, timedelta

import pandas as pd
from tvDatafeed import Interval

TR_TZ = timezone(timedelta(hours=3))
N_BARS = 2200  # 2019 basindan itibaren gosterebilmek icin (+200g MA tamponu)
START_DATE = "2019-01-01"

BIST100_SEMBOLLER = [
    "AEFES", "AKBNK", "AKSA", "AKSEN", "ALARK", "ALTNY", "ANSGR", "ARCLK", "ASELS", "ASTOR",
    "BALSU", "BERA", "BIMAS", "BRSAN", "BRYAT", "BSOKE", "BTCIM", "CANTE", "CCOLA", "CIMSA",
    "CVKMD", "CWENE", "DAPGM", "DOAS", "DOHOL", "DSTKF", "ECILC", "EFOR", "EKGYO", "ENERY",
    "ENJSA", "ENKAI", "EREGL", "ESEN", "EUPWR", "EUREN", "FENER", "FROTO", "GARAN", "GENIL",
    "GESAN", "GLRMK", "GRSEL", "GRTHO", "GSRAY", "GUBRF", "HALKB", "HEKTS", "IEYHO", "ISCTR",
    "ISMEN", "IZENR", "KCHOL", "KLRHO", "KRDMD", "KTLEV", "KUYAS", "MAGEN", "MAVI", "MGROS",
    "MIATK", "MPARK", "OBAMS", "ODAS", "ODINE", "OTKAR", "OYAKC", "PAHOL", "PASEU", "PATEK",
    "PETKM", "PGSUS", "PSGYO", "QUAGR", "RALYH", "REEDR", "SAHOL", "SARKY", "SASA", "SISE",
    "SKBNK", "SOKM", "TAVHL", "TCELL", "THYAO", "TKFEN", "TOASO", "TRALT", "TRENJ", "TRMET",
    "TSKB", "TTKOM", "TUKAS", "TUPRS", "TURSG", "ULKER", "VAKBN", "VESTL", "YKBNK", "ZOREN",
]


def gunluk_seri(tv, symbol, exchange="BIST"):
    df = tv.get_hist(symbol=symbol, exchange=exchange, interval=Interval.in_daily, n_bars=N_BARS)
    if df is None or df.empty:
        return None
    out = {}
    for ts, row in df.iterrows():
        d = ts.tz_localize("UTC").astimezone(TR_TZ).strftime("%Y-%m-%d") if ts.tzinfo is None else ts.astimezone(TR_TZ).strftime("%Y-%m-%d")
        out[d] = float(row["close"])
    return pd.Series(out)


def xu100_serileri(tv):
    """(xu100_try, xu100_usd) gunluk kapanis serilerini dondurur (bos olabilir)."""
    xu100_try = gunluk_seri(tv, "XU100")
    xu100_usd = gunluk_seri(tv, "XU100.USD")
    return (
        pd.Series(dtype=float) if xu100_try is None else xu100_try,
        pd.Series(dtype=float) if xu100_usd is None else xu100_usd,
    )
