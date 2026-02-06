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
# Özel CSS (profesyonel, kurumsal tasarım)
# ──────────────────────────────────────────────
st.markdown("""
<style>
    /* ── Google Fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

    /* ── Genel ── */
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }

    /* ── Üst Banner ── */
    .top-banner {
        background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #1d4ed8 100%);
        border-radius: 16px;
        padding: 2rem 2.5rem;
        margin-bottom: 1.8rem;
        position: relative;
        overflow: hidden;
    }
    .top-banner::before {
        content: '';
        position: absolute;
        top: -50%; right: -20%;
        width: 400px; height: 400px;
        background: radial-gradient(circle, rgba(59,130,246,0.15) 0%, transparent 70%);
        border-radius: 50%;
    }
    .top-banner::after {
        content: '';
        position: absolute;
        bottom: -30%; left: 10%;
        width: 300px; height: 300px;
        background: radial-gradient(circle, rgba(147,197,253,0.08) 0%, transparent 70%);
        border-radius: 50%;
    }
    .top-banner h1 {
        margin: 0;
        font-size: 1.75rem;
        font-weight: 800;
        color: #ffffff;
        letter-spacing: -0.5px;
        position: relative;
        z-index: 1;
    }
    .top-banner p {
        margin: 0.4rem 0 0 0;
        font-size: 0.9rem;
        color: #93c5fd;
        font-weight: 400;
        position: relative;
        z-index: 1;
    }

    /* ── Metrik Kartları ── */
    .metric-card {
        background: #ffffff;
        border-radius: 14px;
        padding: 1.3rem 1.5rem;
        text-align: left;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.06);
        border: 1px solid #f1f5f9;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        position: relative;
        overflow: hidden;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
    }
    .metric-card .icon {
        font-size: 1.6rem;
        margin-bottom: 0.5rem;
        display: inline-block;
    }
    .metric-card h3 {
        margin: 0;
        font-size: 0.75rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .metric-card .value {
        margin: 0.3rem 0 0 0;
        font-size: 1.7rem;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -0.5px;
    }
    .metric-card .badge {
        display: inline-block;
        margin-top: 0.5rem;
        padding: 0.15rem 0.6rem;
        border-radius: 20px;
        font-size: 0.65rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.3px;
    }
    .badge-blue { background: #eff6ff; color: #2563eb; }
    .badge-green { background: #f0fdf4; color: #16a34a; }
    .badge-red { background: #fef2f2; color: #dc2626; }
    .badge-amber { background: #fffbeb; color: #d97706; }

    /* Kart sol accent çizgisi */
    .metric-card::before {
        content: '';
        position: absolute;
        left: 0; top: 0; bottom: 0;
        width: 4px;
        border-radius: 14px 0 0 14px;
    }
    .card-blue::before  { background: linear-gradient(180deg, #3b82f6, #2563eb); }
    .card-green::before { background: linear-gradient(180deg, #22c55e, #16a34a); }
    .card-red::before   { background: linear-gradient(180deg, #ef4444, #dc2626); }
    .card-amber::before { background: linear-gradient(180deg, #f59e0b, #d97706); }
    .card-purple::before{ background: linear-gradient(180deg, #a855f7, #7c3aed); }

    /* ── Bölüm Başlıkları ── */
    .section-header {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.6rem;
        border-bottom: 2px solid #e2e8f0;
    }
    .section-header .sec-icon {
        width: 36px; height: 36px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
        flex-shrink: 0;
    }
    .sec-blue  { background: #eff6ff; }
    .sec-red   { background: #fef2f2; }
    .sec-green { background: #f0fdf4; }
    .section-header h2 {
        margin: 0;
        font-size: 1.1rem;
        font-weight: 700;
        color: #1e293b;
    }
    .section-header span.sub {
        font-size: 0.8rem;
        color: #94a3b8;
        font-weight: 400;
    }

    /* ── Grafik Konteynerleri ── */
    .chart-container {
        background: #ffffff;
        border-radius: 14px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 4px 12px rgba(0,0,0,0.06);
        border: 1px solid #f1f5f9;
        margin-bottom: 1rem;
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e3a5f 100%);
    }
    [data-testid="stSidebar"] * { color: #ffffff !important; }
    [data-testid="stSidebar"] .stDateInput label,
    [data-testid="stSidebar"] .stMultiSelect label,
    [data-testid="stSidebar"] .stSelectbox label { color: #cbd5e1 !important; }

    .sidebar-logo {
        text-align: center;
        padding: 1.2rem 0 0.8rem 0;
        margin-bottom: 0.5rem;
    }
    .sidebar-logo .logo-icon { font-size: 2.2rem; display: block; }
    .sidebar-logo h2 {
        margin: 0.3rem 0 0 0;
        font-size: 1rem;
        font-weight: 700;
        color: #e2e8f0 !important;
        letter-spacing: -0.3px;
    }
    .sidebar-logo p {
        margin: 0.15rem 0 0 0;
        font-size: 0.7rem;
        color: #64748b !important;
        font-weight: 500;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .sidebar-divider {
        border: 0;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(148,163,184,0.3), transparent);
        margin: 0.8rem 0;
    }

    /* ── Footer ── */
    .footer {
        text-align: center;
        padding: 1.5rem 0 0.5rem 0;
        color: #94a3b8;
        font-size: 0.75rem;
        border-top: 1px solid #e2e8f0;
        margin-top: 2rem;
    }
    .footer a { color: #3b82f6; text-decoration: none; }
    .tech-badges {
        display: flex;
        justify-content: center;
        gap: 0.5rem;
        margin-top: 0.5rem;
        flex-wrap: wrap;
    }
    .tech-badge {
        display: inline-block;
        padding: 0.2rem 0.7rem;
        border-radius: 20px;
        font-size: 0.65rem;
        font-weight: 600;
        background: #f1f5f9;
        color: #475569;
        border: 1px solid #e2e8f0;
    }

    /* ── Streamlit element overrides ── */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        box-shadow: 0 2px 8px rgba(37,99,235,0.3) !important;
        transition: all 0.2s ease !important;
    }
    .stDownloadButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 16px rgba(37,99,235,0.4) !important;
    }

    /* Anormallik tablosu */
    .dataframe th {
        background-color: #0f172a !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 0.8rem !important;
    }

    /* Hide Streamlit default menu/footer/deploy (sidebar toggle korunuyor) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display: none !important;}
    [data-testid="stStatusWidget"] {display: none !important;}
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
    st.markdown("""
    <div class="sidebar-logo">
        <span class="logo-icon">🏭</span>
        <h2>Üretim Analiz</h2>
        <p>Karar Destek Sistemi</p>
    </div>
    <hr class="sidebar-divider">
    """, unsafe_allow_html=True)

    st.markdown("**📅 Tarih Aralığı**")
    min_tarih = df_ham["tarih"].min().date()
    max_tarih = df_ham["tarih"].max().date()

    tarih_baslangic = st.date_input("Başlangıç", value=min_tarih, min_value=min_tarih, max_value=max_tarih)
    tarih_bitis = st.date_input("Bitiş", value=max_tarih, min_value=min_tarih, max_value=max_tarih)

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

    st.markdown("**🔧 Filtreler**")
    hatlar = ["Tümü"] + sorted(df_ham["uretim_hatti"].unique().tolist())
    secili_hat = st.selectbox("Üretim Hattı", hatlar)

    if secili_hat == "Tümü":
        mevcut_makineler = sorted(df_ham["makine_no"].unique().tolist())
    else:
        mevcut_makineler = sorted(
            df_ham[df_ham["uretim_hatti"] == secili_hat]["makine_no"].unique().tolist()
        )
    secili_makineler = st.multiselect("Makine Seçimi", mevcut_makineler, default=mevcut_makineler)

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)

    if st.button("🔄 Verileri Yeniden Oluştur", use_container_width=True):
        veritabani_olustur(DB_YOLU)
        st.cache_data.clear()
        st.rerun()

    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
    st.markdown('<hr class="sidebar-divider">', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center; padding: 0.5rem 0;">
        <p style="font-size: 0.7rem; color: #94a3b8 !important; margin: 0;">Geliştiren</p>
        <p style="font-size: 0.85rem; font-weight: 700; color: #e2e8f0 !important; margin: 0.2rem 0 0 0;">Ekrem Sekmen</p>
    </div>
    """, unsafe_allow_html=True)

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
# Üst Banner
# ──────────────────────────────────────────────
st.markdown(f"""
<div class="top-banner">
    <h1>📊 Tekstil İplik Üretim Analiz Sistemi</h1>
    <p>Gerçek zamanlı üretim takibi &bull; OEE analizi &bull; Otomatik raporlama &bull;
    {tarih_baslangic.strftime('%d.%m.%Y')} – {tarih_bitis.strftime('%d.%m.%Y')}</p>
</div>
""", unsafe_allow_html=True)

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

