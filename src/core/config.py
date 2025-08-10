"""
Konfigürasyon ayarları
"""

import os
from pathlib import Path

# Proje kök dizini (src/core klasöründen 2 seviye yukarı)
PROJE_KOK = Path(__file__).parent.parent.parent

# Veri dizinleri
VERI_DIZIN = PROJE_KOK / "data"
HAM_VERI_DIZIN = VERI_DIZIN / "raw"
ISLENMIŞ_VERI_DIZIN = VERI_DIZIN / "processed"
RAPOR_DIZIN = VERI_DIZIN / "reports"

# Excel dosya ayarları
EXCEL_MOTOR = "xlrd"  # xlrd 1.2.0 için
DESTEKLENEN_FORMATLAR = [".xls", ".xlsx"]

# Parquet ayarları
PARQUET_MOTOR = "pyarrow"
PARQUET_SIKISTIRMA = "snappy"

# Veri dosya yolu
VERI_DOSYA_YOLU = ISLENMIŞ_VERI_DIZIN / "ana_veri.parquet"

# Tarih ayarları
TARIH_FORMATI = "%Y-%m-%d"
TARIH_KOLON_ADI = "tarih"

# Excel tarih formatı ayarları
EXCEL_TARIH_FORMATI = "dd-mm-yyyy hh:mm"  # Excel'de gösterilecek tarih formatı
EXCEL_TARIH_SUTUNLARI = [  # Excel'de tarih formatı uygulanacak sütunlar
    "talep tarihi",
    "oluşturma tarihi",
    "yer aramaya başlama tarihi",
    "yer bulunma tarihi",
    "ekip talep tarihi",
    "ekip belirlenme tarihi",
    "vakanın ekibe veriliş tarihi",
]

# Log ayarları
LOG_SEVIYE = "ERROR"
LOG_DOSYA = PROJE_KOK / "app.log"

# Analiz ayarları
VARSAYILAN_GRAFIK_BOYUTU = (12, 8)
VARSAYILAN_DPI = 300

# Nakil verisi sütun tanımları
NAKIL_SUTUNLARI = {
    "nakil_tipi": "Nakil Tipi",
    "talep_kaynagi": "Talep Kaynağı",
    "vaka_sorumlusu": "Vaka Sorumlusu",
    "konsultan_hekim": "Konsültan Hekim",
    "il": "İl",
    "ilce": "İlçe",
    "nakil_talep_eden_hastane": "Nakil Talep Eden Hastane",
    "bulundugu_klinik": "Bulunduğu Klinik",
    "hasta_uyruk": "Hasta Uyruk",
    "yas": "Yaş",
    "solunum_durumu": "Solunum Durumu",
    "solunum_islemi": "Solunum İşlemi",
    "sevk_nedeni": "Sevk Nedeni",
    "nakledilmesi_istenen_klinik": "Nakledilmesi İstenen Klinik",
    "durum": "Durum",
    "nakil_durumu": "Nakil Durumu",
    "kabul_eden_hastane": "Kabul Eden Hastane",
    "kabul_eden_klinik": "Kabul Eden Klinik",
    "iptal_nedeni": "İptal Nedeni",
    "iptal_eden": "İptal Eden",
    "askom_karari": "ASKOM Kararı ile Yerleştirildi",
    "ekip_talep_durumu": "Ekip Talep Durumu",
    "ekip_oncelik_durumu": "Ekip Öncelik Durumu",
    "talep_tarihi": "Talep Tarihi",
    "olusturma_tarihi": "Oluşturma Tarihi",
    "bekleme_suresi": "Bekleme Süresi",
    "yer_aramaya_baslama_tarihi": "Yer Aramaya Başlama Tarihi",
    "yer_bulunma_tarihi": "Yer Bulunma Tarihi",
    "ekip_talep_tarihi": "Ekip Talep Tarihi",
    "ekip_belirlenme_tarihi": "Ekip Belirlenme Tarihi",
    "vakanin_ekibe_verilis_tarihi": "Vakanın Ekibe Veriliş Tarihi",
}

# Analiz için önemli sütunlar
TARIH_SUTUNLARI = [
    "Talep Tarihi",
    "Oluşturma Tarihi",
    "Yer Aramaya Başlama Tarihi",
    "Yer Bulunma Tarihi",
    "Ekip Talep Tarihi",
    "Ekip Belirlenme Tarihi",
    "Vakanın Ekibe Veriliş Tarihi",
]

SAYISAL_SUTUNLAR = ["Yaş", "Bekleme Süresi"]

KATEGORIK_SUTUNLAR = [
    "Nakil Tipi",
    "Talep Kaynağı",
    "İl",
    "İlçe",
    "Hasta Uyruk",
    "Solunum Durumu",
    "Durum",
    "Nakil Durumu",
]

