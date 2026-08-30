"""
S&P 500 uyelerinin yuzde kacinin 14 gunluk RSI'i 70'in uzerinde (asiri alim)
ve yuzde kacinin 30'un altinda (asiri satim) oldugu.

Bu veri TradingView'de (ne sembol arama API'sinde ne de tahmin edilebilir
ticker kaliplarinda - S5RH, S5RSI, S5OB vb. hicbiri yok) hazir bir ticker
olarak bulunamadi; arastirildi ve dogrulandi (bkz. proje sohbet gecmisi).
Bu yuzden ham veriyi Yahoo Finance'den (hizli, limitsiz, kimlik dogrulama
gerektirmeyen chart API'si) cekip RSI'i kendimiz hesapliyoruz:

1. S&P 500 uye listesi: Wikipedia "List of S&P 500 companies" tablosu
   (guncel, herkese acik, standart kaynak).
2. Her hisse icin ~2 yillik gunluk kapanis fiyati: Yahoo Finance chart API
   (query1.finance.yahoo.com) - ayni SPY/MAGS kartinda ilk denedigimiz
   kaynak, TradingView'de olmayan bu veri icin tekrar kullaniliyor.
3. RSI(14): Wilder'in orijinal yumusatma yontemi (EWM, alpha=1/14).
4. Her gun icin: gecerli RSI'i olan hisselerin yuzde kaci >70, yuzde kaci
   <30.

503 hisse icin ~3 dakika suruyor ama bunun neredeyse tamami ag bekleme
suresi (CPU degil) - PythonAnywhere'in CPU-saniye kotasini pratikte
zorlamiyor. TR saatiyle gunde 1 kez (23:00) calisir.
"""
import io
from datetime import timezone, timedelta

import pandas as pd
import requests

TR_TZ = timezone(timedelta(hours=3))
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
}
RSI_PERIOD = 14
MIN_KAPSAMA = 0.7  # gunun gecerli sayilmasi icin hisselerin en az %70'inde RSI olmali


def _sp500_semboller():
    r = requests.get(
        "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
        headers=HEADERS, timeout=20,
    )
    r.raise_for_status()
    tablo = pd.read_html(io.StringIO(r.text))[0]
    # Yahoo Finance "BRK.B" degil "BRK-B" bekliyor
    return [s.replace(".", "-") for s in tablo["Symbol"].tolist()]


def _kapanis_serisi(session, sembol):
    resp = session.get(
        f"https://query1.finance.yahoo.com/v8/finance/chart/{sembol}",
        headers=HEADERS, params={"range": "2y", "interval": "1d"}, timeout=15,
    )
    resp.raise_for_status()
    result = resp.json()["chart"]["result"]
    if not result:
        return None
    result = result[0]
    closes = result["indicators"]["adjclose"][0]["adjclose"]
    timestamps = result["timestamp"]
    tarihler, degerler = [], []
    for ts, c in zip(timestamps, closes):
        if c is None:
            continue
        gun = pd.Timestamp(ts, unit="s", tz="UTC").tz_convert(TR_TZ).strftime("%Y-%m-%d")
        tarihler.append(gun)
        degerler.append(c)
    if len(degerler) < RSI_PERIOD + 5:
        return None
    return pd.Series(degerler, index=pd.Index(tarihler, name="tarih"))


def _rsi(kapanislar: pd.Series) -> pd.Series:
    delta = kapanislar.diff()
    kazanc = delta.clip(lower=0)
    kayip = -delta.clip(upper=0)
    ort_kazanc = kazanc.ewm(alpha=1 / RSI_PERIOD, min_periods=RSI_PERIOD, adjust=False).mean()
    ort_kayip = kayip.ewm(alpha=1 / RSI_PERIOD, min_periods=RSI_PERIOD, adjust=False).mean()
    rs = ort_kazanc / ort_kayip
    return 100 - (100 / (1 + rs))


def fetch():
    semboller = _sp500_semboller()

    session = requests.Session()
    rsi_serileri = {}
    for sembol in semboller:
        try:
            kapanis = _kapanis_serisi(session, sembol)
            if kapanis is None:
                continue
            rsi_serileri[sembol] = _rsi(kapanis)
        except Exception:
            continue  # bir hisse basarisiz olursa digerlerini etkilemesin

    if not rsi_serileri:
        return []

    rsi_df = pd.DataFrame(rsi_serileri)  # satir: tarih, sutun: sembol
    rsi_df = rsi_df.sort_index()

    min_hisse = int(len(rsi_serileri) * MIN_KAPSAMA)
    events = []
    for tarih, satir in rsi_df.iterrows():
        gecerli = satir.dropna()
        if len(gecerli) < min_hisse:
            continue
        ustunde_70 = float((gecerli > 70).sum()) / len(gecerli) * 100
        altinda_30 = float((gecerli < 30).sum()) / len(gecerli) * 100
        events.append({
            "tarih": tarih,
            "ustunde_70_yuzde": round(ustunde_70, 2),
            "altinda_30_yuzde": round(altinda_30, 2),
            "kapsam": int(len(gecerli)),
        })

    return events