# OEE durum badge
if ort_oee >= 85:
    oee_badge = '<span class="badge badge-green">Mükemmel</span>'
elif ort_oee >= 70:
    oee_badge = '<span class="badge badge-blue">İyi</span>'
elif ort_oee >= 50:
    oee_badge = '<span class="badge badge-amber">Geliştirilmeli</span>'
else:
    oee_badge = '<span class="badge badge-red">Kritik</span>'

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.markdown(f"""
    <div class="metric-card card-blue">
        <span class="icon">📦</span>
        <h3>Toplam Üretim</h3>
        <p class="value">{toplam_uretim:,.0f}</p>
        <span class="badge badge-blue">kg</span>
    </div>""", unsafe_allow_html=True)

with col2:
    fire_badge = "badge-red" if ort_fire_orani > 5 else "badge-green"
    fire_label = "Yüksek" if ort_fire_orani > 5 else "Normal"
    st.markdown(f"""
    <div class="metric-card card-{"red" if ort_fire_orani > 5 else "green"}">
        <span class="icon">🔥</span>
        <h3>Ort. Fire Oranı</h3>
        <p class="value">%{ort_fire_orani:.2f}</p>
        <span class="badge {fire_badge}">{fire_label}</span>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card card-green">
        <span class="icon">⚡</span>
        <h3>Ortalama OEE</h3>
        <p class="value">%{ort_oee:.1f}</p>
        {oee_badge}
    </div>""", unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card card-red">
        <span class="icon">🚨</span>
        <h3>Kritik Kayıt</h3>
        <p class="value">{kritik_kayit}</p>
        <span class="badge badge-red">{len(df)} kayıttan</span>
    </div>""", unsafe_allow_html=True)

with col5:
    ariza_saat = toplam_ariza_dk / 60
    st.markdown(f"""
    <div class="metric-card card-amber">
        <span class="icon">🔧</span>
        <h3>Toplam Arıza</h3>
        <p class="value">{toplam_ariza_dk:,.0f}</p>
        <span class="badge badge-amber">{ariza_saat:.1f} saat</span>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Grafikler — Satır 1
# ──────────────────────────────────────────────
st.markdown("""
<div class="section-header">
    <div class="sec-icon sec-blue">📊</div>
    <div>
        <h2>Verimlilik Analizi</h2>
        <span class="sub">Makine bazlı OEE ve günlük fire trendi</span>
    </div>
</div>
""", unsafe_allow_html=True)

graf_col1, graf_col2 = st.columns(2)

# 1) Makine Bazlı Verimlilik (OEE) — Sütun Grafiği
with graf_col1:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
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
        title="Makine Bazlı OEE Karşılaştırması",
    )
    fig_oee.update_traces(
        texttemplate="%{text:.1f}%",
        textposition="outside",
        marker_line_width=0,
    )
    fig_oee.update_layout(
        yaxis_range=[0, 105],
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend_title_text="Durum",
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(family="Inter"),
        title_font=dict(size=14, color="#1e293b"),
    )
    fig_oee.add_hline(y=85, line_dash="dash", line_color="#3B82F6",
                      annotation_text="Hedef (%85)", annotation_font_size=11)
    fig_oee.update_xaxes(showgrid=False)
    fig_oee.update_yaxes(gridcolor="#f1f5f9")
    st.plotly_chart(fig_oee, width="stretch")
    st.markdown('</div>', unsafe_allow_html=True)

