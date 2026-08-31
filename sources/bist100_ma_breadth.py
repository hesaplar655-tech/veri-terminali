"""
BIST 100 uyelerinin yuzde kacinin 50 gunluk ve yuzde kacinin 200 gunluk
hareketli ortalamasinin uzerinde oldugu, ayni grafikte iki seri olarak.

Ham fiyat verisi TradingView'den (tvDatafeed, kullanicinin standart
tercihi) cekiliyor - BIST 100'un sadece 100 uyesi oldugu icin tek tek
cekmek performans acisindan sorun degil. Uye listesi ve gunluk seri cekme
yardimcisi bist100_common.py'de - diger BIST 100 kartlariyla paylasiliyor.
Her hisse icin kapanis serisi sadece bir kez cekiliyor, hem 50g hem 200g
ortalama ayni seriden hesaplaniyor (ekstra ag istegi yok).

START_DATE (bist100_common.py, su an 2020-10-30): RSI genislik kartinda
oldugu gibi, daha erken tarihlerde yeterli hisse kapsamasi (MIN_KAPSAMA)
guvenilir saglanamiyor (bazi hisselerin tvDatafeed uzerinden erisilebilir
gecmisi daha kisa). Diger BIST kartlariyla tutarli olsun diye ayni tarih
kullanildi.

TR saatiyle gunde 1 kez (23:00) calisir.
"""
import pandas as pd
from tvDatafeed import TvDatafeed

from sources.bist100_common import BIST100_SEMBOLLER, START_DATE, gunluk_seri

MA_PERIODS = (50, 200)
MIN_KAPSAMA = 0.7  # gunun gecerli sayilmasi icin hisselerin en az %70'inde ilgili MA olmali


def _ustunde_mi(kapanislar: pd.Series, period: int) -> pd.Series:
    sma = kapanislar.rolling(period).mean()
    ustunde = kapanislar > sma
    return ustunde.where(sma.notna())  # MA henuz tanimsizsa (warmup) NaN birak, False sayma


def fetch():
    tv = TvDatafeed()

    kapanis_serileri = {}
    for sembol in BIST100_SEMBOLLER:
        try:
            kapanis = gunluk_seri(tv, sembol)
            if kapanis is None or len(kapanis) < max(MA_PERIODS) + 5:
                continue
            kapanis_serileri[sembol] = kapanis
        except Exception:
            continue  # bir hisse basarisiz olursa digerlerini etkilemesin

    if not kapanis_serileri:
        return []

    min_hisse = int(len(kapanis_serileri) * MIN_KAPSAMA)
    gunluk_yuzdeler = {}
    for period in MA_PERIODS:
        ustunde_serileri = {s: _ustunde_mi(k, period) for s, k in kapanis_serileri.items()}
        ustunde_df = pd.DataFrame(ustunde_serileri).sort_index()
        gunluk = {}
        for tarih, satir in ustunde_df.iterrows():
            if tarih < START_DATE:
                continue
            gecerli = satir.dropna()
            if len(gecerli) < min_hisse:
                continue
            gunluk[tarih] = round(float(gecerli.sum()) / len(gecerli) * 100, 2)
        gunluk_yuzdeler[period] = gunluk

    ortak_tarihler = sorted(set(gunluk_yuzdeler[50]) & set(gunluk_yuzdeler[200]))
    return [
        {
            "tarih": tarih,
            "ustunde_50g_yuzde": gunluk_yuzdeler[50][tarih],
            "ustunde_200g_yuzde": gunluk_yuzdeler[200][tarih],
        }
        for tarih in ortak_tarihler
    ]
