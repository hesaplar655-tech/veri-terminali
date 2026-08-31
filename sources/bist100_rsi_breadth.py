"""
BIST 100 uyelerinin yuzde kacinin 14 gunluk RSI'i 70'in uzerinde (asiri alim)
ve yuzde kacinin 30'un altinda (asiri satim) oldugu.

S&P 500 RSI genisligi kartinin (rsi_breadth.py) aksine, burada ham fiyat
verisi TradingView'den (tvDatafeed, kullanicinin standart tercihi) cekiliyor
- BIST 100'un sadece 100 uyesi oldugu icin (S&P 500'un 503'u yerine)
tvDatafeed ile tek tek cekmek performans acisindan sorun degil.

1. BIST 100 uye listesi: TradingView'in kendi bilesen sayfasi
   (tr.tradingview.com/symbols/BIST-XU100/components/) + Midas
   (getmidas.com/canli-borsa/xu100-bist-100-hisseleri) ile capraz kontrol
   edilerek asagida sabit olarak tanimlandi - Wikipedia'nin S&P 500
   tablosu gibi otomatik guncellenen, girisi gerektirmeyen bir kaynak BIST
   100 icin bulunamadi. BIST 100 bilesimi ceyreklik donemlerde (Ocak-Mart,
   Nisan-Haziran, Temmuz-Eylul, Ekim-Aralik) degisebilir; bu liste zaman
   icinde hafifce eskiyebilir.
2. Her hisse icin ~2 yillik gunluk kapanis fiyati: tvDatafeed (exchange
   "BIST").
3. RSI(14): Wilder'in orijinal yumusatma yontemi (EWM, alpha=1/14).
4. Her gun icin: gecerli RSI'i olan hisselerin yuzde kaci >70, yuzde kaci
   <30.

Karsilastirma icin BIST 100 endeksinin hem TL (BIST:XU100) hem dolar
(BIST:XU100.USD) cinsinden kapanis fiyati da TradingView'den cekilip
ikinci eksende cizgi olarak ekleniyor.

TR saatiyle gunde 1 kez (23:00) calisir.
"""
from datetime import timezone, timedelta

import pandas as pd
from tvDatafeed import TvDatafeed, Interval

TR_TZ = timezone(timedelta(hours=3))
RSI_PERIOD = 14
MIN_KAPSAMA = 0.7  # gunun gecerli sayilmasi icin hisselerin en az %70'inde RSI olmali
N_BARS = 600  # ~2 yillik gunluk bar + tampon

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


def _gunluk_seri(tv, symbol, exchange):
    df = tv.get_hist(symbol=symbol, exchange=exchange, interval=Interval.in_daily, n_bars=N_BARS)
    if df is None or df.empty:
        return None
    out = {}
    for ts, row in df.iterrows():
        d = ts.tz_localize("UTC").astimezone(TR_TZ).strftime("%Y-%m-%d") if ts.tzinfo is None else ts.astimezone(TR_TZ).strftime("%Y-%m-%d")
        out[d] = float(row["close"])
    return pd.Series(out)


def _rsi(kapanislar: pd.Series) -> pd.Series:
    delta = kapanislar.diff()
    kazanc = delta.clip(lower=0)
    kayip = -delta.clip(upper=0)
    ort_kazanc = kazanc.ewm(alpha=1 / RSI_PERIOD, min_periods=RSI_PERIOD, adjust=False).mean()
    ort_kayip = kayip.ewm(alpha=1 / RSI_PERIOD, min_periods=RSI_PERIOD, adjust=False).mean()
    rs = ort_kazanc / ort_kayip
    return 100 - (100 / (1 + rs))


def fetch():
    tv = TvDatafeed()

    xu100_try = _gunluk_seri(tv, "XU100", "BIST")
    xu100_try = {} if xu100_try is None else xu100_try
    xu100_usd = _gunluk_seri(tv, "XU100.USD", "BIST")
    xu100_usd = {} if xu100_usd is None else xu100_usd

    rsi_serileri = {}
    for sembol in BIST100_SEMBOLLER:
        try:
            kapanis = _gunluk_seri(tv, sembol, "BIST")
            if kapanis is None or len(kapanis) < RSI_PERIOD + 5:
                continue
            rsi_serileri[sembol] = _rsi(kapanis)
        except Exception:
            continue  # bir hisse basarisiz olursa digerlerini etkilemesin

    if not rsi_serileri:
        return []

    rsi_df = pd.DataFrame(rsi_serileri).sort_index()

    min_hisse = int(len(rsi_serileri) * MIN_KAPSAMA)
    events = []
    for tarih, satir in rsi_df.iterrows():
        gecerli = satir.dropna()
        if len(gecerli) < min_hisse:
            continue
        ustunde_70 = float((gecerli > 70).sum()) / len(gecerli) * 100
        altinda_30 = float((gecerli < 30).sum()) / len(gecerli) * 100
        event = {
            "tarih": tarih,
            "ustunde_70_yuzde": round(ustunde_70, 2),
            "altinda_30_yuzde": round(altinda_30, 2),
            "kapsam": int(len(gecerli)),
        }
        if tarih in xu100_try:
            event["xu100_try"] = round(xu100_try[tarih], 2)
        if tarih in xu100_usd:
            event["xu100_usd"] = round(xu100_usd[tarih], 3)
        events.append(event)

    return events