# 2) Günlük Fire Oranı — Çizgi Grafiği
with graf_col2:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    gunluk = df.groupby("tarih").agg(
        ort_fire=("fire_orani", "mean")
    ).reset_index()

    fig_fire = px.area(
        gunluk,
        x="tarih",
        y="ort_fire",
        labels={"tarih": "Tarih", "ort_fire": "Fire Oranı (%)"},
        title="Günlük Fire Oranı Trendi",
    )
    fig_fire.update_traces(
        line_color="#ef4444",
        fillcolor="rgba(239,68,68,0.08)",
        line_shape="spline",
        line_width=2.5,
    )
    fig_fire.add_hline(y=5, line_dash="dash", line_color="#f59e0b",
                       annotation_text="Kritik Eşik (%5)", annotation_font_size=11)
    fig_fire.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(family="Inter"),
        title_font=dict(size=14, color="#1e293b"),
    )
    fig_fire.update_xaxes(showgrid=False)
    fig_fire.update_yaxes(gridcolor="#f1f5f9")
    st.plotly_chart(fig_fire, width="stretch")
    st.markdown('</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Grafikler — Satır 2
# ──────────────────────────────────────────────
st.markdown("""
<div class="section-header">
    <div class="sec-icon sec-green">🎯</div>
    <div>
        <h2>Dağılım ve Bileşen Analizi</h2>
        <span class="sub">Hatlara göre üretim ve OEE bileşen detayları</span>
    </div>
</div>
""", unsafe_allow_html=True)

graf_col3, graf_col4 = st.columns(2)

# 3) Üretim Hattı Bazlı Üretim Dağılımı — Donut Grafiği
with graf_col3:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    hat_uretim = df.groupby("uretim_hatti")["toplam_uretim"].sum().reset_index()
    fig_pasta = px.pie(
        hat_uretim,
        values="toplam_uretim",
        names="uretim_hatti",
        color_discrete_sequence=["#3b82f6", "#22c55e", "#f59e0b", "#ef4444"],
        hole=0.55,
        title="Hatlara Göre Üretim Dağılımı",
    )
    fig_pasta.update_layout(
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=50, b=20),
        font=dict(family="Inter"),
        title_font=dict(size=14, color="#1e293b"),
    )
    fig_pasta.update_traces(
        textinfo="percent+label",
        textfont_size=12,
        marker=dict(line=dict(color='#ffffff', width=2)),
    )
    st.plotly_chart(fig_pasta, width="stretch")
    st.markdown('</div>', unsafe_allow_html=True)

