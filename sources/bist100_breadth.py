"""
BIST 100 uyelerinin yuzde kacinin 200 gunluk hareketli ortalamasinin
uzerinde oldugu ("genislik/breadth" gostergesi) - sp500_breadth.py'nin
BIST 100 hali.

Ham fiyat verisi TradingView'den (tvDatafeed, kullanicinin standart
tercihi) cekiliyor - BIST 100'un sadece 100 uyesi oldugu icin (S&P 500'un
503'u yerine) tvDatafeed ile tek tek cekmek performans acisindan sorun
degil. Uye listesi, gunluk seri cekme ve XU100 (TL/USD) yardimcilari
bist100_common.py'de - RSI genislik kartiyla (bist100_rsi_breadth.py)
paylasiliyor.

Her hisse icin 200 gunluk basit hareketli ortalama (SMA) hesaplanip
kapanis fiyati bu ortalamanin uzerinde mi diye bakiliyor. Karsilastirma
icin BIST 100 endeksinin hem TL (BIST:XU100) hem dolar (BIST:XU100.USD)
cinsinden kapanis fiyati da TradingView'den cekilip ikinci eksende cizgi
olarak ekleniyor.

TR saatiyle gunde 1 kez (23:00) calisir.
"""
import pandas as pd
from tvDatafeed import TvDatafeed

from sources.bist100_common import BIST100_SEMBOLLER, gunluk_seri, xu100_serileri

MA_PERIOD = 200
MIN_KAPSAMA = 0.7  # gunun gecerli sayilmasi icin hisselerin en az %70'inde 200g MA olmali


def _200g_ustunde_mi(kapanislar: pd.Series) -> pd.Series:
    sma200 = kapanislar.rolling(MA_PERIOD).mean()
    ustunde = kapanislar > sma200
    return ustunde.where(sma200.notna())  # MA henuz tanimsizsa (warmup) NaN birak, False sayma


def fetch():
    tv = TvDatafeed()

    xu100_try, xu100_usd = xu100_serileri(tv)

    ustunde_serileri = {}
    for sembol in BIST100_SEMBOLLER:
        try:
            kapanis = gunluk_seri(tv, sembol)
            if kapanis is None or len(kapanis) < MA_PERIOD + 5:
                continue
            ustunde_serileri[sembol] = _200g_ustunde_mi(kapanis)
        except Exception:
            continue  # bir hisse basarisiz olursa digerlerini etkilemesin

    if not ustunde_serileri:
        return []

    ustunde_df = pd.DataFrame(ustunde_serileri).sort_index()

    min_hisse = int(len(ustunde_serileri) * MIN_KAPSAMA)
    events = []
    for tarih, satir in ustunde_df.iterrows():
        gecerli = satir.dropna()
        if len(gecerli) < min_hisse:
            continue
        yuzde = float(gecerli.sum()) / len(gecerli) * 100
        event = {
            "tarih": tarih,
            "ustunde_200g_yuzde": round(yuzde, 2),
            "kapsam": int(len(gecerli)),
        }
        if tarih in xu100_try:
            event["xu100_try"] = round(xu100_try[tarih], 2)
        if tarih in xu100_usd:
            event["xu100_usd"] = round(xu100_usd[tarih], 3)
        events.append(event)

    return events
