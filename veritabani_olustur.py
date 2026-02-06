"""
Tekstil İplik Üretim Veritabanı Oluşturucu
-------------------------------------------
SQLite3 kullanarak gerçekçi üretim verileri içeren bir veritabanı oluşturur.
100 satırlık, tekstil iplik üretimine uygun sahte (ama mantıklı) veriler üretir.
"""

import sqlite3
import random
from datetime import datetime, timedelta


def veritabani_olustur(db_yolu: str = "uretim.db") -> None:
    """Üretim veritabanını oluşturur ve 100 satırlık gerçekçi veri ekler."""

    conn = sqlite3.connect(db_yolu)
    cursor = conn.cursor()

    # Tablo varsa sil ve yeniden oluştur
    cursor.execute("DROP TABLE IF EXISTS uretim_verileri")

    cursor.execute("""
        CREATE TABLE uretim_verileri (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uretim_hatti TEXT NOT NULL,
            makine_no TEXT NOT NULL,
            vites_saati REAL NOT NULL,
            toplam_uretim REAL NOT NULL,
            fire_miktari REAL NOT NULL,
            ariza_suresi REAL NOT NULL,
            tarih TEXT NOT NULL
        )
    """)

    # ---- Gerçekçi parametre aralıkları ----
    uretim_hatlari = ["Hat-A", "Hat-B", "Hat-C"]
    makineler = {
        "Hat-A": ["M-101", "M-102", "M-103", "M-104"],
        "Hat-B": ["M-201", "M-202", "M-203"],
        "Hat-C": ["M-301", "M-302", "M-303"],
    }

    # Bazı makinelerin sorunlu olmasını istiyoruz (demo için)
    sorunlu_makineler = {"M-102", "M-203", "M-302"}

    baslangic_tarihi = datetime(2025, 1, 1)
    veriler = []

    for i in range(100):
        hat = random.choice(uretim_hatlari)
        makine = random.choice(makineler[hat])
        tarih = baslangic_tarihi + timedelta(days=random.randint(0, 89))

        if makine in sorunlu_makineler:
            # Sorunlu makineler: düşük üretim, yüksek fire, fazla arıza
            vites_saati = round(random.uniform(6.0, 8.0), 1)       # saat
            toplam_uretim = round(random.uniform(800, 1400), 1)    # kg
            fire_miktari = round(toplam_uretim * random.uniform(0.04, 0.12), 1)  # %4-12 fire
            ariza_suresi = round(random.uniform(30, 180), 0)       # dakika
        else:
            # Normal makineler: yüksek üretim, düşük fire, az arıza
            vites_saati = round(random.uniform(7.5, 8.0), 1)
            toplam_uretim = round(random.uniform(1400, 2200), 1)
            fire_miktari = round(toplam_uretim * random.uniform(0.01, 0.04), 1)
            ariza_suresi = round(random.uniform(0, 30), 0)

        veriler.append((
            hat,
            makine,
            vites_saati,
            toplam_uretim,
            fire_miktari,
            ariza_suresi,
            tarih.strftime("%Y-%m-%d"),
        ))

    cursor.executemany("""
        INSERT INTO uretim_verileri
            (uretim_hatti, makine_no, vites_saati, toplam_uretim, fire_miktari, ariza_suresi, tarih)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, veriler)

    conn.commit()
    conn.close()
    print(f"Veritabanı başarıyla oluşturuldu: {db_yolu}  ({len(veriler)} satır)")


if __name__ == "__main__":
    veritabani_olustur()
