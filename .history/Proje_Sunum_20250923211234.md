# Nakil Vaka Talep Analiz ve Raporlama Sistemi

## 1. Giriş

**Amaç:** Bu proje, "Nakil Vaka Talepleri" raporlarının manuel olarak işlenmesi sürecini otomatize etmek, bu verilerden anlamlı istatistikler ve görseller üreterek karar alma süreçlerini desteklemek amacıyla geliştirilmiştir. Sistem, günlük olarak alınan Excel raporlarını otomatik olarak işler, analiz eder ve kapsamlı PDF raporları oluşturur.

**Çözülen Problem:**
*   **Manuel Raporlamanın Yükü:** Günlük raporların elle incelenmesi, istatistiklerin hesaplanması ve sunum hazırlanması zaman alıcı ve hataya açık bir süreçtir.
*   **Veri Görselleştirme Eksikliği:** Ham verilerden anlık durum ve trendleri takip etmek zordur. Görselleştirme, verinin daha anlaşılır olmasını sağlar.
*   **Standardizasyon:** Otomatik sistem, her gün aynı standartlarda ve formatlarda raporlar üreterek tutarlılık sağlar.

---

## 2. Sistem Mimarisi ve İşleyişi

Sistem, verinin ham halden nihai rapora dönüşmesine kadar modüler bir yapıda çalışır. İş akışı aşağıdaki gibidir:

```mermaid
graph TD
    A[Excel Raporu (.xls)] --> B{1. Veri İşleme Modülü};
    B --> C[Temizlenmiş & Zenginleştirilmiş Veri (.parquet)];
    C --> D{2. Analiz Motoru};
    D --> E[İstatistiksel Sonuçlar (.json)];
    E --> F{3. Raporlama ve Görselleştirme};
    F --> G[Grafikler (.png)];
    F --> H[İstatistik Özeti (.pdf)];
    G --> H;
    H --> I[Nihai Birleştirilmiş Rapor (.pdf)];
```

1.  **Veri Alımı:** Günlük `Nakil Vaka Talepleri Raporu.xls` dosyası sisteme girdi olarak verilir.
2.  **Veri İşleme:** Python tabanlı script, Excel dosyasını okur, veriyi temizler, standartlaştırır ve `vaka tipi` (Yeni, Devreden), `süre` gibi yeni ve anlamlı sütunlar ekler. Bu işlenmiş veri, hızlı erişim için `.parquet` formatında saklanır.
3.  **Analiz:** Sistem, işlenmiş veri üzerinden kapsamlı istatistikler hesaplar.
4.  **Görselleştirme:** Hesaplanan analiz sonuçları, `Matplotlib` ve `Seaborn` kütüphaneleri kullanılarak çeşitli grafiklere (pasta, çubuk vb.) dönüştürülür.
5.  **PDF Raporlama:** Hem analiz özeti hem de oluşturulan grafikler, `ReportLab` kütüphanesi ile profesyonel bir PDF dokümanında birleştirilir.

---

## 3. Modüller ve Temel Kabiliyetler

### 3.1 Veri İşleme Modülü
Bu modül, ham verinin analize hazır hale getirilmesinden sorumludur.
*   **Veri Okuma:** `.xls` formatındaki Excel dosyalarını okur.
*   **Sütun Standardizasyonu:** Türkçe karakterler ve boşluklar içeren sütun isimlerini programatik olarak kullanılabilir hale getirir.
*   **Veri Zenginleştirme:**
    *   **Vaka Tipi:** Her bir vakanın `Yeni Vaka` mı yoksa `Devreden Vaka` mı olduğunu belirler.
    *   **Süre Hesaplama:** Vaka açılış, yer bulunma ve kapanış zamanları arasındaki farkları (saat, gün olarak) hesaplar.
    *   **İl Grubu:** Vakaları `İl İçi` ve `İl Dışı` olarak kategorize eder.

