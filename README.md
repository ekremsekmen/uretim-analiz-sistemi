# 🏭 Tekstil İplik Üretim Analiz Sistemi

Tekstil iplik üretim hatlarından gelen verileri **SQL veritabanından** çeken, **OEE (Overall Equipment Effectiveness)** analizi yapan, kritik makineleri tespit eden ve sonuçları hem **interaktif web dashboard** hem de **formatlanmış Excel raporu** olarak sunan bir karar destek sistemidir.

---

## 🎯 Projenin Amacı

Üretim sahalarında manuel olarak yapılan veri toplama, analiz etme ve raporlama süreçlerini **otomatize etmek**. Sistem sayesinde:

- Farklı üretim hatlarından gelen veriler tek merkezde toplanır
- OEE hesaplaması otomatik yapılır (Kullanılabilirlik × Performans × Kalite)
- Fire oranı %5'i aşan makineler **Kritik** olarak işaretlenir
- Tek tıkla formatlanmış Excel raporu indirilebilir

---

## 📸 Ekran Görüntüleri

### Dashboard Genel Görünüm
> Metrik kartları, filtreleme paneli ve interaktif grafikler

### Makine Bazlı OEE Analizi
> Hedef OEE çizgisiyle birlikte her makinenin verimlilik karşılaştırması

### Anormallik Raporu
> Fire oranı kritik seviyedeki kayıtlar kırmızıyla işaretlenir

### Excel Rapor Çıktısı
> 3 sayfalık, formatlanmış, kritik satırları kırmızıyla vurgulanan profesyonel rapor

---

## 🛠️ Teknik Altyapı

| Bileşen | Teknoloji | Açıklama |
|---------|-----------|----------|
| **Veritabanı** | SQLite3 | Üretim verilerinin saklanması |
| **Veri Analizi** | Pandas | OEE hesaplama, gruplama, filtreleme |
| **Dashboard** | Streamlit | İnteraktif web arayüzü |
| **Grafikler** | Plotly | Sütun, çizgi, pasta ve radar grafikleri |
| **Raporlama** | XlsxWriter | Formatlanmış Excel çıktısı |
| **Dil** | Python 3 | Tüm sistem |

---

## 📊 OEE Hesaplama Formülü

```
OEE = Kullanılabilirlik × Performans × Kalite

Kullanılabilirlik = (Planlı Süre − Arıza Süresi) / Planlı Süre
Performans        = Gerçek Üretim / Teorik Kapasite
Kalite            = (Toplam Üretim − Fire) / Toplam Üretim
```

---

## 🚀 Kurulum ve Çalıştırma

```bash
# 1. Projeyi klonla
git clone https://github.com/KULLANICI_ADIN/uretim-analiz-sistemi.git
cd uretim-analiz-sistemi

# 2. Sanal ortam oluştur
python3 -m venv venv
source venv/bin/activate

# 3. Bağımlılıkları kur
pip install -r requirements.txt

# 4. Uygulamayı başlat
streamlit run app.py
```

Uygulama otomatik olarak `http://localhost:8501` adresinde açılır.

---

## 📁 Proje Yapısı

```
uretim-analiz-sistemi/
├── app.py                  # Streamlit dashboard (ana uygulama)
├── analiz.py               # OEE hesaplama ve anormallik raporu modülü
├── veritabani_olustur.py   # SQLite veritabanı oluşturucu
├── requirements.txt        # Python bağımlılıkları
├── uretim.db               # SQLite veritabanı (otomatik oluşur)
└── README.md               # Bu dosya
```

---

## 💡 Geliştirme Potansiyeli

Bu sistem demo amaçlı SQLite ile çalışmaktadır. Gerçek bir üretim ortamında:

- **SQL Server / PostgreSQL** bağlantısıyla canlı veriye geçilebilir
- **Zamanlayıcı (scheduler)** ile otomatik rapor e-posta gönderilebilir
- **Makine öğrenmesi** ile arıza tahmini eklenebilir
- **ERP entegrasyonu** ile stok ve maliyet analizi yapılabilir

---

*Python ile geliştirilmiştir.*
