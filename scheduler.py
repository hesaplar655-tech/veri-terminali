"""
PythonAnywhere'de bir "Always-on task" olarak calistirilacak surekli process.
Her veri kaynagini kendi frekansinda (sources/__init__.py -> SOURCES) calistirir
ve sonucu data/<key>.json dosyasina yazar.

Yerelde test: python scheduler.py
"""
import logging
import time
from datetime import datetime, timedelta, timezone

import schedule

from sources import SOURCES
import storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("scheduler")

TR_TZ = timezone(timedelta(hours=3))


def make_job(source):
    def job():
        try:
            payload = source.fetch()
            storage.save(source.key, payload)
            log.info("guncellendi: %s", source.key)
        except Exception:
            log.exception("veri cekilemedi: %s", source.key)
    return job


def _should_run_daily(source) -> bool:
    """TR saatiyle gunde 1 kez calisan kaynaklar icin: bugun henuz calismadi mi
    ve hedef saat gecti mi? Sunucunun kendi saat dilimine bagli degil - sistem
    UTC de olsa baska bir dilimde de olsa dogru calisir. Always-on task yeniden
    baslasa bile data/<key>.json'daki son guncelleme zamanina bakarak ayni gun
    icinde tekrar calismaz."""
    record = storage.load(source.key)
    if record is None:
        return True  # hic veri yok, hemen cek

    now = datetime.now(TR_TZ)
    last_tr = datetime.fromisoformat(record["guncellenme_zamani"]).astimezone(TR_TZ)
    if last_tr.date() >= now.date():
        return False  # bugun zaten calisti

    target_h, target_m = (int(x) for x in source.daily_at_tr.split(":"))
    if (now.hour, now.minute) < (target_h, target_m):
        return False  # bugunku saat henuz gelmedi

    return True


def main():
    interval_sources = [s for s in SOURCES if s.daily_at_tr is None]
    daily_sources = [s for s in SOURCES if s.daily_at_tr is not None]

    for source in interval_sources:
        job = make_job(source)
        every = getattr(schedule.every(source.interval_value), source.interval_unit)
        every.do(job)
        job()  # baslangicta bir kere calistir, veri hemen dolsun
        log.info(
            "zamanlandi: %s -> her %s %s",
            source.key, source.interval_value, source.interval_unit,
        )

    for source in daily_sources:
        log.info("zamanlandi: %s -> TR saatiyle gunde 1 kez, %s", source.key, source.daily_at_tr)
        if _should_run_daily(source):
            make_job(source)()

    while True:
        schedule.run_pending()
        for source in daily_sources:
            if _should_run_daily(source):
                make_job(source)()
        time.sleep(30)


if __name__ == "__main__":
    main()