# Dashboard için KPI tanımları
KPI_TANIMLARI = {
    "toplam_nakil_sayisi": "Toplam Nakil Sayısı",
    "basarili_nakil_orani": "Başarılı Nakil Oranı",
    "ortalama_bekleme_suresi": "Ortalama Bekleme Süresi (Saat)",
    "il_bazinda_dagilim": "İl Bazında Dağılım",
    "nakil_tipi_dagilimi": "Nakil Tipi Dağılımı",
    "yas_grubu_analizi": "Yaş Grubu Analizi",
}

# Klinik analizi filtre ayarları
KLINIK_ANALIZ_AYARLARI = {
    # En çok giriş olan kaç klinik alınacak (gerisi filtrelenecek)
    "en_cok_klinik_sayisi": {
        "aktif": True,  # Filtreyi aktif/pasif yapma
        "deger": 7,  # Default 7 klinik
    },
    # Minimum giriş sayısı barajı (altındakiler filtrelenecek)
    "minimum_giris_baraj": {
        "aktif": True,  # Filtreyi aktif/pasif yapma
        "deger": 10,  # Default 10'dan az giriş olanlar silinecek
    },
}

# Klinik sütun adı tanımı
KLINIK_SUTUN_ADI = "nakledilmesi i̇stenen klinik"

# Program başlangıç ayarları
PROGRAM_AYARLARI = {
    # Eski verileri otomatik silme (processed ve reports klasörleri)
    # Default: True - başlangıçta eski veriler silinir
    "eski_verileri_sil": True,
}

# Otomatik analiz ayarları
OTOMATIK_ANALIZ_AYARLARI = {
    # Günlük işlem sonrası otomatik nakil analizi
    "gunluk_islem_sonrasi_analiz": True,  # Default: True
    # Hangi analizlerin yapılacağı
    "dun_analizi": True,  # Dün analizi (dün 08:00 - bugün 08:00)
    "bugun_analizi": True,  # Bugün analizi (bugün 08:00 - yarın 08:00)
}

# Veri düzenleme ayarları
VERI_DUZENLEME_AYARLARI = {
    # "Yeni Talep" durumunu "Yer Aranıyor" olarak değiştir
    "yeni_talep_yer_araniyor_donusum": True,  # Default: True
    # Klinik adı dönüştürmeleri (her şeyin en başında yapılır)
    "klinik_adi_donusturmeler": {
        "aktif": True,  # Dönüştürme işlemini aktif/pasif yapma
        "donusumler": {
            "ANESTEZIYOLOJI VE REANIMASYON": "GENEL YOĞUN BAKIM",
            "ANESTEZİ VE REANİMASYON YOĞUN BAKIM": "GENEL YOĞUN BAKIM",
            "GÖĞÜS HASTALIKLARI": "KORONER YOĞUN BAKIM",
            "ÇOCUK YOĞUN BAKIMI": "YENİDOĞAN YOĞUN BAKIM",
            # Buraya yeni klinik dönüştürmeleri ekleyebilirsiniz
            # "ESKİ KLİNİK ADI": "YENİ KLİNİK ADI",
        },
    },
    # Solunum işlemi dönüştürmeleri
    "solunum_islemi_donusturmeler": {
        "aktif": True,  # Dönüştürme işlemini aktif/pasif yapma
        "donusumler": {
            "NON-INVASIVE": "Non-Entübe",
            "SPONTAN": "Non-Entübe",
            # Buraya yeni solunum işlemi dönüştürmeleri ekleyebilirsiniz
            # "ESKİ SOLUNUM İŞLEMİ": "YENİ SOLUNUM İŞLEMİ",
        },
    },
}

# Grafik ayarları - Her grafik türü için ayrı kontrol
GRAFIK_AYARLARI = {
    # Klinik grafikleri
    "klinik_pasta_grafik": True,  # Klinik dağılım pasta grafiği
    "klinik_vaka_durum_grafik": True,  # Klinik vaka durum bar grafiği
    "klinik_bekleme_grafik": False,  # Klinik bekleme süreleri grafiği (pasif)
    # Genel grafikler (diğer mevcut grafikler için)
    "genel_grafik": True,  # Diğer tüm grafikler için genel kontrol
    # Yeni pasta grafikleri
    "vaka_tipi_pasta_grafigi": True,  # Vaka tipi dağılımı (Yeni/Devreden)
    "il_dagilim_pasta_grafigi": True,  # İl dağılımı (İl İçi/İl Dışı)
    "iptal_eden_cubuk_grafigi": False,  # Devre dışı
    "solunum_islemi_pasta_grafigi": True,  # Solunum işlemi dağılımı
    "iptal_nedenleri_grafik": True,  # İptal nedenleri çubuk grafiği
    # Metin raporları
    "nakil_bekleyen_raporu": True,  # Nakil bekleyen talep raporu (txt)
}

