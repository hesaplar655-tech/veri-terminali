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

from sources import ornek, ekonomik_takvim, sp500_concentration, sp500_breadth


@dataclass
class Source:
    key: str                     # data/<key>.json dosya adi ve /sayfa/<key> url'i olur
    title: str                    # sayfada gorunecek baslik
    fetch: Callable               # veriyi ureten fonksiyon
    interval_unit: Optional[str] = None
    interval_value: int = 1
    daily_at_tr: Optional[str] = None   # orn. "23:00" - interval_unit yerine kullanilir


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
        key="ornek",
        title="Ornek Veri",
        fetch=ornek.fetch,
        interval_unit="hours",
        interval_value=1,
    ),
]
