"""Grafik oluşturma için sabit değerler ve yardımcı fonksiyonlar."""

from typing import List, Tuple

# Erişilebilir ve kullanıcı dostu renk paleti
GRAFIK_RENK_PALETI = [
    '#2E86C1',  # Koyu Mavi
    '#F39C12',  # Turuncu
    '#27AE60',  # Yeşil
    '#E74C3C',  # Kırmızı
    '#8E44AD',  # Mor
    '#16A085',  # Turkuaz
    '#D35400',  # Koyu Turuncu
    '#2C3E50',  # Lacivert
]

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
    'axes.facecolor': 'white',
    'axes.edgecolor': '#333333',
    'axes.labelcolor': '#333333',
    'text.color': '#333333',
    'xtick.color': '#333333',
    'ytick.color': '#333333',
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