### 3.2 Analiz Motoru
Sistemin kalbi olan bu modül, işlenmiş veriden istatistiksel çıktılar üretir.
*   **Genel İstatistikler:** Toplam talep, il içi/dışı talep sayıları.
*   **Yoğun Bakım Analizi:** Toplam yoğun bakım talebi, entübe/non-entübe hasta sayıları.
*   **Süre Analizleri:** Ortalama yer bulma süresi, en hızlı/en yavaş yer bulunan vakalar, halen bekleyen vakaların ortalama bekleme süresi.
*   **Klinik Performansı:** En hızlı ve en yavaş yer bulan ilk 3 klinik.
*   **İptal Analizleri:** İptal nedenlerinin ve iptal eden kurumların dağılımı.

### 3.3 Raporlama ve Görselleştirme
Bu modül, analiz sonuçlarını son kullanıcıya sunar.
*   **Grafik Üretimi:** Aşağıdakiler dahil olmak üzere 20'den fazla farklı grafik otomatik olarak oluşturulur:
    *   Vaka Durumu Dağılımı (Pasta Grafik)
    *   Bekleme Süresi Eşiği Analizi (Pasta Grafik)
    *   Klinik Dağılımları (Çubuk Grafik)
    *   İl Dağılımı (Pasta Grafik)
    *   İptal Nedenleri (Yatay Çubuk Grafik)
*   **PDF Oluşturma:**
    *   **İstatistik Özeti Sayfası:** Tüm önemli sayısal verilerin özetlendiği bir giriş sayfası.
    *   **Grafik Sayfaları:** Oluşturulan tüm grafiklerin 2x2 grid düzeninde sayfalara yerleştirilmesi.
    *   **Kapak Sayfası:** Kurumsal kimliğe uygun, dinamik tarih bilgisi içeren bir kapak.

---

## 4. Örnek Rapor Çıktıları

Sistem tarafından üretilen nihai PDF raporu aşağıdaki bölümlerden oluşur:

#### Örnek İstatistik Sayfası
*(Buraya `nakil_analiz_raporu_2025-09-22.pdf` dosyasının ilk sayfasının ekran görüntüsü eklenebilir)*

> **GENEL İSTATİSTİKLER**
> • Toplam Nakil Bekleyen Talep: 41
> • İl İçi Talep: 33
> • İl Dışı Talep: 8
>
> **SÜRE ANALİZLERİ**
> • Ortalama yer bulma süresi: 2.2 saat
> ...

#### Örnek Grafik Sayfası
*(Buraya `nakil_analiz_raporu_2025-09-22.pdf` dosyasının grafik içeren bir sayfasının ekran görüntüsü eklenebilir)*

> Sistem, analiz edilen her kategori için (örn: Yeni Vakalar, Devreden Vakalar, İl İçi, Bütün Bölgeler) ayrı ayrı grafikler üreterek detaylı bir görsel analiz sunar. Grafikler, daha kolay okunabilirlik için sayfalara 2x2'lik bir düzende yerleştirilir.

---

## 5. Kullanılan Teknolojiler

*   **Programlama Dili:** Python 3
*   **Veri Analizi:** Pandas, NumPy
*   **Veri Okuma:** `xlrd`
*   **Görselleştirme:** Matplotlib, Seaborn
*   **PDF Raporlama:** ReportLab
*   **Veri Depolama:** PyArrow (Parquet formatı için)

---

## 6. Sonuç ve Gelecek Geliştirmeler

Bu otomasyon sistemi, nakil vaka yönetimi sürecinde veriye dayalı karar almayı hızlandıran, operasyonel verimliliği artıran ve standart raporlama sağlayan güçlü bir araçtır.

**Potansiyel Geliştirmeler:**
*   **Web Arayüzü:** Kullanıcıların tarih aralığı seçerek veya filtreler uygulayarak kendi raporlarını oluşturabileceği interaktif bir web arayüzü.
*   **Veritabanı Entegrasyonu:** Verilerin Excel yerine doğrudan bir veritabanından okunması.
*   **Gelişmiş Analizler:** Makine öğrenmesi modelleri ile gelecekteki vaka yoğunluğunu tahmin etme.
