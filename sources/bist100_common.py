"""
BIST 100 kartlari (bist100_rsi_breadth.py, bist100_breadth.py,
bist100_ma_breadth.py) arasinda
paylasilan sabitler ve yardimci fonksiyonlar.

BIST 100 uye listesi: TradingView'in kendi bilesen sayfasi
(tr.tradingview.com/symbols/BIST-XU100/components/) + Midas
(getmidas.com/canli-borsa/xu100-bist-100-hisseleri) ile capraz kontrol
edilerek asagida sabit olarak tanimlandi - Wikipedia'nin S&P 500 tablosu
gibi otomatik guncellenen, girisi gerektirmeyen bir kaynak BIST 100 icin
bulunamadi. BIST 100 bilesimi ceyreklik donemlerde (Ocak-Mart, Nisan-
Haziran, Temmuz-Eylul, Ekim-Aralik) degisebilir; bu liste zaman icinde
hafifce eskiyebilir.

Endeks degisikligi ve sabit gecmis: BIST100_SEMBOLLER her zaman GUNCEL
donemin listesidir ve sadece GUNCEL_DONEM_BASLANGIC'tan itibaren hesaplanir.
Bu tarihten onceki gunler sources/sabit/<key>.json'dan okunur - canli
sitedeki degerlerden oldugu gibi dondurulmustur, bir daha hesaplanmaz.
Boylece sunucu her gun sadece guncel 100 hisseyi ceker.
- 2026-10-01 oncesi: Agustos 2026 listesiyle hesaplanmis degerler (sabit).
- 2026-10-01'den itibaren: 1 Ekim - 31 Aralik 2026 donemi bilesimi
  (Borsa Istanbul'un Eylul 2026'da duyurdugu 27 giris / 27 cikis).
  TradingView scanner (SYML:BIST;XU100) ve Midas listeleriyle birebir
  ayni oldugu dogrulandi.
Yeni bir ceyreklik degisiklikte: o gunku canli veriyi yeni yururluk
tarihine kadar sabit dosyalara ekle, BIST100_SEMBOLLER'i ve
GUNCEL_DONEM_BASLANGIC'i guncelle.
"""
import json
import os
from datetime import timezone, timedelta

import pandas as pd
from tvDatafeed import Interval

TR_TZ = timezone(timedelta(hours=3))
N_BARS = 2200  # genis bir gecmis penceresi + 200g MA tamponu
# RSI kartinin gecerli veri kapsamasi (MIN_KAPSAMA) bu tarihten once
# saglanamiyor (bazi hisselerin gecmisi daha kisa); iki kart tutarli
# olsun diye ikisi de bu tarihten baslatiliyor.
START_DATE = "2020-10-30"

# 1 Ekim - 31 Aralik 2026 donemi bilesimi.
BIST100_SEMBOLLER = [
    "AEFES", "AGHOL", "AHGAZ", "AKBNK", "AKCNS", "AKFYE", "AKSA", "AKSEN", "ALARK", "ALBRK",
    "ALTNY", "ANHYT", "ANSGR", "ARCLK", "ASELS", "ASTOR", "AYGAZ", "BERA", "BIMAS", "BINHO",
    "BRSAN", "BRYAT", "BTCIM", "CANTE", "CCOLA", "CIMSA", "CVKMD", "CWENE", "DOAS", "DOHOL",
    "ECILC", "ECZYT", "EGEEN", "EGGUB", "EKGYO", "ENERY", "ENJSA", "ENKAI", "ENTRA", "EREGL",
    "EUREN", "FENER", "FROTO", "GARAN", "GLRMK", "GLYHO", "GRSEL", "GUBRF", "GWIND", "HALKB",
    "HEKTS", "ISCTR", "ISDMR", "ISMEN", "KARSN", "KATMR", "KCAER", "KCHOL", "KORDS", "KRDMD",
    "LMKDC", "MAVI", "MGROS", "MPARK", "OBAMS", "ODAS", "OTKAR", "OYAKC", "PAHOL", "PETKM",
    "PGSUS", "RGYAS", "RYSAS", "SAHOL", "SASA", "SISE", "SNGYO", "SOKM", "TABGD", "TAVHL",
    "TCELL", "TCKRC", "THYAO", "TKFEN", "TOASO", "TRALT", "TRENJ", "TRGYO", "TRMET", "TSKB",
    "TTKOM", "TTRAK", "TUKAS", "TUPRS", "TURSG", "ULKER", "VAKBN", "VESTL", "YKBNK", "ZOREN",
]

# Guncel uye listesi bu tarihten itibaren gecerli; oncesi sabit dosyadan.
GUNCEL_DONEM_BASLANGIC = "2026-10-01"

SABIT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sabit")


def sabit_gecmis(key):
    """GUNCEL_DONEM_BASLANGIC oncesi dondurulmus kayitlar (tarih sirali liste)."""
    path = os.path.join(SABIT_DIR, f"{key}.json")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as f:
        veri = json.load(f)["veri"]
    return [r for r in veri if r["tarih"] < GUNCEL_DONEM_BASLANGIC]


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
