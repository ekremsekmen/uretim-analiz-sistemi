"""
Üretim Analiz Modülü
--------------------
SQL veritabanından verileri çeker, OEE hesaplar ve anormallik raporu oluşturur.

OEE (Overall Equipment Effectiveness) Formülü:
    OEE = Kullanılabilirlik × Performans × Kalite

Tanımlar:
    - Kullanılabilirlik = (Planlı Süre − Arıza Süresi) / Planlı Süre
    - Performans        = Gerçek Üretim / Teorik Kapasite
    - Kalite            = (Toplam Üretim − Fire) / Toplam Üretim
"""

import sqlite3
import pandas as pd


# ---- Sabitler ----
PLANLI_CALISMA_SURESI_DK = 480  # 8 saatlik vardiya (dakika)
TEORIK_KAPASITE_KG = 2200       # Makine başı ideal günlük kapasite (kg)
FIRE_ESIK_YUZDESI = 5.0         # %5 üzeri fire → Kritik


def veri_cek(db_yolu: str = "uretim.db") -> pd.DataFrame:
    """Veritabanından tüm üretim verilerini Pandas DataFrame olarak döndürür."""
    conn = sqlite3.connect(db_yolu)
    df = pd.read_sql_query("SELECT * FROM uretim_verileri", conn)
    conn.close()
    df["tarih"] = pd.to_datetime(df["tarih"])
    return df


def oee_hesapla(df: pd.DataFrame) -> pd.DataFrame:
    """
    Her satır için OEE bileşenlerini hesaplar ve DataFrame'e ekler.
    Dönen sütunlar: kullanilabilirlik, performans, kalite, oee, fire_orani, durum
    """
    df = df.copy()

    # Kullanılabilirlik
    df["kullanilabilirlik"] = (
        (PLANLI_CALISMA_SURESI_DK - df["ariza_suresi"]) / PLANLI_CALISMA_SURESI_DK
    ).clip(0, 1)

    # Performans
    df["performans"] = (df["toplam_uretim"] / TEORIK_KAPASITE_KG).clip(0, 1)

    # Kalite
    df["kalite"] = (
        (df["toplam_uretim"] - df["fire_miktari"]) / df["toplam_uretim"]
    ).clip(0, 1)

    # OEE
    df["oee"] = df["kullanilabilirlik"] * df["performans"] * df["kalite"]

    # Fire oranı (%)
    df["fire_orani"] = (df["fire_miktari"] / df["toplam_uretim"] * 100).round(2)

    # Durum etiketleme
    df["durum"] = df["fire_orani"].apply(
        lambda x: "Kritik" if x > FIRE_ESIK_YUZDESI else "Normal"
    )

    return df


def makine_bazli_ozet(df: pd.DataFrame) -> pd.DataFrame:
    """Makine bazlı ortalama OEE ve fire oranı özetini döndürür."""
    ozet = (
        df.groupby("makine_no")
        .agg(
            ortalama_oee=("oee", "mean"),
            ortalama_fire_orani=("fire_orani", "mean"),
            toplam_uretim=("toplam_uretim", "sum"),
            toplam_fire=("fire_miktari", "sum"),
            toplam_ariza_dk=("ariza_suresi", "sum"),
            kayit_sayisi=("id", "count"),
        )
        .reset_index()
    )
    ozet["ortalama_oee"] = (ozet["ortalama_oee"] * 100).round(2)
    ozet["ortalama_fire_orani"] = ozet["ortalama_fire_orani"].round(2)
    ozet["durum"] = ozet["ortalama_fire_orani"].apply(
        lambda x: "Kritik" if x > FIRE_ESIK_YUZDESI else "Normal"
    )
    return ozet


def anormallik_raporu(df: pd.DataFrame) -> pd.DataFrame:
    """Fire oranı %5'in üzerinde olan kayıtları 'Anormallik Raporu' olarak döndürür."""
    kritik = df[df["durum"] == "Kritik"].copy()
    kritik = kritik.sort_values(["fire_orani"], ascending=False)
    return kritik


if __name__ == "__main__":
    veriler = veri_cek()
    analiz = oee_hesapla(veriler)
    ozet = makine_bazli_ozet(analiz)
    rapor = anormallik_raporu(analiz)

    print("\n=== Makine Bazlı OEE Özeti ===")
    print(ozet.to_string(index=False))

    print(f"\n=== Anormallik Raporu ({len(rapor)} kayıt) ===")
    print(rapor[["makine_no", "tarih", "toplam_uretim", "fire_miktari", "fire_orani", "oee", "durum"]]
          .to_string(index=False))
