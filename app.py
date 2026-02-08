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
# Temiz, okunabilir CSS
# ──────────────────────────────────────────────
st.markdown("""
<style>
    /* Genel */
    .block-container { padding-top: 1.5rem; }

    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #1e293b; }
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stMarkdown * { color: #e2e8f0 !important; }
    /* Input/select icindeki yazilari koyu yap (okunabilirlik) */
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] select,
    [data-testid="stSidebar"] [data-baseweb="select"] span,
    [data-testid="stSidebar"] [data-baseweb="input"] input,
    [data-testid="stSidebar"] .stDateInput input,
    [data-testid="stSidebar"] .stSelectbox [data-baseweb="select"] div { color: #0f172a !important; }
    /* Multiselect tag yazilari */
    [data-testid="stSidebar"] [data-baseweb="tag"] span { color: #ffffff !important; }

    .sidebar-brand {
        text-align: center;
        padding: 1.2rem 0 0.5rem 0;
    }
    .sidebar-brand h2 { margin: 0; font-size: 1.15rem; font-weight: 800; color: #ffffff !important; letter-spacing: -0.3px; }
    .sidebar-brand p { margin: 0.2rem 0 0 0; font-size: 0.65rem; color: #64748b !important; letter-spacing: 2px; text-transform: uppercase; font-weight: 500; }
    .sidebar-sep { border: 0; height: 1px; background: rgba(148,163,184,0.2); margin: 0.8rem 0; }

    /* Metrik kartlar */
    .kpi-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; }
    .kpi-card {
        flex: 1;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 1rem 1.2rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }
    .kpi-card .label { font-size: 0.75rem; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px; margin: 0; }
    .kpi-card .val { font-size: 1.6rem; font-weight: 800; color: #0f172a; margin: 0.2rem 0 0 0; }
    .kpi-card .sub { font-size: 0.7rem; color: #94a3b8; margin: 0.2rem 0 0 0; }
    .kpi-accent-blue   { border-left: 4px solid #2563eb; }
    .kpi-accent-green  { border-left: 4px solid #16a34a; }
    .kpi-accent-red    { border-left: 4px solid #dc2626; }
    .kpi-accent-amber  { border-left: 4px solid #d97706; }
    .kpi-accent-purple { border-left: 4px solid #7c3aed; }

    /* Başlık bandı */
    .page-title {
        background: #1e293b;
        color: #ffffff;
        padding: 1.5rem 2rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    .page-title h1 { margin: 0; font-size: 1.5rem; font-weight: 700; }
    .page-title p { margin: 0.3rem 0 0 0; font-size: 0.85rem; color: #94a3b8; }

    /* Bölüm başlıkları */
    .sec-title {
        font-size: 1rem;
        font-weight: 700;
        color: #1e293b;
        margin: 1.5rem 0 0.3rem 0;
        padding-bottom: 0.4rem;
        border-bottom: 2px solid #e2e8f0;
    }
    .sec-sub { font-size: 0.8rem; color: #64748b; margin: 0 0 1rem 0; }

    /* Footer */
    .app-footer {
        text-align: center;
        padding: 1.5rem 0 0.5rem 0;
        margin-top: 2rem;
        border-top: 1px solid #e2e8f0;
        font-size: 0.75rem;
        color: #94a3b8;
    }
    .app-footer strong { color: #475569; }
    .tech-pills { display: flex; justify-content: center; gap: 0.4rem; margin-top: 0.5rem; flex-wrap: wrap; }
    .tech-pill { padding: 0.15rem 0.6rem; border-radius: 20px; font-size: 0.65rem; font-weight: 600; background: #f1f5f9; color: #475569; }

    /* Gizle */
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
# Sidebar
# ──────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <h2>URETIM ANALIZ</h2>
        <p>Karar Destek Sistemi</p>
    </div>
    <hr class="sidebar-sep">
    """, unsafe_allow_html=True)

    min_tarih = df_ham["tarih"].min().date()
    max_tarih = df_ham["tarih"].max().date()

    st.markdown("**Tarih Aralığı**")
    tarih_baslangic = st.date_input("Başlangıç", value=min_tarih, min_value=min_tarih, max_value=max_tarih)
    tarih_bitis = st.date_input("Bitiş", value=max_tarih, min_value=min_tarih, max_value=max_tarih)

    st.markdown('<hr class="sidebar-sep">', unsafe_allow_html=True)

    st.markdown("**Filtreler**")
    hatlar = ["Tümü"] + sorted(df_ham["uretim_hatti"].unique().tolist())
    secili_hat = st.selectbox("Üretim Hattı", hatlar)

    if secili_hat == "Tümü":
        mevcut_makineler = sorted(df_ham["makine_no"].unique().tolist())
    else:
        mevcut_makineler = sorted(
            df_ham[df_ham["uretim_hatti"] == secili_hat]["makine_no"].unique().tolist()
        )
    secili_makineler = st.multiselect("Makine", mevcut_makineler, default=mevcut_makineler)

    st.markdown('<hr class="sidebar-sep">', unsafe_allow_html=True)

    if st.button("🔄 Verileri Yeniden Oluştur", use_container_width=True):
        veritabani_olustur(DB_YOLU)
        st.cache_data.clear()
        st.rerun()

    st.markdown('<hr class="sidebar-sep">', unsafe_allow_html=True)
    st.markdown("""
    <div style="text-align:center;">
        <p style="font-size:0.7rem; color:#64748b !important; margin:0;">Geliştiren</p>
        <p style="font-size:0.85rem; font-weight:700; margin:0.2rem 0 0 0;">Ekrem Sekmen</p>
    </div>
    """, unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Filtreleme
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
st.markdown(f"""
<div class="page-title">
    <h1>Tekstil İplik Üretim Analiz Sistemi</h1>
    <p>{tarih_baslangic.strftime('%d.%m.%Y')} – {tarih_bitis.strftime('%d.%m.%Y')} &nbsp;|&nbsp; {len(df)} kayıt</p>
</div>
""", unsafe_allow_html=True)

if df.empty:
    st.warning("Seçilen filtrelere uygun veri bulunamadı.")
    st.stop()

# ──────────────────────────────────────────────
# Metrik Kartları (tek satır HTML)
# ──────────────────────────────────────────────
toplam_uretim = df["toplam_uretim"].sum()
ort_fire_orani = df["fire_orani"].mean()
ort_oee = df["oee"].mean() * 100
kritik_kayit = len(df[df["durum"] == "Kritik"])
toplam_ariza_dk = df["ariza_suresi"].sum()

st.markdown(f"""
<div class="kpi-row">
    <div class="kpi-card kpi-accent-blue">
        <p class="label">Toplam Üretim</p>
        <p class="val">{toplam_uretim:,.0f} kg</p>
        <p class="sub">{len(df)} üretim kaydı</p>
    </div>
    <div class="kpi-card kpi-accent-{"red" if ort_fire_orani > 5 else "green"}">
        <p class="label">Ort. Fire Oranı</p>
        <p class="val">%{ort_fire_orani:.2f}</p>
        <p class="sub">{"Yüksek — aksiyon gerekli" if ort_fire_orani > 5 else "Normal aralıkta"}</p>
    </div>
    <div class="kpi-card kpi-accent-green">
        <p class="label">Ortalama OEE</p>
        <p class="val">%{ort_oee:.1f}</p>
        <p class="sub">Hedef: %85</p>
    </div>
    <div class="kpi-card kpi-accent-red">
        <p class="label">Kritik Kayıt</p>
        <p class="val">{kritik_kayit}</p>
        <p class="sub">Fire oranı > %5</p>
    </div>
    <div class="kpi-card kpi-accent-amber">
        <p class="label">Toplam Arıza</p>
        <p class="val">{toplam_ariza_dk:,.0f} dk</p>
        <p class="sub">{toplam_ariza_dk / 60:.1f} saat</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Grafikler — Satır 1
# ──────────────────────────────────────────────
st.markdown('<p class="sec-title">Verimlilik Analizi</p>', unsafe_allow_html=True)
st.markdown('<p class="sec-sub">Makine bazlı OEE karşılaştırması ve günlük fire oranı trendi</p>', unsafe_allow_html=True)

graf_col1, graf_col2 = st.columns(2)

PLOT_LAYOUT = dict(
    plot_bgcolor="#ffffff",
    paper_bgcolor="#ffffff",
    font=dict(color="#1e293b", size=12),
    margin=dict(l=40, r=20, t=40, b=40),
    height=400,
)

with graf_col1:
    ozet = makine_bazli_ozet(df)
    renk_haritasi = {"Normal": "#22c55e", "Kritik": "#ef4444"}
    fig_oee = px.bar(
        ozet, x="makine_no", y="ortalama_oee",
        color="durum", color_discrete_map=renk_haritasi,
        text="ortalama_oee",
        labels={"makine_no": "Makine", "ortalama_oee": "OEE (%)"},
        title="Makine Bazlı OEE",
    )
    fig_oee.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_oee.update_layout(**PLOT_LAYOUT, yaxis_range=[0, 105])
    fig_oee.add_hline(y=85, line_dash="dash", line_color="#2563eb", annotation_text="Hedef %85")
    fig_oee.update_xaxes(showgrid=False, linecolor="#e2e8f0")
    fig_oee.update_yaxes(gridcolor="#f1f5f9", linecolor="#e2e8f0")
    st.plotly_chart(fig_oee, width="stretch")

with graf_col2:
    gunluk = df.groupby("tarih").agg(ort_fire=("fire_orani", "mean")).reset_index()
    fig_fire = px.line(
        gunluk, x="tarih", y="ort_fire",
        labels={"tarih": "Tarih", "ort_fire": "Fire Oranı (%)"},
        title="Günlük Fire Oranı Trendi",
        markers=True,
    )
    fig_fire.update_traces(line_color="#ef4444", fill="tozeroy", fillcolor="rgba(239,68,68,0.06)")
    fig_fire.add_hline(y=5, line_dash="dash", line_color="#d97706", annotation_text="Kritik Eşik %5")
    fig_fire.update_layout(**PLOT_LAYOUT)
    fig_fire.update_xaxes(showgrid=False, linecolor="#e2e8f0")
    fig_fire.update_yaxes(gridcolor="#f1f5f9", linecolor="#e2e8f0")
    st.plotly_chart(fig_fire, width="stretch")

# ──────────────────────────────────────────────
# Grafikler — Satır 2
# ──────────────────────────────────────────────
st.markdown('<p class="sec-title">Dağılım ve Bileşen Analizi</p>', unsafe_allow_html=True)
st.markdown('<p class="sec-sub">Üretim hattı dağılımı ve OEE bileşen detayları</p>', unsafe_allow_html=True)

graf_col3, graf_col4 = st.columns(2)

with graf_col3:
    hat_uretim = df.groupby("uretim_hatti")["toplam_uretim"].sum().reset_index()
    fig_pasta = px.pie(
        hat_uretim, values="toplam_uretim", names="uretim_hatti",
        color_discrete_sequence=["#2563eb", "#16a34a", "#d97706"],
        hole=0.5, title="Hatlara Göre Üretim Dağılımı",
    )
    fig_pasta.update_traces(textinfo="percent+label", textfont_size=12)
    fig_pasta.update_layout(**PLOT_LAYOUT)
    st.plotly_chart(fig_pasta, width="stretch")

with graf_col4:
    ort_k = df["kullanilabilirlik"].mean() * 100
    ort_p = df["performans"].mean() * 100
    ort_q = df["kalite"].mean() * 100

    fig_radar = go.Figure()
    fig_radar.add_trace(go.Scatterpolar(
        r=[ort_k, ort_p, ort_q, ort_k],
        theta=["Kullanılabilirlik", "Performans", "Kalite", "Kullanılabilirlik"],
        fill="toself", fillcolor="rgba(37,99,235,0.15)",
        line_color="#2563eb", line_width=2, name="Ortalama",
    ))
    fig_radar.add_trace(go.Scatterpolar(
        r=[85, 85, 85, 85],
        theta=["Kullanılabilirlik", "Performans", "Kalite", "Kullanılabilirlik"],
        fill="none", line_color="#e2e8f0", line_dash="dash", line_width=1, name="Hedef %85",
    ))
    fig_radar.update_layout(
        **PLOT_LAYOUT,
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor="#f1f5f9")),
        title="OEE Bileşen Analizi",
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
    )
    st.plotly_chart(fig_radar, width="stretch")

# ──────────────────────────────────────────────
# Anormallik Raporu
# ──────────────────────────────────────────────
rapor = anormallik_raporu(df)

st.markdown(f'<p class="sec-title">Anormallik Raporu ({len(rapor)} kayıt)</p>', unsafe_allow_html=True)
st.markdown('<p class="sec-sub">Fire oranı %5 üzerindeki kayıtlar — kritik seviye</p>', unsafe_allow_html=True)

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
        return ["background-color: #fef2f2; color: #991b1b; font-weight: 600"] * len(row)

    st.dataframe(
        rapor_goster.style.apply(satirlari_renklendir, axis=1),
        width="stretch",
        height=320,
    )

# ──────────────────────────────────────────────
# Excel Rapor İndirme
# ──────────────────────────────────────────────

def excel_olustur(df_tum, df_rapor, df_ozet):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        workbook = writer.book
        baslik_fmt = workbook.add_format({"bold": True, "bg_color": "#1E3A5F", "font_color": "#FFFFFF", "border": 1, "text_wrap": True, "valign": "vcenter", "align": "center"})
        normal_fmt = workbook.add_format({"border": 1, "valign": "vcenter"})
        kritik_fmt = workbook.add_format({"bg_color": "#FEE2E2", "font_color": "#991B1B", "bold": True, "border": 1, "valign": "vcenter"})
        sayi_fmt = workbook.add_format({"num_format": "#,##0.0", "border": 1, "valign": "vcenter"})
        kritik_sayi_fmt = workbook.add_format({"num_format": "#,##0.0", "bg_color": "#FEE2E2", "font_color": "#991B1B", "bold": True, "border": 1, "valign": "vcenter"})
        yuzde_fmt = workbook.add_format({"num_format": "0.00%", "border": 1, "valign": "vcenter"})
        kritik_yuzde_fmt = workbook.add_format({"num_format": "0.00%", "bg_color": "#FEE2E2", "font_color": "#991B1B", "bold": True, "border": 1, "valign": "vcenter"})

        # Sayfa 1
        s1 = "Tüm Üretim Verileri"
        cols1 = ["makine_no","uretim_hatti","tarih","vites_saati","toplam_uretim","fire_miktari","fire_orani","ariza_suresi","kullanilabilirlik","performans","kalite","oee","durum"]
        h1 = ["Makine No","Üretim Hattı","Tarih","Vites Saati (s)","Toplam Üretim (kg)","Fire Miktarı (kg)","Fire Oranı (%)","Arıza Süresi (dk)","Kullanılabilirlik","Performans","Kalite","OEE","Durum"]
        d1 = df_tum[cols1].copy()
        d1["tarih"] = d1["tarih"].dt.strftime("%Y-%m-%d")
        ws1 = workbook.add_worksheet(s1); writer.sheets[s1] = ws1
        for c, h in enumerate(h1): ws1.write(0, c, h, baslik_fmt)
        for r, (_, row) in enumerate(d1.iterrows(), 1):
            ik = row["durum"] == "Kritik"
            for c, v in enumerate(row):
                if c in {3,4,5,6,7}: ws1.write_number(r, c, float(v), kritik_sayi_fmt if ik else sayi_fmt)
                elif c in {8,9,10,11}: ws1.write_number(r, c, float(v), kritik_yuzde_fmt if ik else yuzde_fmt)
                else: ws1.write(r, c, v, kritik_fmt if ik else normal_fmt)
        for i, h in enumerate(h1): ws1.set_column(i, i, max(len(h)+4, 14))

        # Sayfa 2
        s2 = "Anormallik Raporu"
        cols2 = ["makine_no","uretim_hatti","tarih","toplam_uretim","fire_miktari","fire_orani","ariza_suresi","oee","durum"]
        h2 = ["Makine No","Üretim Hattı","Tarih","Toplam Üretim (kg)","Fire Miktarı (kg)","Fire Oranı (%)","Arıza Süresi (dk)","OEE","Durum"]
        d2 = df_rapor[cols2].copy()
        d2["tarih"] = d2["tarih"].dt.strftime("%Y-%m-%d")
        ws2 = workbook.add_worksheet(s2); writer.sheets[s2] = ws2
        for c, h in enumerate(h2): ws2.write(0, c, h, baslik_fmt)
        for r, (_, row) in enumerate(d2.iterrows(), 1):
            for c, v in enumerate(row):
                if c in {3,4,5,6}: ws2.write_number(r, c, float(v), kritik_sayi_fmt)
                elif c == 7: ws2.write_number(r, c, float(v), kritik_yuzde_fmt)
                else: ws2.write(r, c, v, kritik_fmt)
        for i, h in enumerate(h2): ws2.set_column(i, i, max(len(h)+4, 14))

        # Sayfa 3
        s3 = "Makine Özet"
        h3 = ["Makine No","Ort. OEE (%)","Ort. Fire (%)","Toplam Üretim (kg)","Toplam Fire (kg)","Toplam Arıza (dk)","Kayıt Sayısı","Durum"]
        ws3 = workbook.add_worksheet(s3); writer.sheets[s3] = ws3
        for c, h in enumerate(h3): ws3.write(0, c, h, baslik_fmt)
        for r, (_, row) in enumerate(df_ozet.iterrows(), 1):
            ik = row["durum"] == "Kritik"
            for c, v in enumerate(row):
                if c in {1,2,3,4,5,6}: ws3.write_number(r, c, float(v), kritik_sayi_fmt if ik else sayi_fmt)
                else: ws3.write(r, c, v, kritik_fmt if ik else normal_fmt)
        for i, h in enumerate(h3): ws3.set_column(i, i, max(len(h)+4, 14))

    buffer.seek(0)
    return buffer.getvalue()


ozet_df = makine_bazli_ozet(df)
rapor_df = anormallik_raporu(df)

st.markdown("---")
dl1, dl2 = st.columns([1, 3])
with dl1:
    excel_data = excel_olustur(df, rapor_df, ozet_df)
    st.download_button(
        label="📥 Excel Raporu İndir",
        data=excel_data,
        file_name="Uretim_Analiz_Raporu.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
    )
with dl2:
    st.caption(
        f"{len(df)} kayıt  ·  {len(rapor_df)} kritik  ·  {pd.Timestamp.now().strftime('%d.%m.%Y %H:%M')}"
    )

# Ham veri
with st.expander("Detaylı Veri Tablosu", expanded=False):
    st.dataframe(df, width="stretch", height=400)

# Footer
st.markdown("""
<div class="app-footer">
    <p>Üretim Analiz Sistemi v1.0 — Tasarım ve geliştirme: <strong>Ekrem Sekmen</strong></p>
    <div class="tech-pills">
        <span class="tech-pill">Python</span>
        <span class="tech-pill">Streamlit</span>
        <span class="tech-pill">Plotly</span>
        <span class="tech-pill">Pandas</span>
        <span class="tech-pill">SQLite</span>
        <span class="tech-pill">XlsxWriter</span>
    </div>
</div>
""", unsafe_allow_html=True)
