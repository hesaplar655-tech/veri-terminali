"""
PythonAnywhere'de bir "Always-on task" olarak calistirilacak surekli process.
Her veri kaynagini kendi frekansinda (sources/__init__.py -> SOURCES) calistirir
ve sonucu data/<key>.json dosyasina yazar.

Yerelde test: python scheduler.py
"""
import logging
import time

import schedule

from sources import SOURCES
import storage

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("scheduler")


def make_job(source):
    def job():
        try:
            payload = source.fetch()
            storage.save(source.key, payload)
            log.info("guncellendi: %s", source.key)
        except Exception:
            log.exception("veri cekilemedi: %s", source.key)
    return job


def main():
    for source in SOURCES:
        job = make_job(source)
        every = getattr(schedule.every(source.interval_value), source.interval_unit)
        every.do(job)
        job()  # baslangicta bir kere calistir, veri hemen dolsun
        log.info(
            "zamanlandi: %s -> her %s %s",
            source.key, source.interval_value, source.interval_unit,
        )

    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == "__main__":
    main()
