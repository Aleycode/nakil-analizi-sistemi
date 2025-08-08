# Kapak Sayfası Konfigürasyon Dosyası

Bu dosya (`assets/kapak_config.json`) kapak sayfasındaki metinlerin, boyutların ve konumların ayarlanması için kullanılır.

## Konfigürasyon Ayarları

### Başlık (`baslik`)
- `metin`: Ana başlık metni
- `font_boyutu`: Yazı boyutu (varsayılan: 24)
- `renk`: Yazı rengi (hex kod, örnek: "#2c3e50")
- `konum`: Yazı konumu ("sol", "merkez", "sag")
- `ust_bosluk`: Üstten boşluk (inch cinsinden)
- `alt_bosluk`: Alttan boşluk (inch cinsinden)

### Alt Başlık (`alt_baslik`)
- Başlık ile aynı parametreler
- Varsayılan font_boyutu: 16

### Kurum (`kurum`)
- Başlık ile aynı parametreler
- Varsayılan font_boyutu: 18

### Logo (`logo`)
- `dosya_adi`: Logo dosya adı (assets klasöründe)
- `genislik`: Logo genişliği (inch cinsinden)
- `yukseklik`: Logo yüksekliği (inch cinsinden)
- `alt_bosluk`: Logo altından boşluk

### Sayfa Ayarları (`sayfa_ayarlari`)
- `kenar_boslugu`: Sayfa kenar boşluğu (inch cinsinden)
- `sayfa_boyutu`: Sayfa boyutu ("A4", "A3", "Letter")

### Tarih Ayarları
- `tarih_goster`: Kapak sayfasında tarih gösterilsin mi (false önerilir)
- Ana raporda tarih otomatik olarak giriş sayfasında gösterilir

## Kullanım

Kapak sayfasını yeniden oluşturmak için:

```bash
python kapak_sayfasi_olusturucu.py
```

Bu komut `assets/kapak.pdf` dosyasını güncelleyecektir.

## Renk Kodları

Önerilen renk kodları:
- Ana başlık: `#2c3e50` (koyu mavi)
- Alt başlık: `#34495e` (gri-mavi)
- Kurum: `#2c3e50` (koyu mavi)
- Tarih: `#7f8c8d` (açık gri)

## Örnek Değişiklikler

Başlığı değiştirmek için:
```json
{
  "baslik": {
    "metin": "YENİ BAŞLIK METNİ",
    "font_boyutu": 26,
    "renk": "#e74c3c"
  }
}
```

Logo boyutunu ayarlamak için:
```json
{
  "logo": {
    "genislik": 3.0,
    "yukseklik": 3.0
  }
}
```
