"""Ornek veri kaynagi - gercek kaynaklar eklendikce silinebilir/referans olarak kalabilir."""
from datetime import datetime, timezone


def fetch():
    return {
        "mesaj": "Bu ornek bir veri kaynagidir.",
        "olusturulma_zamani": datetime.now(timezone.utc).isoformat(),
    }
