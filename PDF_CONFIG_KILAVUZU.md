# PDF Rapor Konfigürasyon Kılavuzu

Bu dosya (`pdf_config.json`) PDF raporunun içeriğini, grafik sırasını ve ara metinleri kontrol eder.

## Ana Ayarlar

### PDF Oluşturma (`pdf_olustur`)
- `true`: PDF raporu oluşturulur
- `false`: PDF raporu oluşturulmaz

### Dosya Ayarları
- `pdf_dosya_adi`: PDF dosya adı formatı (`{tarih}` otomatik değiştirilir)
- `font_ayarlari`: Font ayarları (Türkçe karakter desteği)
- `sayfa_ayarlari`: Sayfa boyutu ve kenar boşlukları

## Grafik Sırası (`grafik_sirasi`)

Grafiklerin PDF'teki sırası ve özellikleri:

```json
{
  "pattern": "vaka-tipi-dagilimi",
  "baslik": "Vaka Tipi Dağılımı",
  "aciklama": "Yeni vaka ve devreden vaka dağılımı",
  "sayfa_sonu": false
}
```

### Mevcut Grafik Pattern'ları:
- `vaka-tipi-dagilimi`: Yeni/Devreden vaka pasta grafiği
- `il-dagilimi`: İl içi/dışı pasta grafiği
- `vaka_durumu`: Nakil bekleyen/gerçekleşen/iptal vakalar
- `bekleme_threshold`: Bekleme süresi analizi
- `klinik-dagilim`: Klinik dağılımı
- `klinik_vaka_durum`: Klinik bazlı vaka durumu
- `klinik-bekleme`: Klinik bazlı bekleme süresi
- `iptal-nedenleri`: İptal nedenleri çubuk grafiği
- `iptal-eden-dagilimi`: İptal eden dağılımı
- `solunum-islemi-dagilimi`: Entübe/Non-entübe dağılımı

### Grafik Özellikleri:
- `pattern`: Dosya adında aranacak anahtar kelime
- `baslik`: PDF'te görünecek başlık
- `aciklama`: Grafik altında görünecek açıklama (isteğe bağlı)
- `sayfa_sonu`: Bu grafikten sonra sayfa sonu eklensin mi

## Ara Metinler (`ara_metinler`)

Belirli pozisyonlarda eklenen açıklama metinleri:

```json
{
  "pozisyon": "klinik_analiz_baslangici",
  "metin": "KLİNİK BAZLI DETAY ANALİZLER",
  "stil": "baslik"
}
```

### Pozisyon Türleri:
- `vaka_durumu_sonrasi`: Vaka durum grafiklerinden sonra
- `klinik_analiz_baslangici`: Klinik analizler başlamadan önce
- `klinik_vaka_durum_sonrasi`: Klinik vaka durum grafiklerinden sonra
- `iptal_analizleri_baslangici`: İptal analizleri başlamadan önce

### Stil Türleri:
- `ara_metin`: Normal açıklama metni
- `baslik`: Büyük başlık

## Giriş Sayfası (`giris_sayfasi`)

PDF'in ikinci sayfasında (kapaktan sonra) görünen özet bilgiler:

- `baslik.metin`: Giriş sayfası başlığı
- `kaynak_dosya`: Nakil bekleyen rapor dosyası formatı
- `aciklama`: Giriş sayfası açıklaması

## Ek Metinler (`ek_metinler`)

PDF sonunda eklenen genel bilgi metinleri:

- `pozisyon`: `sayfa_sonu` veya `son_sayfa`
- `metin`: Eklenecek metin

## Grafik Ayarları (`grafik_ayarlari`)

- `maksimum_grafik_per_sayfa`: Sayfa başına maksimum grafik sayısı
- `grafik_boyutu`: Grafiklerin boyutları
- `sayfa_sonu_otomatik`: Otomatik sayfa sonu eklensin mi

## Metin Stilleri (`metin_stilleri`)

Farklı metin türleri için stil ayarları:

- `ara_metin`: Ara açıklama metinleri
- `baslik`: Başlık metinleri
- `aciklama`: Grafik açıklamaları

Her stil için:
- `font_boyutu`: Yazı boyutu
- `renk`: Yazı rengi (hex kod)
- `hizalama`: Yazı hizalaması (sol, merkez, sag)

## Örnek Değişiklikler

### Grafik Sırasını Değiştirmek:
Grafik sırasını değiştirmek için `grafik_sirasi` array'inin elemanlarının sırasını değiştirin.

### Yeni Ara Metin Eklemek:
```json
{
  "pozisyon": "yeni_pozisyon",
  "metin": "Yeni açıklama metni",
  "stil": "ara_metin"
}
```

### Grafik Başlığını Değiştirmek:
İlgili grafik pattern'ının `baslik` değerini değiştirin.

### Sayfa Sonunu Kontrol Etmek:
Grafik pattern'ının `sayfa_sonu` değerini `true` veya `false` yapın.

## Dikkat Edilecekler

1. JSON formatına uygun syntax kullanın
2. Türkçe karakterler desteklenir
3. Pattern'lar dosya adlarında aranır
4. Grafik bulunmazsa o kısım atlanır
5. Config hatası durumunda varsayılan ayarlar kullanılır
