"""
Yillik enflasyon oranlari (%): TUIK, KKTC (Kuzey Kibris) ve ITO (Istanbul
Ticaret Odasi Ucretliler Gecinme Endeksi) - kullanicinin verdigi referans
gorseldeki "Grafik 1 Yillik Enflasyon Oranlari" ile ayni uc seri.

Bu bir piyasa (TradingView) verisi degil, resmi enflasyon istatistigi -
her kurumun kendi aylik veri portalindan cekiliyor:

1. TUIK (Turkiye Istatistik Kurumu) - TUFE yillik % degisim.
   Kaynak: TCMB EVDS3'un kendi web arayuzunun ("Tablo Olustur" butonu)
   kullandigi ic servis - POST https://evds3.tcmb.gov.tr/igmevdsms-dis/fe,
   seri kodu TP.GENENDEKS.T1 (TUFE Genel Endeksi, 2003=100),
   formulas=3 (Yillik Yuzde Degisim). Bu, EVDS'in resmi/belgelenmis
   API key gerektiren REST servisi (/service/evds/) degil - o servis
   evds2/evds3 tasinmasi sirasinda artik sadece SPA kabugu donduruyor.
   Tarayicida "Tablo Olustur" tiklanip ag istekleri izlenerek bulunan bu
   ic servis kimlik dogrulama gerektirmiyor (public, TUIK'in kendi
   veri portalindan (veriportali.tuik.gov.tr) daha kullanisli - o JS
   sorgu araci oldugu icin dogrudan cekilemiyordu).

2. KKTC Istatistik Kurumu - TUFE yillik % degisim.
   Kaynak: istatistik.gov.ct.tr'nin "Tablolar (MS EXCEL)" sayfasindaki
   "TUFE_ARSIV_YUZDE_<AY>_<YIL>_WEB.xls" arsiv dosyasi (dosya adi her ay
   degisiyor, guncel adi sayfadan otomatik bulunuyor). Workbook'un 3.
   sayfasi ("Bir Onceki Yilin Ayni Ayina Gore") 1978'den gunumuze kadar
   yil x ay tablosu iceriyor, kimlik dogrulama gerekmiyor.

3. ITO (Istanbul Ticaret Odasi) - iki ayri endeks, ikisi de gosteriliyor
   (ayni AJAX endpoint'i, view/rapor05/index.php, sadece IndeksId farkli,
   kimlik dogrulama gerekmiyor):
   - Ucretliler Gecinme Endeksi (1995=100), IndeksId=3: 2015'ten
     gunumuze kesintisiz veri var - kullanicinin ilk verdigi referans
     gorseldeki "ITO" serisiyle ayni. 1 Ocak 2027'de yayimi
     durdurulacagi acaiklandi.
   - Istanbul Tuketici Fiyat Indeksi (2023=100), IndeksId=1: yeni,
     guncel basin bultenlerinde one cikan resmi rakam bu - ama gecmisi
     sadece 2024'ten itibaren var. Kullanici, eski seriyle (39,62%
     Agustos 2026) resmi bultendeki yeni serinin (34,96% Agustos 2026)
     farkli oldugunu fark edip sorunca ikisi de dogrulandi (ito.org.tr
     sitesinin kendisinden) ve ikisinin de gecerli, sadece farkli
     metodolojili iki ayri endeks oldugu anlasildi - kullanicinin
     tercihiyle ikisi de grafige eklendi.

Yayim takvimi (TR saatiyle, resmi sabit bir gun degil, her ay bulten
tarihinden cikarildi):
- TUIK: takip eden ayin ~3-5. is gunu (orn. Agustos verisi 3 Eylul'de aciklandi)
- KKTC: takip eden ayin ~3-5'i
- ITO: takip eden ayin 1. gunu (en erken aciklayan)
Bu farkli tarihler yuzunden sabit bir "ayin X. gunu calis" kurali yerine
diger BIST kartlariyla ayni sekilde HER GUN kontrol ediliyor
(daily_at_tr="19:00") - fetch() her zaman o an mevcut olan en guncel veriyi
cekip birlestirdigi icin, her kurum kendi ayini yayimladiginda kart bir
sonraki gunluk kontrolde otomatik guncellenmis olur.
"""
import re
from datetime import timezone, timedelta

import requests

TR_TZ = timezone(timedelta(hours=3))
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
}
START_YEAR = 2015

AY_ISIMLERI_KKTC = [
    "OCAK", "ŞUBAT", "MART", "NİSAN", "MAYIS", "HAZİRAN",
    "TEMMUZ", "AĞUSTOS", "EYLÜL", "EKİM", "KASIM", "ARALIK",
]