# Grafik oluşturma ayarları
GRAFIK_AYARLARI = {
    # Genel grafikler
    "nakil_tipi_dagilimi": True,  # Nakil tipi dağılımı
    "il_bazli_dagilim": True,  # İl bazlı dağılım
    "gunluk_trend": True,  # Günlük trend
    "vaka_tipi_dagilimi": True,  # Vaka tipi dağılımı
    "bekleme_suresi_analizi": True,  # Bekleme süresi analizi
    # Klinik grafikler
    "klinik_pasta_grafigi": True,  # Klinik dağılım pasta
    "klinik_vaka_durum_grafigi": True,  # Klinik vaka durum bar
    "klinik_bekleme_grafigi": False,  # Klinik bekleme süresi (pasif)
    "iptal_nedenleri_grafik": True,  # İptal nedenleri çubuk grafiği
    # Zaman serisi grafikler
    "saatlik_dagilim": True,  # Saatlik dağılım
    "haftalik_trend": True,  # Haftalık trend
}

# Grafik görünüm ayarları
GRAFIK_GORUNUM_AYARLARI = {
    # Tarih gösterimi
    "tarih_goster": True,  # Grafiklerde tarih gösterilsin mi
    # Tarih konumu: "alt_sag", "alt_sol", "ust_sag", "ust_sol"
    "tarih_konum": "alt_sag",
    "tarih_boyut": 8,  # Tarih yazı boyutu
    # Pasta grafik ayarları
    # Format: "isim", "yuzde", "sayi", "isim_yuzde", "isim_sayi",
    # "isim_yuzde_sayi", "isim_yuzde_sayi_yanli"
    "pasta_etiket_format": "isim_yuzde_sayi_yanli",
}

# Grafik başlık şablonları
GRAFIK_BASLIK_SABLONLARI = {
    # Klinik grafikleri
    "klinik_dagilim": "Klinik Dağılımı - {grup_adi} - {vaka_tipi}",
    "klinik_bekleme": "Klinik Bekleme Süreleri - {grup_adi} - {vaka_tipi}",
    "klinik_vaka_durum": "Klinik Vaka Durumu - {grup_adi} - {vaka_tipi}",
    "bekleme_threshold": "Bekleme Süresi Dağılımı - {grup_adi} - {vaka_tipi}",
    "vaka_durumu": "Vaka Durumu - {grup_adi} - {vaka_tipi}",
    # Yeni pasta grafikleri
    "vaka_tipi_dagilimi": "Vaka Tipi Dağılımı - {grup_adi}",
    "il_dagilimi": "İl Dağılımı - Bütün Vakalar",
    # Genel formatlar
    "genel": "{analiz_tipi} - {grup_adi} - {vaka_tipi}",
}

# Grup adı çeviri tablosu (İngilizce kodlardan Türkçe'ye)
GRUP_ADI_CEVIRI = {
    "Il_Ici": "İl İçi",
    "Il_Disi": "İl Dışı",
    "Butun_Bolgeler": "Bütün Bölgeler",
    "Butun_Vakalar": "Bütün Vakalar",
    "Yeni_Vaka": "Son 24 saatlik vaka",
    "Devreden_Vaka": "Devreden Vaka",
    "Sevk_Vakalar": "Sevk Vakaları",
    "Yerel_Vakalar": "Yerel Vakalar",
}

# Vaka tipi isimleri
VAKA_TIPI_ISIMLERI = {
    "yeni_vaka_adi": "Son 24 saatlik vaka",
    "devreden_vaka_adi": "Devreden Vaka",
}

# Vaka tipi sabitler (kod içinde kullanım için)
YENI_VAKA_KODU = "Yeni Vaka"  # Kod içinde kullanılan sabit değer
DEVREDEN_VAKA_KODU = "Devreden Vaka"  # Kod içinde kullanılan sabit değer

# Gelişmiş pasta grafik renk paleti (komşu dilimler farklı renkte olacak)
PASTA_GRAFIK_RENK_PALETI = [
    "#1f77b4",  # Mavi
    "#ff7f0e",  # Turuncu
    "#2ca02c",  # Yeşil
    "#d62728",  # Kırmızı
    "#9467bd",  # Mor
    "#8c564b",  # Kahverengi
    "#e377c2",  # Pembe
    "#7f7f7f",  # Gri
    "#bcbd22",  # Olive
    "#17becf",  # Açık mavi
    "#aec7e8",  # Açık mavi 2
    "#ffbb78",  # Açık turuncu
    "#98df8a",  # Açık yeşil
    "#ff9896",  # Açık kırmızı
    "#c5b0d5",  # Açık mor
    "#c49c94",  # Açık kahverengi
    "#f7b6d3",  # Açık pembe
    "#c7c7c7",  # Açık gri
    "#dbdb8d",  # Açık olive
    "#9edae5",  # Açık cyan
]

# PDF konfigürasyonu ayrı dosyada tutulmaktadır
PDF_CONFIG_DOSYA_YOLU = PROJE_KOK / "pdf_config.json"
