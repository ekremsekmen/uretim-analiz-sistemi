"""
Üretim Analiz Sistemi — Streamlit Dashboard
=============================================
Tekstil iplik üretim verilerini SQL'den çekip OEE analizi yapar,
görsel dashboard sunar ve formatlanmış Excel raporu indirir.

Çalıştırma:
    streamlit run app.py
"""

import io
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from analiz import veri_cek, oee_hesapla, makine_bazli_ozet, anormallik_raporu
from veritabani_olustur import veritabani_olustur
import os

# ──────────────────────────────────────────────
# Sayfa Yapılandırması
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="Üretim Analiz Sistemi",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# Özel CSS (modern, temiz tasarım)
# ──────────────────────────────────────────────
st.markdown("""
<style>
    /* Ana başlık */
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        color: #1E3A5F;
        padding-bottom: 0.3rem;
        border-bottom: 3px solid #3B82F6;
        margin-bottom: 1.5rem;
    }
    /* Metrik kart */
    .metric-card {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border-left: 4px solid #3B82F6;
    }
    .metric-card h3 { margin: 0; font-size: 0.85rem; color: #64748b; }
    .metric-card p  { margin: 0; font-size: 1.8rem; font-weight: 700; color: #1e293b; }

    .metric-card-danger { border-left-color: #ef4444; }
    .metric-card-success { border-left-color: #22c55e; }
    .metric-card-warning { border-left-color: #f59e0b; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1E3A5F 0%, #2563EB 100%);
    }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    [data-testid="stSidebar"] .stDateInput label,
    [data-testid="stSidebar"] .stMultiSelect label { color: #e2e8f0 !important; }

    /* Tablo stili */
    .dataframe th { background-color: #1E3A5F !important; color: white !important; }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────
# Veritabanı kontrolü & veri yükleme
# ──────────────────────────────────────────────
DB_YOLU = "uretim.db"

if not os.path.exists(DB_YOLU):
    veritabani_olustur(DB_YOLU)

@st.cache_data(ttl=300)
def veri_yukle():
    df = veri_cek(DB_YOLU)
    df = oee_hesapla(df)
    return df

df_ham = veri_yukle()

# ──────────────────────────────────────────────
# Sidebar — Filtreler
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🔧 Filtreler")
    st.markdown("---")

    # Tarih aralığı
    min_tarih = df_ham["tarih"].min().date()
    max_tarih = df_ham["tarih"].max().date()

    tarih_baslangic = st.date_input("Başlangıç Tarihi", value=min_tarih, min_value=min_tarih, max_value=max_tarih)
    tarih_bitis = st.date_input("Bitiş Tarihi", value=max_tarih, min_value=min_tarih, max_value=max_tarih)

    st.markdown("---")

    # Üretim hattı filtresi
    hatlar = ["Tümü"] + sorted(df_ham["uretim_hatti"].unique().tolist())
    secili_hat = st.selectbox("Üretim Hattı", hatlar)

    # Makine filtresi
    if secili_hat == "Tümü":
        mevcut_makineler = sorted(df_ham["makine_no"].unique().tolist())
    else:
        mevcut_makineler = sorted(
            df_ham[df_ham["uretim_hatti"] == secili_hat]["makine_no"].unique().tolist()
        )
    secili_makineler = st.multiselect("Makine Seçimi", mevcut_makineler, default=mevcut_makineler)

    st.markdown("---")
    st.markdown("##### ℹ️ Hakkında")
    st.caption("Tekstil iplik üretim verilerini analiz eden, OEE hesaplayan ve otomatik raporlar üreten bir karar destek sistemi.")

    # Veritabanını yeniden oluştur butonu
    if st.button("🔄 Verileri Yeniden Oluştur"):
        veritabani_olustur(DB_YOLU)
        st.cache_data.clear()
        st.rerun()

# ──────────────────────────────────────────────
# Filtreleme uygula
# ──────────────────────────────────────────────
df = df_ham[
    (df_ham["tarih"].dt.date >= tarih_baslangic)
    & (df_ham["tarih"].dt.date <= tarih_bitis)
    & (df_ham["makine_no"].isin(secili_makineler))
].copy()

if secili_hat != "Tümü":
    df = df[df["uretim_hatti"] == secili_hat]

# ──────────────────────────────────────────────
# Başlık
# ──────────────────────────────────────────────
st.markdown('<div class="main-header">🏭 Tekstil İplik Üretim Analiz Sistemi</div>', unsafe_allow_html=True)

if df.empty:
    st.warning("Seçilen filtrelere uygun veri bulunamadı.")
    st.stop()

# ──────────────────────────────────────────────
# Metrik Kartları
# ──────────────────────────────────────────────
toplam_uretim = df["toplam_uretim"].sum()
ort_fire_orani = df["fire_orani"].mean()
ort_oee = df["oee"].mean() * 100
kritik_kayit = len(df[df["durum"] == "Kritik"])
toplam_ariza_dk = df["ariza_suresi"].sum()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <h3>Toplam Üretim</h3>
        <p>{toplam_uretim:,.0f} kg</p>
    </div>""", unsafe_allow_html=True)

