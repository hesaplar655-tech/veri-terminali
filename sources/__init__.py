"""
Veri kaynaklarinin kayit defteri.

Yeni bir sayfa/veri kaynagi eklemek icin:
1. sources/ altina yeni bir <isim>.py dosyasi olustur, icinde bir `fetch()`
   fonksiyonu tanimla. fetch() bir dict/list dondurmeli (JSON'a yazilacak).
2. Asagidaki SOURCES listesine bir kayit ekle.

interval_unit: "minutes" | "hours" | "days" | "weeks"
interval_value: schedule kutuphanesine gidecek sayi (orn. saatlik icin unit="hours", value=1)
"""
from dataclasses import dataclass
from typing import Callable

from sources import ornek, ekonomik_takvim


@dataclass
class Source:
    key: str            # data/<key>.json dosya adi ve /sayfa/<key> url'i olur
    title: str           # sayfada gorunecek baslik
    fetch: Callable      # veriyi ureten fonksiyon
    interval_unit: str
    interval_value: int = 1


SOURCES: list[Source] = [
    Source(
        key="ekonomik_takvim",
        title="Ekonomik Takvim",
        fetch=ekonomik_takvim.fetch,
        interval_unit="minutes",
        interval_value=30,
    ),
    Source(
        key="ornek",
        title="Ornek Veri",
        fetch=ornek.fetch,
        interval_unit="hours",
        interval_value=1,
    ),
]
