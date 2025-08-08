# Nakil Z-Raporu Analiz Sistemi

Bu proje hasta nakil işlemleri için Excel dosyalarını işleyip parquet formatına dönüştüren ve kapsamlı analiz eden bir Python uygulamasıdır.

## 🏗️ Modüler Mimari

Proje, bakım kolaylığı ve genişletilebilirlik için modüler bir yapıda tasarlanmıştır:

### Ana Modüller

1. **`veri_isleme.py`** - Veri okuma, filtreleme ve sınıflandırma
   - Excel/Parquet dosyası okuma
   - Zaman aralığı filtreleme
   - Vaka tipi belirleme (Yeni/Devreden/Analiz Dışı)
   - İl bazında gruplama

2. **`analiz_motoru.py`** - Ana analiz mantığı ve istatistikler
   - Vaka durumu analizi
   - Bekleme süresi hesaplamaları
   - Threshold analizleri
   - Genel istatistik hesaplamaları

3. **`grafik_olusturucu.py`** - Tüm grafik oluşturma işlemleri
   - Pasta grafikleri
   - Threshold grafikleri
   - İptal nedenleri çubuk grafikleri
   - Grafik konfigürasyon yönetimi

4. **`klinik_analizcisi.py`** - Klinik analizi özel işlemleri
   - Klinik filtreleme
   - Klinik dağılım analizi
   - Klinik bazında grafik oluşturma
   - Vaka durum analizleri

5. **`nakil_analyzer.py`** - Ana koordinatör sınıf
   - Diğer modülleri koordine eder
   - Kapsamlı analiz yöneticisi
   - Geriye uyumluluk sağlar

6. **`data_processor.py`** - Excel veri işleme (mevcut)
7. **`config.py`** - Konfigürasyon yönetimi (mevcut)
8. **`main.py`** - Ana uygulama giriş noktası (mevcut)

## Kurulum

1. Projeyi klonlayın veya indirin

2. Sanal ortam oluşturun ve aktifleştirin:

```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
```

3. Gereksinimları yükleyin:

```bash
pip install -r requirements.txt
```

## Kullanım

### Günlük Veri İşleme

```bash
python main.py --process-daily dosya.xls
```

### Veri Durumu Kontrolü

```bash
python main.py --status
```

### Tarih Aralığı Analizi

```bash
python main.py --analyze --start-date 2025-01-01 --end-date 2025-01-31
```

### Detaylı Analiz (Grafik ve Rapor ile)

```bash
python main.py --analyze --start-date 2025-01-01 --end-date 2025-01-31 --detailed
```

### Trend Analizi

```bash
python main.py --trend sutun_adi --days 30
```

### Nakil Analizi (Özel)

```bash
python main.py --nakil-analysis
```

### Nakil Analizi (Tarih Aralığı ile)

```bash
python main.py --nakil-analysis --start-date 2025-01-01 --end-date 2025-01-31
```

### Günlük Nakil Analizi (Yeni Vaka vs Devreden Vaka)

```bash
python main.py --daily-analysis                           # Bugün için
python main.py --daily-analysis --analysis-date 2025-08-01  # Belirli gün için
```

## Test Etme

Test verisi oluşturmak için:

```bash
python create_test_data.py          # Genel test verisi
python create_nakil_test_data.py    # Nakil-özel test verisi
```

Test verisini işlemek için:

```bash
python main.py --process-daily data/raw/test_veri.xlsx
python main.py --process-daily data/raw/nakil_test_veri.xlsx  # Nakil verisi
```

## Dosya Yapısı

```
nakil_z_raporu/
├── main.py                    # Ana uygulama dosyası
├── data_processor.py          # Excel okuma ve parquet dönüştürme modülü
├── analyzer.py                # Veri analizi modülü
├── config.py                  # Konfigürasyon ayarları
├── create_test_data.py        # Test verisi oluşturma scripti
├── requirements.txt           # Python paket gereksinimleri
├── .gitignore                 # Git ignore dosyası
├── data/                      # Veri dosyaları klasörü
│   ├── raw/                   # Ham Excel dosyaları
│   ├── processed/             # İşlenmiş parquet dosyaları
│   └── reports/               # Günlük ve analiz raporları
└── .vscode/                   # VS Code görev tanımları
    └── tasks.json
```

## Çıktı Dosyaları

### Parquet Dosyaları
- `ana_veri.parquet`: Tüm geçmiş verilerin birleştirilmiş hali
- `gunluk_veri_YYYYMMDD.parquet`: Günlük işlenen veriler

### Rapor Dosyaları
- `gunluk_rapor_YYYY-MM-DD.json`: Günlük özet raporu
- `detayli_analiz_başlangıç_bitiş.json`: Detaylı analiz raporu
- `trend_sutun_YYYYMMDD.png`: Trend analizi grafiği
- `korelasyon_başlangıç_bitiş.png`: Korelasyon matrisi
- `gunluk_trend_başlangıç_bitiş.png`: Günlük trend grafiği

## VS Code Görevleri

Proje VS Code görev tanımları ile gelir. `Ctrl+Shift+P` ile komut paletini açıp "Tasks: Run Task" seçerek görevleri çalıştırabilirsiniz.

## Teknolojiler

- **Python 3.12+**
- **xlrd 1.2.0**: .xls dosyaları için
- **openpyxl**: .xlsx dosyaları için
- **pandas**: Veri manipülasyonu
- **pyarrow**: Parquet format desteği
- **matplotlib & seaborn**: Veri görselleştirme
- **numpy**: Sayısal hesaplamalar