with col2:
    fire_cls = "metric-card-danger" if ort_fire_orani > 5 else ""
    st.markdown(f"""
    <div class="metric-card {fire_cls}">
        <h3>Ort. Fire Oranı</h3>
        <p>%{ort_fire_orani:.2f}</p>
    </div>""", unsafe_allow_html=True)

with col3:
    oee_cls = "metric-card-success" if ort_oee >= 70 else "metric-card-warning"
    st.markdown(f"""
    <div class="metric-card {oee_cls}">
        <h3>Ort. OEE</h3>
        <p>%{ort_oee:.1f}</p>
    </div>""", unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card metric-card-danger">
        <h3>Kritik Kayıt</h3>
        <p>{kritik_kayit}</p>
    </div>""", unsafe_allow_html=True)

with col5:
    st.markdown(f"""
    <div class="metric-card metric-card-warning">
        <h3>Toplam Arıza</h3>
        <p>{toplam_ariza_dk:,.0f} dk</p>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Grafikler — Satır 1
# ──────────────────────────────────────────────
graf_col1, graf_col2 = st.columns(2)

# 1) Makine Bazlı Verimlilik (OEE) — Sütun Grafiği
with graf_col1:
    st.subheader("📊 Makine Bazlı Verimlilik (OEE)")
    ozet = makine_bazli_ozet(df)

    renk_haritasi = {"Normal": "#22c55e", "Kritik": "#ef4444"}
    fig_oee = px.bar(
        ozet,
        x="makine_no",
        y="ortalama_oee",
        color="durum",
        color_discrete_map=renk_haritasi,
        text="ortalama_oee",
        labels={"makine_no": "Makine", "ortalama_oee": "OEE (%)"},
    )
    fig_oee.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_oee.update_layout(
        yaxis_range=[0, 105],
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend_title_text="Durum",
        height=420,
    )
    # Referans çizgisi: %85 OEE hedef
    fig_oee.add_hline(y=85, line_dash="dash", line_color="#3B82F6",
                      annotation_text="Hedef OEE (%85)")
    st.plotly_chart(fig_oee, width="stretch")

# 2) Günlük Fire Oranı — Çizgi Grafiği
with graf_col2:
    st.subheader("📈 Günlük Fire Oranı Trendi")
    gunluk = df.groupby("tarih").agg(
        ort_fire=("fire_orani", "mean")
    ).reset_index()

    fig_fire = px.line(
        gunluk,
        x="tarih",
        y="ort_fire",
        labels={"tarih": "Tarih", "ort_fire": "Fire Oranı (%)"},
        markers=True,
    )
    fig_fire.update_traces(line_color="#ef4444", fill="tozeroy", fillcolor="rgba(239,68,68,0.1)")
    fig_fire.add_hline(y=5, line_dash="dash", line_color="#f59e0b",
                       annotation_text="Kritik Eşik (%5)")
    fig_fire.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=420,
    )
    st.plotly_chart(fig_fire, width="stretch")

