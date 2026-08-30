"""
Ekonomik takvim - TradingView'in genel widget API'sinden (economic-calendar.
tradingview.com) TR/US/EU/GB/AU/JP icin veri ceker.

Neden TradingView (investing.com veya doviz.com degil):
- investing.com Cloudflare arkasinda, dogrudan (hatta headless tarayiciyla
  bile) kazinamiyor (403).
- doviz.com kazinabiliyor ama: hicbir zaman "Beklenti" (forecast) vermiyor,
  ve sadece Bugun/Yarin/Bu Hafta/Bu Ay sekmeleri var - keyfi tarih araligi
  yok, ay sinirini asan pencereler icin kendi depomuzda birlestirme/budama
  yapmak gerekiyordu.
- TradingView'in bu endpoint'i sadece bir Referer header'i ile herhangi bir
  tarih araligini (ay sinirini asarak) tek istekte donduruyor, Turkiye dahil
  tum ulkeler icin forecast+actual+previous veriyor. Tum olay adlari
  Ingilizce (Turkiye dahil - kullanicinin tercihiyle ceviri yapilmiyor).
"""
from datetime import datetime, timedelta, timezone

import requests

URL = "https://economic-calendar.tradingview.com/events"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Referer": "https://www.tradingview.com/",
    "Origin": "https://www.tradingview.com",
}

COUNTRIES = ["TR", "US", "EU", "GB", "AU", "JP"]

# TradingView importance: -1 (dusuk/tatil), 0 (orta), 1 (yuksek)
IMPORTANCE_LABEL = {-1: "dusuk", 0: "orta", 1: "yuksek"}

TR_TZ = timezone(timedelta(hours=3))
FETCH_WINDOW_DAYS = 8  # goruntulenen 7 gunluk pencereden (app.py) bir gun fazla tampon


def _format_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        value = int(value)
    return str(value)


def _yon(actual, forecast) -> str:
    """Gerceklesen, beklentinin uzerinde mi altinda mi - renklendirme icin."""
    if actual is None or forecast is None:
        return ""
    if actual > forecast:
        return "yukari"
    if actual < forecast:
        return "asagi"
    return "esit"


def fetch():
    now = datetime.now(TR_TZ)
    start = now - timedelta(days=FETCH_WINDOW_DAYS)
    end = now + timedelta(days=FETCH_WINDOW_DAYS)
    params = {
        "from": start.astimezone(timezone.utc).strftime("%Y-%m-%dT00:00:00.000Z"),
        "to": end.astimezone(timezone.utc).strftime("%Y-%m-%dT23:59:59.000Z"),
        "countries": ",".join(COUNTRIES),
    }

    resp = requests.get(URL, headers=HEADERS, params=params, timeout=20)
    resp.raise_for_status()
    data = resp.json()

    events = []
    for item in data.get("result", []):
        country = item.get("country")
        if country not in COUNTRIES:
            continue
        dt = datetime.fromisoformat(item["date"].replace("Z", "+00:00")).astimezone(TR_TZ)
        events.append({
            "tarih": dt.strftime("%Y-%m-%d"),
            "saat": dt.strftime("%H:%M"),
            "ulke_kodu": country,
            "ulke": country,
            "onem": IMPORTANCE_LABEL.get(item.get("importance"), "dusuk"),
            "olay": item.get("title", ""),
            "gerceklesen": _format_value(item.get("actual")),
            "beklenti": _format_value(item.get("forecast")),
            "onceki": _format_value(item.get("previous")),
            "yon": _yon(item.get("actual"), item.get("forecast")),
        })

    events.sort(key=lambda e: (e["tarih"], e["saat"]))
    return events
