"""
Veri kaynaklarinin kayit defteri.

Yeni bir sayfa/veri kaynagi eklemek icin:
1. sources/ altina yeni bir <isim>.py dosyasi olustur, icinde bir `fetch()`
   fonksiyonu tanimla. fetch() bir dict/list dondurmeli (JSON'a yazilacak).
2. Asagidaki SOURCES listesine bir kayit ekle.

Zamanlama iki sekilde tanimlanabilir (birini kullan):
- interval_unit + interval_value: duzenli araliklarla ("minutes"|"hours"|"days"|"weeks")
- daily_at_tr: Turkiye saatiyle gunde 1 kez ("23:00" gibi) - sunucunun kendi
  saat dilimi ne olursa olsun dogru calisir (scheduler.py TR saatini kendi
  hesaplar, sistem saatine guvenmez).
"""
from dataclasses import dataclass
from typing import Callable, Optional

from sources import ekonomik_takvim, sp500_concentration, sp500_breadth, market_relative, sector_breadth, index_breadth, rsi_breadth, bist100_rsi_breadth, bist100_breadth, bist100_ma_breadth, bist100_sector_drawdown, bist100_excess_return


@dataclass
class Source:
    key: str                     # data/<key>.json dosya adi ve /sayfa/<key> url'i olur
    title: str                    # sayfada gorunecek baslik
    fetch: Callable               # veriyi ureten fonksiyon
    interval_unit: Optional[str] = None
    interval_value: int = 1
    daily_at_tr: Optional[str] = None   # orn. "23:00" - interval_unit yerine kullanilir
    group: str = "SP500 Breadth"        # panel sayfasinda kartin altina gireceği baslik


SOURCES: list[Source] = [
    Source(
        key="ekonomik_takvim",
        title="Ekonomik Takvim",
        fetch=ekonomik_takvim.fetch,
        interval_unit="minutes",
        interval_value=30,
    ),
    Source(
        key="sp500_concentration",
        title="S&P 500 Konsantrasyonu",
        fetch=sp500_concentration.fetch,
        daily_at_tr="23:00",
    ),
    Source(
        key="sp500_breadth",
        title="S&P 500 Genislik (% 200g MA Uzeri)",
        fetch=sp500_breadth.fetch,
        daily_at_tr="23:00",
    ),
    Source(
        key="market_relative",
        title="Zirveden Geri Cekilme: S&P 500 / Nasdaq / RSP",
        fetch=market_relative.fetch,
        interval_unit="hours",
        interval_value=1,
    ),
    Source(
        key="sector_breadth",
        title="Sektor Genislikleri (% 20g MA Uzeri)",
        fetch=sector_breadth.fetch,
        daily_at_tr="23:00",
    ),
    Source(
        key="index_breadth",
        title="Endeks Genislikleri: S&P 500 / Nasdaq / Russell 2000",
        fetch=index_breadth.fetch,
        daily_at_tr="23:00",
    ),
    Source(
        key="rsi_breadth",
        title="S&P 500 RSI Genisligi (14g, Asiri Alim/Satim)",
        fetch=rsi_breadth.fetch,
        daily_at_tr="23:00",
    ),
    Source(
        key="bist100_breadth",
        title="BIST 100 Genislik (% 200g MA Uzeri)",
        fetch=bist100_breadth.fetch,
        daily_at_tr="19:00",
        group="BIST Genislik Gostergeleri",
    ),
    Source(
        key="bist100_excess_return",
        title="BIST 100 3M Excess Return (XU100 - XTUMY)",
        fetch=bist100_excess_return.fetch,
        daily_at_tr="19:00",
        group="BIST Genislik Gostergeleri",
    ),
    Source(
        key="bist100_sector_drawdown",
        title="BIST Sektorleri: Zirveden Geri Cekilme",
        fetch=bist100_sector_drawdown.fetch,
        daily_at_tr="19:00",
        group="BIST Genislik Gostergeleri",
    ),
    Source(
        key="bist100_ma_breadth",
        title="BIST 100 Genislik (% 50g / 200g MA Uzeri)",
        fetch=bist100_ma_breadth.fetch,
        daily_at_tr="19:00",
        group="BIST Genislik Gostergeleri",
    ),
    Source(
        key="bist100_rsi_breadth",
        title="BIST 100 RSI Genisligi (14g, Asiri Alim/Satim)",
        fetch=bist100_rsi_breadth.fetch,
        daily_at_tr="19:00",
        group="BIST Genislik Gostergeleri",
    ),
]