def _tuik_yillik():
    try:
        r = requests.post(
            "https://evds3.tcmb.gov.tr/igmevdsms-dis/fe",
            json={
                "type": "json",
                "series": "TP.GENENDEKS.T1",
                "aggregationTypes": "avg",
                "formulas": "3",  # Yillik Yuzde Degisim
                "startDate": f"01-01-{START_YEAR}",
                "endDate": "01-12-2030",
                "frequency": "5",  # aylik
                "decimalSeperator": ".",
                "decimal": "2",
                "dateFormat": "0",
                "lang": "tr",
                "yon": "0",
                "sira": "0",
                "ozelFormuller": [],
                "groupSeperator": True,
                "isRaporSayfasi": False,
            },
            headers=HEADERS, timeout=20,
        )
        r.raise_for_status()
        veri = r.json().get("items", [])
    except Exception:
        return {}

    out = {}
    for satir in veri:
        tarih = satir.get("Tarih")  # "YYYY-MM" formatinda
        deger = satir.get("TP_GENENDEKS_T1-3")
        if not tarih or deger in (None, ""):
            continue
        try:
            out[tarih] = round(float(deger), 2)
        except (ValueError, TypeError):
            continue
    return out


def _kktc_yillik():
    try:
        sayfa = requests.get(
            "https://istatistik.gov.ct.tr/TEMEL-%C4%B0STAT%C4%B0ST%C4%B0KLER/T%C3%9CKET%C4%B0C%C4%B0-F%C4%B0YAT-ENDEKS%C4%B0",
            headers=HEADERS, timeout=20,
        )
        sayfa.raise_for_status()
        linkler = re.findall(r'href="([^"]*TUFE_ARSIV_YUZDE[^"]*\.xls)"', sayfa.text, re.IGNORECASE)
        if not linkler:
            return {}
        xls_url = linkler[0]
        if xls_url.startswith("/"):
            xls_url = "https://istatistik.gov.ct.tr" + xls_url

        xls = requests.get(xls_url, headers=HEADERS, timeout=20)
        xls.raise_for_status()
        import xlrd
        wb = xlrd.open_workbook(file_contents=xls.content)
        sh = wb.sheet_by_index(2)  # "Bir Onceki Yilin Ayni Ayina Gore"
    except Exception:
        return {}

    # 3. satir: yil basliklari (1978, 1979, ...); 4-15. satirlar: aylar
    yil_satiri = 3
    out = {}
    for col in range(1, sh.ncols):
        try:
            yil = int(sh.cell_value(yil_satiri, col))
        except (ValueError, TypeError):
            continue
        if yil < START_YEAR:
            continue
        for i, ay_adi in enumerate(AY_ISIMLERI_KKTC):
            satir = 4 + i
            if satir >= sh.nrows:
                continue
            deger = sh.cell_value(satir, col)
            if deger == "" or deger is None:
                continue
            try:
                out[f"{yil}-{i + 1:02d}"] = round(float(deger), 2)
            except (ValueError, TypeError):
                continue
    return out


def _ito_yillik(indeks_id, baslangic_yili):
    try:
        r = requests.post(
            "https://ististatistik.ito.org.tr/view/rapor05/index.php",
            data={"IndeksId": str(indeks_id), "Yil": str(baslangic_yili)},
            headers=HEADERS, timeout=20,
        )
        r.raise_for_status()
        r.encoding = "utf-8"
        html = r.text
    except Exception:
        return {}

    # pandas.read_html "11,17" gibi virgullu ondalik sayilari binlik
    # ayiraci sanip 1117'ye cevirdigi icin tabloyu duz regex ile
    # ayikliyoruz - her <tr> bir yil, ardindan 12 aylik <td> hucresi
    out = {}
    satir_regex = re.compile(
        r'<th class="text-white">\s*(\d{4})\s*</th>(.*?)</tr>', re.DOTALL
    )
    hucre_regex = re.compile(r'<td>\s*([^<\s][^<]*?)\s*</td>', re.DOTALL)
    for yil_str, govde in satir_regex.findall(html):
        yil = int(yil_str)
        degerler = hucre_regex.findall(govde)
        for ay, deger in enumerate(degerler[:12], start=1):
            deger = deger.strip()
            if deger in ("-", ""):
                continue
            try:
                out[f"{yil}-{ay:02d}"] = round(float(deger.replace(",", ".")), 2)
            except ValueError:
                continue
    return out


def fetch():
    tuik = _tuik_yillik()
    kktc = _kktc_yillik()
    ito = _ito_yillik(3, START_YEAR)  # Ucretliler Gecinme Endeksi (1995=100)
    ito_yeni = _ito_yillik(1, 2024)   # Istanbul Tuketici Fiyat Indeksi (2023=100)

    tum_aylar = sorted(set(tuik) | set(kktc) | set(ito) | set(ito_yeni))
    events = []
    for ay in tum_aylar:
        event = {"tarih": f"{ay}-01"}
        if ay in tuik:
            event["tuik_yillik"] = tuik[ay]
        if ay in kktc:
            event["kktc_yillik"] = kktc[ay]
        if ay in ito:
            event["ito_yillik"] = ito[ay]
        if ay in ito_yeni:
            event["ito_yeni_yillik"] = ito_yeni[ay]
        if len(event) > 1:  # en az bir seri varsa ekle
            events.append(event)

    return events
