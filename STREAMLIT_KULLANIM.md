# Nakil Z Raporu Analiz Sistemi - Streamlit Kullanım Kılavuzu

Bu belge, Nakil Z Raporu Analiz Sistemi'nin Streamlit web arayüzünün nasıl kullanılacağını açıklar.

## Başlangıç

Streamlit uygulamasını çalıştırmak için:

```bash
# Sanal ortamı etkinleştir
source .venv/bin/activate  # Linux/macOS
# VEYA
.\.venv\Scripts\activate  # Windows

# Streamlit uygulamasını başlat
streamlit run streamlit_app_new.py
```

Uygulama tarayıcınızda otomatik olarak açılacaktır (http://localhost:8501).

## Kullanım Kılavuzu

### Ana Sayfa

Ana sayfa, uygulamanın genel özelliklerine ve mevcut sistem durumuna genel bir bakış sunar:

- **Özellikler**: Sistemin temel özellikleri
- **Sistem Durumu**: Ham veri, işlenmiş veri ve raporların sayısal durumu
- **Son Raporlar**: En son oluşturulan rapor gösterilir

### Excel Veri İşleme

Bu sayfa, Excel dosyalarının işlenmesi ve parquet formatına dönüştürülmesi için kullanılır:

1. Mevcut Excel dosyalarından birini seçin veya yeni bir dosya yükleyin
2. Seçilen dosyayı önizleyin
3. "Dosyayı İşle" butonuna tıklayarak dosyayı işleyin
4. İşlem sonuçları ekranda gösterilecektir

### Nakil Analizi

Bu sayfa, işlenmiş veriler üzerinde analiz yapmak için kullanılır:

1. Analiz edilecek tarihi seçin
2. "Günlük Rapor Görüntüle" ile mevcut raporları görüntüleyin
3. "Yeni Analiz Çalıştır" ile seçilen tarih için yeni bir analiz başlatın
4. Analiz sonuçlarını, grafikleri ve PDF raporunu görüntüleyin

### Rapor Arşivi

Bu sayfa, oluşturulmuş tüm raporlara erişim sağlar:

1. Tarih aralığı seçin
2. Görüntülemek istediğiniz raporu seçin
3. Grafikler, PDF raporu ve JSON verileri sekmelerinden istediğinizi görüntüleyin

## Dosya Yapısı

Streamlit uygulaması aşağıdaki ana proje dosyalarını kullanır:

- `streamlit_app_new.py`: Ana Streamlit uygulaması
- `test_streamlit.py`: Basit test uygulaması
- `main.py`: Ana işlem komutları için kullanılan CLI uygulaması

## Sorun Giderme

Uygulama çalışmazsa veya hatalarla karşılaşırsanız:

1. Sanal ortamın etkin olduğundan emin olun
2. Streamlit'in kurulu olduğunu kontrol edin (`pip list | grep streamlit`)
3. Gerekli tüm bağımlılıkların yüklü olduğunu kontrol edin (`pip install -r requirements.txt`)
4. Proje klasör yapısının beklenen şekilde olduğunu kontrol edin

## Notlar

- Uygulamanın bazı özellikleri, main.py üzerinden çalıştırılan komutları kullanır
- PDF gösterimi için tarayıcınızın PDF görüntüleme yeteneğine sahip olması gerekir
- Büyük veri setleri için işlemler biraz zaman alabilir