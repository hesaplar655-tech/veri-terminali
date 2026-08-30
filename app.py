from datetime import datetime, timezone, timedelta

from flask import Flask, abort, render_template

from sources import SOURCES
import storage

app = Flask(__name__)

SOURCES_BY_KEY = {s.key: s for s in SOURCES}

GIRIS_KAYNAK_KEY = "ekonomik_takvim"
GUN_ADLARI = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
AY_ADLARI = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]

# Turkiye saatine gore (UTC+3) bugunku tarihi gostermek icin
TR_TZ = timezone(timedelta(hours=3))


@app.route("/")
def giris():
    record = storage.load(GIRIS_KAYNAK_KEY)
    events = record["veri"] if record else []

    now = datetime.now(TR_TZ)
    bugun = now.date()
    bugun_iso = bugun.isoformat()
    bugun_gorunum = f"{now.day} {AY_ADLARI[now.month - 1]} {now.year}, {GUN_ADLARI[now.weekday()]}"

    # gecen hafta (bugun-7) ile onumuzdeki hafta (bugun+6) arasi, bugun dahil = 14 gun
    gun_sirasi = [(bugun + timedelta(days=i)).isoformat() for i in range(-7, 7)]
    gunler_map = {tarih: [] for tarih in gun_sirasi}
    for event in events:
        if event["tarih"] in gunler_map:
            gunler_map[event["tarih"]].append(event)
    gunler = [(tarih, gunler_map[tarih]) for tarih in gun_sirasi]

    return render_template(
        "giris.html",
        bugun_iso=bugun_iso,
        bugun_gorunum=bugun_gorunum,
        gunler=gunler,
        guncellenme_zamani=record["guncellenme_zamani"] if record else None,
    )


@app.route("/panel")
def panel():
    pages = []
    for source in SOURCES:
        if source.key == GIRIS_KAYNAK_KEY:
            continue
        record = storage.load(source.key)
        pages.append({
            "key": source.key,
            "title": source.title,
            "guncellenme_zamani": record["guncellenme_zamani"] if record else None,
        })
    return render_template("panel.html", pages=pages)


CUSTOM_TEMPLATES = {
    "sp500_concentration": "sp500_concentration.html",
    "sp500_breadth": "sp500_breadth.html",
    "market_relative": "market_relative.html",
    "sector_breadth": "sector_breadth.html",
}


@app.route("/sayfa/<key>")
def page(key):
    source = SOURCES_BY_KEY.get(key)
    if source is None:
        abort(404)
    record = storage.load(key)
    template = CUSTOM_TEMPLATES.get(key, "page.html")
    return render_template(template, source=source, record=record)


if __name__ == "__main__":
    app.run(debug=True)
