"""
BIST 100 uyelerinin yuzde kacinin 14 gunluk RSI'i 70'in uzerinde (asiri alim)
ve yuzde kacinin 30'un altinda (asiri satim) oldugu.

S&P 500 RSI genisligi kartinin (rsi_breadth.py) aksine, burada ham fiyat
verisi TradingView'den (tvDatafeed, kullanicinin standart tercihi) cekiliyor
- BIST 100'un sadece 100 uyesi oldugu icin (S&P 500'un 503'u yerine)
tvDatafeed ile tek tek cekmek performans acisindan sorun degil.

Uye listesi, gunluk seri cekme ve XU100 (TL/USD) yardimcilari
bist100_common.py'de - BIST 100 endeks genisligi kartiyla (bist100_breadth.py)
paylasiliyor.

RSI(14): Wilder'in orijinal yumusatma yontemi (EWM, alpha=1/14). Her gun
icin gecerli RSI'i olan hisselerin yuzde kaci >70, yuzde kaci <30.

Karsilastirma icin BIST 100 endeksinin hem TL (BIST:XU100) hem dolar
(BIST:XU100.USD) cinsinden kapanis fiyati da TradingView'den cekilip
ikinci eksende cizgi olarak ekleniyor.

TR saatiyle gunde 1 kez (23:00) calisir.
"""
import pandas as pd
from tvDatafeed import TvDatafeed

from sources.bist100_common import BIST100_SEMBOLLER, gunluk_seri, xu100_serileri

RSI_PERIOD = 14
MIN_KAPSAMA = 0.7  # gunun gecerli sayilmasi icin hisselerin en az %70'inde RSI olmali


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

    xu100_try, xu100_usd = xu100_serileri(tv)

    rsi_serileri = {}
    for sembol in BIST100_SEMBOLLER:
        try:
            kapanis = gunluk_seri(tv, sembol)
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