# ──────────────────────────────────────────────
# Grafikler — Satır 2
# ──────────────────────────────────────────────
graf_col3, graf_col4 = st.columns(2)

# 3) Üretim Hattı Bazlı Üretim Dağılımı — Pasta Grafiği
with graf_col3:
    st.subheader("🏭 Hatlara Göre Üretim Dağılımı")
    hat_uretim = df.groupby("uretim_hatti")["toplam_uretim"].sum().reset_index()
    fig_pasta = px.pie(
        hat_uretim,
        values="toplam_uretim",
        names="uretim_hatti",
        color_discrete_sequence=px.colors.qualitative.Set2,
        hole=0.4,
    )
    fig_pasta.update_layout(height=400, paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_pasta, width="stretch")

# 4) OEE Bileşenleri — Radar Grafiği
with graf_col4:
    st.subheader("🎯 OEE Bileşen Analizi (Ortalama)")
    ort_k = df["kullanilabilirlik"].mean() * 100
    ort_p = df["performans"].mean() * 100
    ort_q = df["kalite"].mean() * 100

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=[ort_k, ort_p, ort_q, ort_k],
        theta=["Kullanılabilirlik", "Performans", "Kalite", "Kullanılabilirlik"],
        fill="toself",
        fillcolor="rgba(59,130,246,0.2)",
        line_color="#3B82F6",
        name="Ortalama",
    ))
    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig_radar, width="stretch")

# ──────────────────────────────────────────────
# Anormallik Raporu Tablosu
# ──────────────────────────────────────────────
st.markdown("---")
st.subheader("🚨 Anormallik Raporu (Fire > %5)")

rapor = anormallik_raporu(df)

if rapor.empty:
    st.success("Kritik düzeyde fire oranına sahip kayıt bulunmamaktadır.")
else:
    goster_sutunlar = [
        "makine_no", "uretim_hatti", "tarih", "toplam_uretim",
        "fire_miktari", "fire_orani", "ariza_suresi", "oee", "durum",
    ]
    rapor_goster = rapor[goster_sutunlar].copy()
    rapor_goster["oee"] = (rapor_goster["oee"] * 100).round(1)
    rapor_goster.columns = [
        "Makine", "Hat", "Tarih", "Üretim (kg)", "Fire (kg)",
        "Fire (%)", "Arıza (dk)", "OEE (%)", "Durum",
    ]

    def satirlari_renklendir(row):
        if row["Durum"] == "Kritik":
            return ["background-color: #fef2f2; color: #991b1b"] * len(row)
        return [""] * len(row)

    st.dataframe(
        rapor_goster.style.apply(satirlari_renklendir, axis=1),
        width="stretch",
        height=350,
    )

# ──────────────────────────────────────────────
# Excel Rapor İndirme
# ──────────────────────────────────────────────
st.markdown("---")
st.subheader("📥 Rapor İndir (Excel)")