# 4) OEE Bileşenleri — Radar Grafiği
with graf_col4:
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    ort_k = df["kullanilabilirlik"].mean() * 100
    ort_p = df["performans"].mean() * 100
    ort_q = df["kalite"].mean() * 100

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=[ort_k, ort_p, ort_q, ort_k],
        theta=["Kullanılabilirlik", "Performans", "Kalite", "Kullanılabilirlik"],
        fill="toself",
        fillcolor="rgba(59,130,246,0.15)",
        line_color="#3B82F6",
        line_width=2.5,
        name="Ortalama",
    ))
    # Hedef cizgisi
    fig_radar.add_trace(go.Scatterpolar(
        r=[85, 85, 85, 85],
        theta=["Kullanılabilirlik", "Performans", "Kalite", "Kullanılabilirlik"],
        fill="none",
        line_color="#e2e8f0",
        line_dash="dash",
        line_width=1.5,
        name="Hedef (%85)",
    ))
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="#f1f5f9"),
            angularaxis=dict(gridcolor="#f1f5f9"),
            bgcolor="rgba(0,0,0,0)",
        ),
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=40, r=40, t=50, b=20),
        font=dict(family="Inter"),
        title="OEE Bileşen Analizi",
        title_font=dict(size=14, color="#1e293b"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
    )
    st.plotly_chart(fig_radar, width="stretch")
    st.markdown('</div>', unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Anormallik Raporu Tablosu
# ──────────────────────────────────────────────
rapor = anormallik_raporu(df)

st.markdown(f"""
<div class="section-header">
    <div class="sec-icon sec-red">🚨</div>
    <div>
        <h2>Anormallik Raporu</h2>
        <span class="sub">Fire oranı %5'i aşan kayıtlar &bull; {len(rapor)} kritik kayıt tespit edildi</span>
    </div>
</div>
""", unsafe_allow_html=True)

if rapor.empty:
    st.success("Kritik düzeyde fire oranına sahip kayıt bulunmamaktadır. Tüm makineler normal aralıkta.")
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
            return ["background-color: #fef2f2; color: #991b1b; font-weight: 600"] * len(row)
        return [""] * len(row)

    st.dataframe(
        rapor_goster.style.apply(satirlari_renklendir, axis=1),
        width="stretch",
        height=350,
    )

# ──────────────────────────────────────────────
# Excel Rapor İndirme
# ──────────────────────────────────────────────
st.markdown("<br>", unsafe_allow_html=True)


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

        worksheet1 = workbook.add_worksheet(sheet1_name)
        writer.sheets[sheet1_name] = worksheet1

        for col_num, header in enumerate(header_labels):
            worksheet1.write(0, col_num, header, baslik_fmt)

        sayi_sutunlari = {3, 4, 5, 6, 7}
        yuzde_sutunlari = {8, 9, 10, 11}

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

dl_col1, dl_col2, dl_col3 = st.columns([1.2, 2, 1])
with dl_col1:
    excel_data = excel_olustur(df, rapor_df, ozet_df)
    st.download_button(
        label="📥 Excel Raporu İndir",
        data=excel_data,
        file_name="Uretim_Analiz_Raporu.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )
with dl_col2:
    st.caption(
        f"📋 {len(df)} kayıt &bull; "
        f"🚨 {len(rapor_df)} kritik &bull; "
        f"🕐 {pd.Timestamp.now().strftime('%d.%m.%Y %H:%M')}"
    )

# ──────────────────────────────────────────────
# Ham Veri Tablosu (genişletilebilir)
# ──────────────────────────────────────────────
with st.expander("📋 Detaylı Veri Tablosu", expanded=False):
    st.dataframe(df, width="stretch", height=400)

# ──────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────
st.markdown("""
<div class="footer">
    <p>Üretim Analiz Sistemi v1.0 &mdash; Tasarım ve geliştirme: <strong>Ekrem Sekmen</strong></p>
    <div class="tech-badges">
        <span class="tech-badge">Python</span>
        <span class="tech-badge">Streamlit</span>
        <span class="tech-badge">Plotly</span>
        <span class="tech-badge">Pandas</span>
        <span class="tech-badge">SQLite</span>
        <span class="tech-badge">XlsxWriter</span>
    </div>
</div>
""", unsafe_allow_html=True)
