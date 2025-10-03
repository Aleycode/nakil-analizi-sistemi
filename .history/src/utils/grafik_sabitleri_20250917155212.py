"""Grafik oluşturma için sabit değerler ve yardımcı fonksiyonlar."""

from typing import List, Tuple

# Erişilebilir ve kullanıcı dostu renk paleti (Color-blind friendly)
GRAFIK_RENK_PALETI = [
    '#3498DB',  # Açık Mavi - Ana kategori
    '#E67E22',  # Turuncu - İkincil kategori
    '#2ECC71',  # Yeşil - Olumlu durumlar
    '#E74C3C',  # Kırmızı - Dikkat çekilmesi gereken durumlar
    '#9B59B6',  # Mor - Özel durumlar
    '#1ABC9C',  # Turkuaz - Nötr durumlar
    '#F1C40F',  # Sarı - Uyarı durumları
    '#34495E',  # Lacivert - Diğer
]

# Pasta grafik opacity değerleri
PASTA_GRAFIK_OPACITY = {
    'ana_dilim': 0.9,
    'vurgulanan_dilim': 1.0,
    'soluk_dilim': 0.7
}

# Grafik boyutları
VARSAYILAN_GRAFIK_BOYUTU = (10, 8)
BUYUK_GRAFIK_BOYUTU = (12, 10)
KUCUK_GRAFIK_BOYUTU = (8, 6)

# Font ayarları
BASLIK_FONT_BOYUTU = 14
ETIKET_FONT_BOYUTU = 10
LEJANT_FONT_BOYUTU = 9

# Grafik stil ayarları
GRAFIK_STIL = {
    'figure.facecolor': 'white',
    'axes.facecolor': '#F8F9FA',  # Hafif gri arkaplan
    'axes.edgecolor': '#343A40',  # Koyu gri kenarlıklar
    'axes.labelcolor': '#212529',  # Koyu metin rengi
    'axes.grid': True,  # Izgara çizgileri
    'grid.alpha': 0.2,  # Izgara saydamlığı
    'text.color': '#212529',
    'xtick.color': '#495057',
    'ytick.color': '#495057',
    'figure.titlesize': 16,
    'axes.titlesize': 14,
    'axes.labelsize': 12,
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 10,
    'legend.framealpha': 0.8,
    'legend.edgecolor': '#DEE2E6'
}

def format_etiket(deger: float, toplam: float) -> str:
    """Pasta grafik dilimlerindeki etiketleri formatlar.
    
    Args:
        deger: Dilimin değeri
        toplam: Toplam değer
    
    Returns:
        str: Formatlanmış etiket (örn: "150 (%25.5)")
    """
    yuzde = (deger / toplam) * 100
    return f'{int(deger)}\n(%{yuzde:.1f})'

def renk_paleti_uret(n: int) -> List[str]:
    """İstenilen sayıda renk üretir.
    
    Args:
        n: İhtiyaç duyulan renk sayısı
    
    Returns:
        List[str]: Renk kodları listesi
    """
    return GRAFIK_RENK_PALETI[:n] + GRAFIK_RENK_PALETI[:(n - len(GRAFIK_RENK_PALETI))]