def excel_olustur(df_tum: pd.DataFrame, df_rapor: pd.DataFrame, df_ozet: pd.DataFrame) -> bytes:
    """
    Formatlanmış Excel dosyası oluşturur.
    Kritik satırlar kırmızıyla işaretlenir.
    """
    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        workbook = writer.book

        # --- Formatlar ---
        baslik_fmt = workbook.add_format({
            "bold": True,
            "bg_color": "#1E3A5F",
            "font_color": "#FFFFFF",
            "border": 1,
            "text_wrap": True,
            "valign": "vcenter",
            "align": "center",
        })
        normal_fmt = workbook.add_format({
            "border": 1,
            "valign": "vcenter",
        })
        kritik_fmt = workbook.add_format({
            "bg_color": "#FEE2E2",
            "font_color": "#991B1B",
            "bold": True,
            "border": 1,
            "valign": "vcenter",
        })
        sayi_fmt = workbook.add_format({
            "num_format": "#,##0.0",
            "border": 1,
            "valign": "vcenter",
        })
        kritik_sayi_fmt = workbook.add_format({
            "num_format": "#,##0.0",
            "bg_color": "#FEE2E2",
            "font_color": "#991B1B",
            "bold": True,
            "border": 1,
            "valign": "vcenter",
        })
        yuzde_fmt = workbook.add_format({
            "num_format": "0.00%",
            "border": 1,
            "valign": "vcenter",
        })
        kritik_yuzde_fmt = workbook.add_format({
            "num_format": "0.00%",
            "bg_color": "#FEE2E2",
            "font_color": "#991B1B",
            "bold": True,
            "border": 1,
            "valign": "vcenter",
        })

        # ============================
        # Sayfa 1: Tüm Veriler
        # ============================
        sheet1_name = "Tüm Üretim Verileri"
        export_cols = [
            "makine_no", "uretim_hatti", "tarih", "vites_saati",
            "toplam_uretim", "fire_miktari", "fire_orani",
            "ariza_suresi", "kullanilabilirlik", "performans",
            "kalite", "oee", "durum",
        ]
        header_labels = [
            "Makine No", "Üretim Hattı", "Tarih", "Vites Saati (s)",
            "Toplam Üretim (kg)", "Fire Miktarı (kg)", "Fire Oranı (%)",
            "Arıza Süresi (dk)", "Kullanılabilirlik", "Performans",
            "Kalite", "OEE", "Durum",
        ]

        df_export = df_tum[export_cols].copy()
        df_export["tarih"] = df_export["tarih"].dt.strftime("%Y-%m-%d")

        # Boş sheet oluştur
        worksheet1 = workbook.add_worksheet(sheet1_name)
        writer.sheets[sheet1_name] = worksheet1

        # Başlıklar
        for col_num, header in enumerate(header_labels):
            worksheet1.write(0, col_num, header, baslik_fmt)

        # Veriler
        sayi_sutunlari = {3, 4, 5, 6, 7}      # vites, üretim, fire, fire_oranı, arıza
        yuzde_sutunlari = {8, 9, 10, 11}       # kull, perf, kalite, oee

        for row_num, (_, row) in enumerate(df_export.iterrows(), start=1):
            is_kritik = row["durum"] == "Kritik"
            for col_num, val in enumerate(row):
                if col_num in sayi_sutunlari:
                    fmt = kritik_sayi_fmt if is_kritik else sayi_fmt
                    worksheet1.write_number(row_num, col_num, float(val), fmt)
                elif col_num in yuzde_sutunlari:
                    fmt = kritik_yuzde_fmt if is_kritik else yuzde_fmt
                    worksheet1.write_number(row_num, col_num, float(val), fmt)
                else:
                    fmt = kritik_fmt if is_kritik else normal_fmt
                    worksheet1.write(row_num, col_num, val, fmt)

        # Sütun genişlikleri
        for i, label in enumerate(header_labels):
            worksheet1.set_column(i, i, max(len(label) + 4, 14))

        # ============================
        # Sayfa 2: Anormallik Raporu
        # ============================
        sheet2_name = "Anormallik Raporu"
        rapor_cols = [
            "makine_no", "uretim_hatti", "tarih",
            "toplam_uretim", "fire_miktari", "fire_orani",
            "ariza_suresi", "oee", "durum",
        ]
        rapor_headers = [
            "Makine No", "Üretim Hattı", "Tarih",
            "Toplam Üretim (kg)", "Fire Miktarı (kg)", "Fire Oranı (%)",
            "Arıza Süresi (dk)", "OEE", "Durum",
        ]

        df_rapor_export = df_rapor[rapor_cols].copy()
        df_rapor_export["tarih"] = df_rapor_export["tarih"].dt.strftime("%Y-%m-%d")

        worksheet2 = workbook.add_worksheet(sheet2_name)
        writer.sheets[sheet2_name] = worksheet2

        for col_num, header in enumerate(rapor_headers):
            worksheet2.write(0, col_num, header, baslik_fmt)

        rapor_sayi_sutunlari = {3, 4, 5, 6}
        rapor_yuzde_sutunlari = {7}

        for row_num, (_, row) in enumerate(df_rapor_export.iterrows(), start=1):
            for col_num, val in enumerate(row):
                if col_num in rapor_sayi_sutunlari:
                    worksheet2.write_number(row_num, col_num, float(val), kritik_sayi_fmt)
                elif col_num in rapor_yuzde_sutunlari:
                    worksheet2.write_number(row_num, col_num, float(val), kritik_yuzde_fmt)
                else:
                    worksheet2.write(row_num, col_num, val, kritik_fmt)

        for i, label in enumerate(rapor_headers):
            worksheet2.set_column(i, i, max(len(label) + 4, 14))

        # ============================
        # Sayfa 3: Makine Özeti
        # ============================
        sheet3_name = "Makine Özet"
        ozet_headers = [
            "Makine No", "Ort. OEE (%)", "Ort. Fire (%)",
            "Toplam Üretim (kg)", "Toplam Fire (kg)",
            "Toplam Arıza (dk)", "Kayıt Sayısı", "Durum",
        ]

        worksheet3 = workbook.add_worksheet(sheet3_name)
        writer.sheets[sheet3_name] = worksheet3

        for col_num, header in enumerate(ozet_headers):
            worksheet3.write(0, col_num, header, baslik_fmt)

        for row_num, (_, row) in enumerate(df_ozet.iterrows(), start=1):
            is_kritik = row["durum"] == "Kritik"
            for col_num, val in enumerate(row):
                if col_num in {1, 2, 3, 4, 5, 6}:
                    fmt = kritik_sayi_fmt if is_kritik else sayi_fmt
                    worksheet3.write_number(row_num, col_num, float(val), fmt)
                else:
                    fmt = kritik_fmt if is_kritik else normal_fmt
                    worksheet3.write(row_num, col_num, val, fmt)

        for i, label in enumerate(ozet_headers):
            worksheet3.set_column(i, i, max(len(label) + 4, 14))

    buffer.seek(0)
    return buffer.getvalue()


# Excel oluştur ve indir butonu
ozet_df = makine_bazli_ozet(df)
rapor_df = anormallik_raporu(df)

col_btn1, col_btn2 = st.columns([1, 3])
with col_btn1:
    excel_data = excel_olustur(df, rapor_df, ozet_df)
    st.download_button(
        label="📥 Excel Raporu İndir",
        data=excel_data,
        file_name="Uretim_Analiz_Raporu.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )

with col_btn2:
    st.caption(
        f"Rapor {len(df)} kayıt içermektedir. "
        f"Kritik makine sayısı: {len(ozet_df[ozet_df['durum'] == 'Kritik'])}. "
        f"Oluşturulma: {pd.Timestamp.now().strftime('%d.%m.%Y %H:%M')}"
    )

# ──────────────────────────────────────────────
# Ham Veri Tablosu (genişletilebilir)
# ──────────────────────────────────────────────
with st.expander("📋 Ham Veri Tablosu (Tümü)", expanded=False):
    st.dataframe(df, width="stretch", height=400)

# ──────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<center style='color:#94a3b8; font-size:0.8rem;'>"
    "Üretim Analiz Sistemi v1.0 — Python · Streamlit · Plotly · SQLite"
    "</center>",
    unsafe_allow_html=True,
)
